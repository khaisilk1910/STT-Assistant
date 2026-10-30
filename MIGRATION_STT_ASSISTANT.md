# STT Assistant migration and release notes

The integration domain is now `stt_assistant` (formerly `assist_canonicalizer`).

## Existing installations

1. Back up Home Assistant before replacing the integration.
2. Record the old integration options and any automations or service calls.
3. Remove the old integration from Settings > Devices & services, then remove its old custom component directory.
4. Copy `custom_components/stt_assistant` into your Home Assistant configuration and restart.
5. Add STT Assistant using Settings > Devices & services > Add integration and restore your options.
6. Select STT Assistant as the conversation agent in your Assist pipeline if required.
7. Update service calls from `assist_canonicalizer.*` to `stt_assistant.*`.

Do not directly edit `.storage/core.config_entries`; Home Assistant stores config entry domain identifiers there. An automatic config-entry migration across domains is not provided in this release.

## Startup performance

Index prewarming is scheduled 15 seconds after `EVENT_HOMEASSISTANT_STARTED` for normal boot and 15 seconds after an integration reload. Languages are prepared sequentially to limit CPU and memory spikes. The first STT request before prewarming finishes may still incur index-building latency.

## Compatibility caveat

The manifest minimum version and API usage have not been certified against every latest Home Assistant release. Validate with the target Home Assistant version before production deployment.
