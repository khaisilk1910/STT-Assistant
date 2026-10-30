<div align="center">

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="custom_components/stt_assistant/brand/dark_logo.png">
  <img src="custom_components/stt_assistant/brand/logo.png" alt="STT Assistant" width="480">
</picture>

### Improve voice commands before Home Assistant processes them

**🇻🇳 [Tiếng Việt](README.md) · 🇬🇧 [English](README.en.md)**

[![Home Assistant](https://img.shields.io/badge/Home%20Assistant-%E2%89%A5%202026.10-blue)](https://www.home-assistant.io/)
[![GitHub](https://img.shields.io/badge/GitHub-STT--Assistant-181717?logo=github)](https://github.com/khaisilk1910/STT-Assistant)
[![License](https://img.shields.io/github/license/khaisilk1910/STT-Assistant)](LICENSE)

[![Add to HACS](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=khaisilk1910&repository=STT-Assistant&category=integration)

**[Releases](https://github.com/khaisilk1910/STT-Assistant/releases) · [Report an issue](https://github.com/khaisilk1910/STT-Assistant/issues)**

</div>

> [!NOTE]
> This is a **community integration**, not an official Home Assistant component, and has not yet passed full real-world Home Assistant testing. The GitHub repository must contain the integration source before HACS can download it. The button above opens the repository in HACS; it **does not automatically install** the integration.

## What is STT Assistant?

**STT Assistant** is a **Conversation Agent** for Home Assistant Assist. After speech has been transcribed to text by your STT engine, it normalizes and matches commands with transcription errors, word-order changes and device aliases, then delegates intent handling to Home Assistant.

It is **not** an audio STT engine, wake-word detector or TTS engine. Those stages remain the responsibility of the Assist Pipeline.

## ✨ Features

- **Post-STT command correction:** fuzzy matching, BM25, character similarity and intent-aware ranking.
- **Multiple languages** with exposed entities, aliases, areas, floors and custom sentences.
- **Safer intent execution:** confidence thresholds and intent preflight; fallback instead of forcing uncertain commands.
- **Fallback agent & custom hotwords:** route open-ended requests to a configured Conversation Agent.
- **Light startup:** delayed background index warmup; the first request may take longer.
- **Logging & diagnostics:** per-request trace IDs, decision routes, stage timings, P50/P95 and developer actions.
- **Local processing:** no telemetry/cloud calls are initiated by the canonicalizer itself; a configured fallback agent might use cloud services.

## 📥 Installation

### Option 1 — HACS (recommended)

[![Add STT Assistant to HACS](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=khaisilk1910&repository=STT-Assistant&category=integration)

1. Install [HACS](https://www.hacs.xyz/) if needed.
2. Click the button above, or open **HACS → ⋮ → Custom repositories** and enter:
   - **Repository:** `https://github.com/khaisilk1910/STT-Assistant`
   - **Type / Category:** `Integration`
3. Open STT Assistant in HACS and select **Download**.
4. **Restart Home Assistant.**

> [!IMPORTANT]
> HACS can only download this custom integration once valid source files have been pushed to the repository. A **custom repository** is not the same as an approved HACS default repository.

### Option 2 — Manual installation

1. Obtain the project ZIP from [Releases](https://github.com/khaisilk1910/STT-Assistant/releases) or your project package.
2. Copy the **whole** `custom_components/stt_assistant` folder into your Home Assistant configuration directory:

   ```text
   config/
   └── custom_components/
       └── stt_assistant/
           ├── __init__.py
           ├── manifest.json
           └── brand/
   ```

3. **Restart Home Assistant.** You do not need to copy the tests or documentation into `custom_components`.

### Enable it in Assist

1. Open **Settings → Devices & services → Add integration** and search for **STT Assistant**.
2. Choose a **Fallback Conversation Agent** and keep the default confidence thresholds initially.
3. Open **Settings → Voice assistants**, edit the Assist Pipeline you use, and choose **STT Assistant** as its *Conversation Agent*.
4. Try a normal device command, then a mis-transcribed command; inspect logs/diagnostics if needed.

**Important:** Simply installing the integration does **not** make it process commands until you choose it in your Assist Pipeline.

## 🪵 Logging and troubleshooting

Use **Enable debug logging** on the integration page under **Devices & services**, or add to `configuration.yaml`:

```yaml
logger:
  default: warning
  logs:
    custom_components.stt_assistant: info  # switch to debug when troubleshooting
```

If `logger:` already exists, **merge** this entry into the existing section instead of defining it twice. INFO logs include routing decisions and total time; DEBUG logs include per-stage timing. See the [logging guide](LOGGING_STT_ASSISTANT.md) and [validation notes](RELEASE_VALIDATION.md).

## ⚠️ Risks and recommendations

- **Wrong intent execution:** text similarity cannot guarantee the intended action. Carefully test **on/off and lock/unlock** requests, especially with similar device names. Start with default thresholds; do not lower them blindly.
- **Performance:** initial indexing may use CPU/RAM and slow the first request; performance depends on your hardware and entity count.
- **Compatibility:** source version 1.17.0 declares **Home Assistant ≥ 2026.10.0**, but end-to-end operation has not been certified on a real instance. Back up before installing and use a test instance if possible.
- **Migration:** the new domain `stt_assistant` does **not** automatically migrate `assist_canonicalizer` config entries. Follow the [migration guide](MIGRATION_STT_ASSISTANT.md); **do not edit** `.storage` directly.
- **Privacy:** the new INFO/DEBUG logging does not deliberately include transcripts; Home Assistant or other agents can still write sensitive data. Review logs before sharing and consider cloud fallback privacy.
- **Not an STT replacement:** an upstream engine that completely misrecognizes an utterance may not be recoverable.

## 📚 Documentation and support

[Logging](LOGGING_STT_ASSISTANT.md) · [Domain migration](MIGRATION_STT_ASSISTANT.md) · [Validation limits](RELEASE_VALIDATION.md) · [Brand assets](BRANDING.md) · [GitHub Issues](https://github.com/khaisilk1910/STT-Assistant/issues)

**Project:** [github.com/khaisilk1910/STT-Assistant](https://github.com/khaisilk1910/STT-Assistant) · **License:** [LICENSE](LICENSE)
