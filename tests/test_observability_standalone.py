"""Dependency-free tests for lightweight STT Assistant telemetry."""

from __future__ import annotations

import asyncio
import importlib.util
import logging
import sys
from pathlib import Path

import pytest

TELEMETRY = Path(__file__).resolve().parents[1] / "custom_components/stt_assistant/observability.py"
spec = importlib.util.spec_from_file_location("stt_assistant_observability_standalone", TELEMETRY)
assert spec and spec.loader
module = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = module
spec.loader.exec_module(module)


def test_request_metrics_are_bounded_and_percentiles() -> None:
    """Only a rolling window of durations is retained."""
    metrics = module.RequestMetrics()
    for i in range(150):
        trace = module.RequestTrace(language="vi")
        trace.started -= (i + 1) / 1000
        trace.set_route("canonical_success")
        metrics.record(trace)
    snapshot = metrics.as_dict()
    assert snapshot["requests"] == 150
    assert snapshot["recent_sample_size"] == 100
    assert snapshot["routes"] == {"canonical_success": 150}
    assert snapshot["recent_p50_ms"] is not None
    assert snapshot["recent_p95_ms"] >= snapshot["recent_p50_ms"]


def test_log_is_privacy_preserving(caplog: pytest.LogCaptureFixture) -> None:
    """A summary contains only routing and timing metadata, not a transcript."""
    caplog.set_level(logging.DEBUG, logger=module.__name__)
    trace = module.RequestTrace(language="vi")
    trace.set_route("fallback_low_confidence")
    trace.add_detail("candidate_count", 3)
    with trace.phase("ranking"):
        _ = 1 + 1
    metrics = module.RequestMetrics()
    module.log_request_finished(trace, metrics)
    assert trace.trace_id in caplog.text
    assert "fallback_low_confidence" in caplog.text
    assert "candidate_count" in caplog.text
    assert "language=vi" in caplog.text
    assert metrics.as_dict()["requests"] == 1


@pytest.mark.asyncio
async def test_concurrent_request_contexts_are_isolated() -> None:
    """Two simultaneous voice requests cannot overwrite each other's trace."""
    async def task(language: str) -> tuple[str, str]:
        trace = module.RequestTrace(language=language)
        token = module.ACTIVE_TRACE.set(trace)
        try:
            with module.phase("index"):
                await asyncio.sleep(0)
            module.route("canonical_success" if language == "vi" else "fallback_no_index")
            return module.active_trace().language, module.active_trace().route
        finally:
            module.ACTIVE_TRACE.reset(token)

    outputs = await asyncio.gather(task("vi"), task("en"))
    assert outputs == [("vi", "canonical_success"), ("en", "fallback_no_index")]
    assert module.active_trace() is None


def test_phase_records_failure_without_losing_log_context() -> None:
    """Failed phases still measure elapsed time, and error types are counted."""
    trace = module.RequestTrace(language="en")
    with pytest.raises(ValueError), trace.phase("delegate"):
        raise ValueError("hidden user utterance")
    trace.error = "ValueError"
    metrics = module.RequestMetrics()
    metrics.record(trace)
    assert trace.phases_ms["delegate"] >= 0
    assert metrics.as_dict()["failures"] == 1
