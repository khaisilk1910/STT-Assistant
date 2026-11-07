"""Runtime diagnostics models for STT Assistant."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import TYPE_CHECKING

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.util.json import JsonObjectType, JsonValueType

from .const import DATA_RUNTIME, DOMAIN, ConfigKey, FallbackReason
from .utils import resolve_entry_thresholds

if TYPE_CHECKING:
    from .runtime import STTAssistantRuntime


@dataclass(frozen=True, slots=True)
class STTAssistantDiagnostics:
    """Serializable runtime diagnostics snapshot."""

    candidate_count: int = 0
    index_version: int | None = None
    last_query_latency_ms: float | None = None
    last_fallback_reason: FallbackReason | str | None = None
    last_error: str | None = None
    dynamic_candidate_count: int = 0
    last_request_id: str | None = None
    last_trace_id: str | None = None
    selected_delegated_text_hash: str | None = None
    selected_candidate_source: str | None = None
    confidence_gate: Mapping[str, JsonValueType] | None = None
    execution_result: str | None = None
    recognition_kind: str | None = None
    recognition_intent: str | None = None
    recognition_unmatched_count: int = 0
    recognition_latency_ms: float | None = None
    preflight_attempt_count: int = 0
    metadata_diverged: bool = False
    metadata_intent_matches_observed: bool | None = None
    metadata_slots_match_observed: bool | None = None
    metadata_divergence_reason: str | None = None
    recovery_used: bool = False
    registry_record_count: int = 0
    registry_generation: int = 0
    registry_fingerprint: str | None = None
    registry_postings_consulted: int = 0
    registry_values_nominated: int = 0
    registry_values_scored: int = 0
    fuzzy_dynamic_candidates: int = 0
    registry_retrieval_latency_ms: float | None = None
    selected_from_fuzzy_registry: bool = False

    def as_dict(self) -> JsonObjectType:
        """Return diagnostics as a dictionary."""
        return {
            "candidate_count": self.candidate_count,
            "index_version": self.index_version,
            "last_query_latency_ms": self.last_query_latency_ms,
            "last_fallback_reason": (
                self.last_fallback_reason.value
                if isinstance(self.last_fallback_reason, FallbackReason)
                else self.last_fallback_reason
            ),
            "last_error": self.last_error,
            "dynamic_candidate_count": self.dynamic_candidate_count,
            "last_request_id": self.last_request_id,
            "last_trace_id": self.last_trace_id,
            "selected_delegated_text_hash": self.selected_delegated_text_hash,
            "selected_candidate_source": self.selected_candidate_source,
            "confidence_gate": dict(self.confidence_gate) if self.confidence_gate else None,
            "execution_result": self.execution_result,
            "recognition_kind": self.recognition_kind,
            "recognition_intent": self.recognition_intent,
            "recognition_unmatched_count": self.recognition_unmatched_count,
            "recognition_latency_ms": self.recognition_latency_ms,
            "preflight_attempt_count": self.preflight_attempt_count,
            "metadata_diverged": self.metadata_diverged,
            "metadata_intent_matches_observed": self.metadata_intent_matches_observed,
            "metadata_slots_match_observed": self.metadata_slots_match_observed,
            "metadata_divergence_reason": self.metadata_divergence_reason,
            "recovery_used": self.recovery_used,
            "registry_retrieval": {
                "record_count": self.registry_record_count,
                "generation": self.registry_generation,
                "fingerprint": self.registry_fingerprint,
                "postings_consulted": self.registry_postings_consulted,
                "values_nominated": self.registry_values_nominated,
                "values_scored": self.registry_values_scored,
                "fuzzy_dynamic_candidates": self.fuzzy_dynamic_candidates,
                "latency_ms": self.registry_retrieval_latency_ms,
                "selected_from_fuzzy_registry": self.selected_from_fuzzy_registry,
            },
        }


async def async_get_config_entry_diagnostics(
    hass: HomeAssistant, entry: ConfigEntry
) -> JsonObjectType:
    """Return a privacy-safe snapshot for Home Assistant's Download diagnostics.

    Do not include utterances, hotword strings, entity/area names, fallback
    agent IDs, request IDs, or raw candidate metadata in a shareable report.
    All values are read from memory: collecting diagnostics never builds an
    index or accesses a storage file.
    """
    from .runtime import STTAssistantRuntime

    domain_data = hass.data.get(DOMAIN, {})
    entry_data = domain_data.get(entry.entry_id, {})
    runtime = entry_data.get(DATA_RUNTIME)
    if not isinstance(runtime, STTAssistantRuntime) or runtime.closed:
        return {"status": "not_loaded"}

    settings = {**entry.data, **entry.options}
    min_confidence, min_margin = resolve_entry_thresholds(entry)
    diagnostics = runtime.diagnostics
    indexes: JsonObjectType = {
        language: {"candidate_count": index.candidate_count, "version": index.version}
        for language, index in sorted(runtime.indexes.items())
    }
    # Export only an explicit allow-list. The service diagnostics payload is
    # intentionally more detailed and contains request/trace identifiers.
    return {
        "status": "loaded",
        "settings": {
            "fallback_agent_configured": bool(settings.get(ConfigKey.FALLBACK_AGENT_ID)),
            "min_confidence": min_confidence,
            "min_margin": min_margin,
            "hotword_enabled": bool(settings.get(ConfigKey.ENABLE_HOTWORD, False)),
            "hotword_count": _safe_hotword_count(settings.get(ConfigKey.HOTWORD, ())),
        },
        "cached_indexes": indexes,
        "total_cached_candidate_count": runtime.total_candidate_count(),
        "pending_rebuild_languages": sorted(runtime.rebuild_tasks),
        "last_query": {
            "latency_ms": diagnostics.last_query_latency_ms,
            "fallback_reason": (
                diagnostics.last_fallback_reason.value
                if isinstance(diagnostics.last_fallback_reason, FallbackReason)
                else diagnostics.last_fallback_reason
            ),
            # The legacy last_error value can contain an exception message,
            # so never include it verbatim in downloaded diagnostics.
            "error_present": diagnostics.last_error is not None,
            "dynamic_candidate_count": diagnostics.dynamic_candidate_count,
            "recognition_latency_ms": diagnostics.recognition_latency_ms,
        },
        "registry": {
            "record_count": diagnostics.registry_record_count,
            "generation": diagnostics.registry_generation,
            "postings_consulted": diagnostics.registry_postings_consulted,
            "values_scored": diagnostics.registry_values_scored,
        },
        "request_metrics": _safe_request_metrics(runtime),
    }


def _safe_hotword_count(raw_hotwords: object) -> int:
    """Count configured hotwords without logging or exporting their values."""
    if isinstance(raw_hotwords, str):
        return int(bool(raw_hotwords.strip()))
    if isinstance(raw_hotwords, (list, tuple, set)):
        return sum(isinstance(value, str) and bool(value.strip()) for value in raw_hotwords)
    return 0


def _safe_request_metrics(runtime: STTAssistantRuntime) -> JsonObjectType:
    """Return aggregate counts and latency only, without per-route names."""
    metrics = runtime.request_metrics
    snapshot = metrics.as_dict()
    p50 = snapshot["recent_p50_ms"]
    p95 = snapshot["recent_p95_ms"]
    return {
        "requests": metrics.requests,
        "failures": metrics.failures,
        "slow_requests": metrics.slow_requests,
        "recent_sample_size": len(metrics.recent_latencies_ms),
        "recent_p50_ms": float(p50) if isinstance(p50, (int, float)) else None,
        "recent_p95_ms": float(p95) if isinstance(p95, (int, float)) else None,
    }
