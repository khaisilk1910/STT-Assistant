"""Home Assistant entry points for STT Assistant."""

from __future__ import annotations

import asyncio
import logging
import time
from collections.abc import Callable, Mapping, Sequence
from datetime import datetime
from functools import partial

from homeassistant.components.conversation import agent_manager
from homeassistant.components.homeassistant import exposed_entities
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import EVENT_HOMEASSISTANT_STARTED, HomeAssistant, callback
from homeassistant.helpers import area_registry, device_registry, entity_registry, floor_registry
from homeassistant.helpers import event as ha_event
from homeassistant.helpers.typing import ConfigType

from .const import (
    ASSISTANT_CONVERSATION,
    DATA_RUNTIME,
    DOMAIN,
)
from .preparation import async_prepare_language_caches
from .registry import async_registry_slot_values
from .runtime import STTAssistantRuntime
from .services import async_setup_services
from .utils import normalize_language

type PipelineGetter = Callable[[HomeAssistant], Sequence[object]]


class _UninitializedPipelineGetter:
    """Sentinel for a pipeline helper that has not been imported yet."""


_UNINITIALIZED = _UninitializedPipelineGetter()
async_get_pipelines: PipelineGetter | _UninitializedPipelineGetter | None = _UNINITIALIZED

PLATFORMS = [Platform.CONVERSATION]

_LOGGER = logging.getLogger(__name__)


async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """Register actions early, even when no config entry has loaded yet.

    Home Assistant's integration service contract requires registration in
    async_setup, not in entry/platform setup. This does not construct an index.
    """
    async_setup_services(hass)
    _LOGGER.info("STT Assistant services registered; no language index loaded during setup")
    return True


def _runtime_from_entry(hass: HomeAssistant, entry: ConfigEntry) -> STTAssistantRuntime:
    """Return runtime state for an entry."""
    return hass.data[DOMAIN][entry.entry_id][DATA_RUNTIME]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up STT Assistant and roll back owned resources if setup fails.

    No index is built in this method. All expensive warmup work is delayed
    until after Home Assistant has finished starting.
    """
    runtime = STTAssistantRuntime()
    runtime.configure_config_path(hass.config.path)
    domain_data = hass.data.setdefault(DOMAIN, {})
    domain_data[entry.entry_id] = {
        "entry": entry,
        DATA_RUNTIME: runtime,
    }
    platform_setup_attempted = False
    try:
        _subscribe_intent_updates(hass, runtime)
        _refresh_registry_slot_values(hass, runtime)
        _subscribe_registry_updates(hass, runtime)

        platform_setup_attempted = True
        await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

        # Register the listener only after the setup succeeds. Home Assistant
        # owns its disposal through config entry async_on_unload callbacks.
        entry.async_on_unload(entry.add_update_listener(_async_update_listener))

        @callback
        def schedule_warmup(_event: object | None = None) -> None:
            if not runtime.closed:
                runtime.track_warmup_task(
                    hass.async_create_task(_async_warmup_pipeline_languages(hass, runtime))
                )

        @callback
        def schedule_after_start(_event: object | None = None) -> None:
            if runtime.closed:
                return
            runtime.add_cleanup_callback(ha_event.async_call_later(hass, 15, schedule_warmup))

        if hass.is_running:
            schedule_after_start()
        else:
            runtime.add_cleanup_callback(
                hass.bus.async_listen_once(EVENT_HOMEASSISTANT_STARTED, schedule_after_start)
            )
        _LOGGER.info(
            "STT Assistant entry initialized; conversation agent ready, warmup scheduled "
            "15s after Home Assistant startup"
        )
        return True
    except BaseException:
        # Subscription callbacks, timers and background operations must not
        # survive a failed setup. Preserve the original setup exception.
        try:
            await runtime.async_shutdown()
        except Exception:
            _LOGGER.exception("Failed to clean up STT Assistant after setup failure")
        if platform_setup_attempted:
            try:
                await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
            except Exception:
                _LOGGER.exception("Failed to unload STT Assistant platform after setup failure")
        domain_data.pop(entry.entry_id, None)
        if not domain_data:
            hass.data.pop(DOMAIN, None)
        raise


async def _async_update_listener(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Invalidate runtime ranking cache synchronously when entry options change."""
    runtime = _runtime_from_entry(hass, entry)
    runtime.clear_ranking_cache()
    _LOGGER.info("STT Assistant options updated; ranking cache invalidated")


