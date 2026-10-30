# STT Assistant 1.17.0 logging and diagnostics

STT Assistant is a post-transcription Conversation Agent, **not an audio STT engine**. It processes the text from Assist, scores canonical alternatives, validates a local intent and delegates to a fallback agent when needed.

To trace requests, use Settings → Devices & services → STT Assistant → menu → **Enable debug logging**. Reproduce the problem, then **Disable debug logging** to download a log. Alternatively configure:

```yaml
logger:
  default: warning
  logs:
    custom_components.stt_assistant: info
```

Set the component logger to `debug` temporarily to see phase timings and traceback details. Inspect Settings → System → Logs → Show raw logs. The INFO level prints one summary per request, with `request=<random-id>`, `language`, `route`, `status` and `elapsed_ms`, without input text, device ID or conversation ID. The DEBUG level adds phase timings and non-transcript metadata. Some unrelated HA integrations can still log utterances.

Main routing values: `local_intent_shortcut`, `canonical_success`, `canonical_recovered`, `hotword_fallback`, `fallback_no_index`, `fallback_ranking_error`, `fallback_low_confidence`, `fallback_preflight_rejected`, `fallback_execution_failed`, `fallback_candidate_exception`, `unhandled_exception`.

The `stt_assistant.diagnostics` service includes `last_trace_id`, per-route counters, total requests/failures/slow requests, plus P50/P95 over at most 100 recent conversation requests. The slow-warning threshold is 2 seconds. In concurrent requests, only the per-request log correlation ID is reliable; existing `last_*` diagnostics remain a shared latest snapshot. Logs and metrics reset with reload/restart. Agent latency excludes audio capture, STT and TTS.

For details, see `LOGGING_STT_ASSISTANT.vi.md` (Vietnamese) and the official [Home Assistant debug logging documentation](https://www.home-assistant.io/docs/configuration/troubleshooting/).
