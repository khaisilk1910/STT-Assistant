"""Privacy-preserving request telemetry for STT Assistant.

The conversation text, device ID and conversation ID are intentionally excluded
from normal and DEBUG logs. Trace IDs are random per request, not user IDs.
"""

from __future__ import annotations

import logging
import time
from collections import Counter, deque
from contextlib import contextmanager
from contextvars import ContextVar
from dataclasses import dataclass, field
from secrets import token_hex
from typing import Iterator

_LOGGER = logging.getLogger(__name__)
SLOW_REQUEST_MS = 2000.0
HISTORY_SIZE = 100


@dataclass(slots=True)
class RequestTrace:
    """Per-request timings and decision metadata (never transcript data)."""

    language: str
    trace_id: str = field(default_factory=lambda: token_hex(4))
    started: float = field(default_factory=time.monotonic)
    route: str = "unknown"
    error: str | None = None
    phases_ms: dict[str, float] = field(default_factory=dict)
    detail: dict[str, str | int | float | bool] = field(default_factory=dict)

    def set_route(self, route: str) -> None:
        """Record a stable routing decision."""
        self.route = route

    def add_detail(self, key: str, value: str | int | float | bool) -> None:
        """Record metadata without transcribed text or stable user identifiers."""
        self.detail[key] = value

    @contextmanager
    def phase(self, name: str) -> Iterator[None]:
        """Measure an operation and record its duration, even if it fails."""
        start = time.monotonic()
        try:
            yield
        finally:
            duration = round((time.monotonic() - start) * 1000, 1)
            self.phases_ms[name] = self.phases_ms.get(name, 0.0) + duration
            if _LOGGER.isEnabledFor(logging.DEBUG):
                _LOGGER.debug("request=%s phase=%s elapsed_ms=%.1f", self.trace_id, name, duration)

    def duration_ms(self) -> float:
        """Return total elapsed time in milliseconds."""
        return round((time.monotonic() - self.started) * 1000, 1)


ACTIVE_TRACE: ContextVar[RequestTrace | None] = ContextVar("stt_assistant_trace", default=None)


def active_trace() -> RequestTrace | None:
    """Return the current coroutine's trace, when available."""
    return ACTIVE_TRACE.get()


@contextmanager
def phase(name: str) -> Iterator[None]:
    """Time a synchronous block, including awaits inside its containing coroutine."""
    trace = active_trace()
    if trace is None:
        yield
    else:
        with trace.phase(name):
            yield


def route(value: str, **details: str | int | float | bool) -> None:
    """Record the current non-sensitive routing decision."""
    if (trace := active_trace()) is not None:
        trace.set_route(value)
        for key, detail in details.items():
            trace.add_detail(key, detail)


@dataclass(slots=True)
class RequestMetrics:
    """Bounded, memory-only aggregate request statistics for Diagnostics."""

    requests: int = 0
    failures: int = 0
    slow_requests: int = 0
    routes: Counter[str] = field(default_factory=Counter)
    recent_latencies_ms: deque[float] = field(default_factory=lambda: deque(maxlen=HISTORY_SIZE))

    def record(self, trace: RequestTrace) -> None:
        """Update counters; called from the event loop after a request finishes."""
        elapsed = trace.duration_ms()
        self.requests += 1
        self.routes[trace.route] += 1
        self.recent_latencies_ms.append(elapsed)
        if trace.error:
            self.failures += 1
        if elapsed >= SLOW_REQUEST_MS:
            self.slow_requests += 1

    def as_dict(self) -> dict[str, object]:
        """Return a safe snapshot with bounded latency percentiles."""
        latencies = sorted(self.recent_latencies_ms)

        def percentile(percent: float) -> float | None:
            if not latencies:
                return None
            return latencies[max(0, min(len(latencies) - 1, int(len(latencies) * percent + 0.999999) - 1))]

        return {
            "requests": self.requests,
            "failures": self.failures,
            "slow_requests": self.slow_requests,
            "routes": dict(self.routes),
            "recent_sample_size": len(latencies),
            "recent_p50_ms": percentile(0.5),
            "recent_p95_ms": percentile(0.95),
        }


def log_request_finished(trace: RequestTrace, metrics: RequestMetrics) -> None:
    """Emit one compact INFO summary and DEBUG phase detail."""
    metrics.record(trace)
    elapsed = trace.duration_ms()
    level = logging.WARNING if trace.error or elapsed >= SLOW_REQUEST_MS else logging.INFO
    _LOGGER.log(
        level,
        "request=%s language=%s route=%s status=%s elapsed_ms=%.1f",
        trace.trace_id,
        trace.language,
        trace.route,
        trace.error or "ok",
        elapsed,
    )
    if _LOGGER.isEnabledFor(logging.DEBUG):
        _LOGGER.debug(
            "request=%s phases_ms=%s details=%s",
            trace.trace_id,
            trace.phases_ms,
            trace.detail,
        )