def _subscribe_intent_updates(
    hass: HomeAssistant,
    runtime: STTAssistantRuntime,
) -> None:
    """Subscribe when the installed Home Assistant exposes dynamic intent updates."""
    subscribe_intents = getattr(
        agent_manager.get_agent_manager(hass),
        "subscribe_intents",
        None,
    )
    if subscribe_intents is None:
        return
    unsubscribe = subscribe_intents(partial(_handle_intent_updates, hass, runtime))
    if not callable(unsubscribe):
        raise TypeError("subscribe_intents returned a non-callable unsubscribe callback")

    def cleanup() -> None:
        unsubscribe()

    runtime.add_cleanup_callback(cleanup)


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload the platform and release all STT Assistant resources."""
    _LOGGER.info("Unloading STT Assistant conversation agent")
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if not unload_ok:
        return False
    try:
        await _runtime_from_entry(hass, entry).async_shutdown()
    finally:
        # Never leak service registrations or stale entry state if shutdown
        # itself encounters an unexpected error.
        # Actions stay registered for the integration's lifetime, as required
        # by Home Assistant's service architecture.
        domain_data = hass.data.get(DOMAIN, {})
        domain_data.pop(entry.entry_id, None)
        if not domain_data:
            hass.data.pop(DOMAIN, None)
    _LOGGER.info("STT Assistant unloaded; runtime tasks and caches released")
    return True


def _refresh_registry_slot_values(hass: HomeAssistant, runtime: STTAssistantRuntime) -> bool:
    """Refresh registry-derived slot values used for template expansion.

    Returns whether the cached values actually changed.
    """
    return runtime.update_registry_slot_values(async_registry_slot_values(hass))


def _subscribe_registry_updates(hass: HomeAssistant, runtime: STTAssistantRuntime) -> None:
    """Subscribe to Home Assistant registry metadata changes."""
    debounced_rebuild = partial(_debounced_registry_rebuild, hass, runtime)
    refresh_from_event = partial(
        _schedule_registry_refresh,
        hass,
        runtime,
        debounced_rebuild,
    )

    runtime.add_cleanup_callback(
        hass.bus.async_listen(entity_registry.EVENT_ENTITY_REGISTRY_UPDATED, refresh_from_event)
    )
    runtime.add_cleanup_callback(
        hass.bus.async_listen(area_registry.EVENT_AREA_REGISTRY_UPDATED, refresh_from_event)
    )
    runtime.add_cleanup_callback(
        hass.bus.async_listen(floor_registry.EVENT_FLOOR_REGISTRY_UPDATED, refresh_from_event)
    )
    runtime.add_cleanup_callback(
        hass.bus.async_listen(device_registry.EVENT_DEVICE_REGISTRY_UPDATED, refresh_from_event)
    )
    runtime.add_cleanup_callback(
        exposed_entities.async_listen_entity_updates(
            hass, ASSISTANT_CONVERSATION, refresh_from_event
        )
    )


def _handle_intent_updates(
    hass: HomeAssistant,
    runtime: STTAssistantRuntime,
    intents_update: Mapping[object, Mapping[str, object]],
) -> None:
    """Update intent sources and trigger background rebuilds for active languages."""
    if runtime.closed:
        return
    active_languages = list(runtime.indexes)
    if not runtime.update_intent_sources(intents_update):
        return
    for language in active_languages:
        hass.add_job(runtime.async_rebuild_index, hass, language)


@callback
def _debounced_registry_rebuild(
    hass: HomeAssistant,
    runtime: STTAssistantRuntime,
    now: datetime | None = None,
) -> None:
    """Refresh registry slot values and rebuild active indexes."""
    if runtime.closed:
        return
    runtime.rebuild_timer_cancel = None
    active_languages = list(runtime.indexes)
    if not _refresh_registry_slot_values(hass, runtime):
        return
    for language in active_languages:
        hass.add_job(runtime.async_rebuild_index, hass, language)


@callback
def _schedule_registry_refresh(
    hass: HomeAssistant,
    runtime: STTAssistantRuntime,
    debounced_rebuild: Callable[[datetime], None],
    event: object = None,
) -> None:
    """Schedule a debounced refresh after a registry update."""
    if runtime.closed:
        return
    runtime.clear_ranking_cache()
    if runtime.rebuild_timer_cancel is not None:
        runtime.rebuild_timer_cancel()
        runtime.rebuild_timer_cancel = None
    runtime.rebuild_timer_cancel = ha_event.async_call_later(
        hass,
        5,
        debounced_rebuild,
    )


def _discover_pipeline_languages(hass: HomeAssistant) -> set[str]:
    """Return unique language codes from all configured Assist pipelines."""
    global async_get_pipelines
    languages: set[str] = set()
    if isinstance(async_get_pipelines, _UninitializedPipelineGetter):
        try:
            from homeassistant.components.assist_pipeline import (
                async_get_pipelines as imported_get_pipelines,
            )
        except (ImportError, RuntimeError) as err:
            _LOGGER.debug("Assist pipeline import failed: %s", err)
            async_get_pipelines = None
        else:
            async_get_pipelines = imported_get_pipelines
    pipeline_getter = async_get_pipelines
    if pipeline_getter is None or isinstance(pipeline_getter, _UninitializedPipelineGetter):
        return languages

    try:
        pipelines = pipeline_getter(hass)
    except Exception:
        return languages

    for pipeline in pipelines:
        lang = getattr(pipeline, "language", None)
        if isinstance(lang, str) and lang.strip():
            languages.add(normalize_language(lang))

    return languages


async def _warmup_single_language(
    hass: HomeAssistant,
    runtime: STTAssistantRuntime,
    language: str,
) -> None:
    """Try to load an index from store, falling back to a rebuild. Never raises."""
    if runtime.closed:
        return
    started = time.monotonic()
    _LOGGER.debug("Index warmup started language=%s", language)
    try:
        index = runtime.get_index(language)
        cache_source = "memory"
        if index is None:
            index = await runtime.async_load_index_from_store(hass, language)
            cache_source = "store"
        if index is None:
            index = await runtime.async_rebuild_index(hass, language, log_error=False)
            cache_source = "rebuild"
        if index is None:
            _LOGGER.warning("Index warmup unavailable language=%s; requests use fallback agent", language)
            return
        await async_prepare_language_caches(hass, runtime, language)
        if runtime.closed:
            return
        _LOGGER.info(
            "Index warmup completed language=%s source=%s candidates=%d elapsed_ms=%.1f",
            language, cache_source, index.candidate_count,
            (time.monotonic() - started) * 1000,
        )
    except asyncio.CancelledError:
        _LOGGER.debug("Index warmup cancelled language=%s", language)
        raise
    except Exception:
        _LOGGER.warning(
            "Index warmup failed language=%s; will attempt on demand", language,
            exc_info=_LOGGER.isEnabledFor(logging.DEBUG),
        )


async def _async_warmup_pipeline_languages(
    hass: HomeAssistant,
    runtime: STTAssistantRuntime,
) -> None:
    """Discover configured pipeline languages and warm every index in the background."""
    if runtime.closed:
        return
    languages = _discover_pipeline_languages(hass)
    if not languages:
        try:
            languages = {normalize_language(str(hass.config.language))}
        except Exception:
            return

    if runtime.closed:
        return

    _LOGGER.info("Background index warmup started languages=%s", ",".join(sorted(languages)))
    # Build one language at a time to avoid CPU and memory spikes after startup.
    # Requests can still trigger their own on-demand preparation.
    for language in sorted(languages):
        if runtime.closed:
            return
        await _warmup_single_language(hass, runtime, language)
        await asyncio.sleep(0)
