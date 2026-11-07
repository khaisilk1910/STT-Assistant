"""Tests for Home Assistant's shareable config-entry diagnostics."""

import json
from unittest.mock import MagicMock

import pytest
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.stt_assistant.candidate import Candidate
from custom_components.stt_assistant.const import DATA_RUNTIME, DOMAIN
from custom_components.stt_assistant.diagnostics import (
    STTAssistantDiagnostics,
    async_get_config_entry_diagnostics,
)
from custom_components.stt_assistant.indexer import build_index
from custom_components.stt_assistant.runtime import STTAssistantRuntime


@pytest.mark.asyncio
async def test_download_diagnostics_redacts_private_data() -> None:
    """Only counters and safe routing metadata may appear in downloaded diagnostics."""
    secret = "do not export this utterance or hotword"
    entry = MockConfigEntry(
        domain=DOMAIN,
        entry_id="secret_entry_identifier",
        data={"fallback_agent_id": "conversation.private_agent"},
        options={
            "enable_hotword": True,
            "hotword": [secret],
            "min_confidence": 0.75,
            "min_margin": 0.1,
        },
    )
    runtime = STTAssistantRuntime()
    runtime.set_index(
        build_index(
            "en",
            tuple(
                Candidate(text=f"turn on lamp {i}", intent_name="HassTurnOn")
                for i in range(3)
            ),
        )
    )
    runtime.diagnostics = STTAssistantDiagnostics(
        last_request_id="private_request_id",
        last_trace_id="private_trace_id",
        selected_delegated_text_hash="private_hash",
        candidate_count=3,
        last_query_latency_ms=12.5,
        last_error=f"RuntimeError: {secret}",
    )
    hass = MagicMock()
    hass.data = {DOMAIN: {entry.entry_id: {DATA_RUNTIME: runtime}}}

    result = await async_get_config_entry_diagnostics(hass, entry)

    assert result["status"] == "loaded"
    settings = result["settings"]
    assert isinstance(settings, dict)
    assert settings["min_confidence"] == 0.75
    assert settings["hotword_count"] == 1
    last_query = result["last_query"]
    assert isinstance(last_query, dict)
    assert last_query["error_present"] is True
    assert result["total_cached_candidate_count"] == 3
    cached_indexes = result["cached_indexes"]
    assert isinstance(cached_indexes, dict)
    english_index = cached_indexes["en"]
    assert isinstance(english_index, dict)
    assert english_index["candidate_count"] == 3
    serialized = json.dumps(result, ensure_ascii=False)
    for private in (
        secret,
        "conversation.private_agent",
        "secret_entry_identifier",
        "private_request_id",
        "private_trace_id",
        "private_hash",
    ):
        assert private not in serialized


@pytest.mark.asyncio
async def test_download_diagnostics_without_loaded_entry() -> None:
    """Downloading diagnostics for an unloaded entry must not start the runtime."""
    hass = MagicMock()
    hass.data = {}
    entry = MockConfigEntry(domain=DOMAIN, entry_id="missing", data={})

    assert await async_get_config_entry_diagnostics(hass, entry) == {"status": "not_loaded"}
