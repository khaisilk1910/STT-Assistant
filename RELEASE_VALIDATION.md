# STT Assistant 1.17.0 — Conversation / Voice / Logging audit (2026-10-30)

The update was checked against official Home Assistant 2026.10.0 source for the ConversationEntity, conversation agent manager and Assist pipeline. STT Assistant is a **post-STT Conversation Agent**, not a streaming STT, wake-word, microphone or TTS provider.

## Improvements

- Register services in `async_setup`, as recommended in [Home Assistant service development documentation](https://developers.home-assistant.io/docs/dev_101_services/), so actions remain registered when a config entry has not loaded.
- Add correlation-safe request traces using a random per-request ID and `contextvars`; log `language`, `route`, `status`, timing and DEBUG-only per-stage timings without deliberately logging user speech, conversation IDs or device IDs.
- Add lifecycle and warmup logs. Time slow requests at >= 2000 ms and emit WARN on failures. Hide raw exception messages from normal logs and voice users (DEBUG may include stack traces).
- Add memory-bounded request metrics and P50/P95 over 100 requests to `stt_assistant.diagnostics`, plus `last_trace_id`. Keep existing latest-snapshot diagnostics for backward compatibility.
- Harden fallback agent ID against self-entity recursion. Add logging guides and tests.

## Tests completed in the build environment

- Python 3.13.5 `compileall`: **passed** for integration, tests and tools (syntax only; HA 2026.10 requires Python 3.14.2+).
- Dependency-free `pytest -q -o addopts='' tests/test_project_metadata.py tests/test_validate.py tests/test_validate_compatibility.py tests/test_observability_standalone.py`: **156 passed**.
- JSON/manifest/HACS/TOML consistency checks: **passed**.

## Not yet verified

- Home Assistant is not installed in this build environment; Home Assistant-dependent tests fail at collection with `ModuleNotFoundError: homeassistant`. There has been no live HA 2026.10, real microphone, STT/TTS, startup, memory or Vietnamese intent-accuracy benchmark. Full integration compatibility and optimality cannot be guaranteed.
- The local-intent shortcut still probes a private Home Assistant pipeline implementation attribute (`_pipeline_runs`). Its guarded behavior must be tested after Home Assistant updates.
- `last_*` diagnostics fields are shared latest-value snapshots; use the per-request trace ID in logs to troubleshoot concurrency.
- The repository URL in the manifest is illustrative and ownership/existence has not been confirmed.

See `LOGGING_STT_ASSISTANT.vi.md` for complete Vietnamese log setup and route explanations. Validate the complete Assist pipeline on a disposable Home Assistant 2026.10.0+ instance before production deployment. Back up and migrate old-domain configurations before installing.
