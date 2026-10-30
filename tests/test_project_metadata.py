"""Dependency-free regression checks for the distributable integration metadata."""

import json
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
INTEGRATION = ROOT / "custom_components" / "stt_assistant"


def test_metadata_minimum_versions_and_domain_match() -> None:
    """HACS and Python requirements must advertise the supported HA baseline."""
    manifest = json.loads((INTEGRATION / "manifest.json").read_text())
    hacs = json.loads((ROOT / "hacs.json").read_text())
    project = tomllib.loads((ROOT / "pyproject.toml").read_text())
    lock = tomllib.loads((ROOT / "uv.lock").read_text())
    assert manifest["domain"] == "stt_assistant"
    assert manifest["name"] == "STT Assistant"
    assert manifest["config_flow"] is True
    assert manifest["single_config_entry"] is True
    assert "assist_pipeline" not in manifest.get("after_dependencies", [])
    assert hacs["homeassistant"] == "2026.10.0"
    assert manifest["version"] == project["project"]["version"]
    assert project["project"]["name"] == "stt-assistant"
    assert project["project"]["requires-python"].startswith(">=3.14")
    assert any(
        item.get("name") == "stt-assistant" and item.get("version") == manifest["version"]
        for item in lock["package"]
    )


def test_installable_component_does_not_use_old_integration_identifier() -> None:
    """Every shipped implementation and user-facing JSON uses the new name."""
    for path in INTEGRATION.rglob("*"):
        if path.suffix not in {".py", ".json", ".yaml"}:
            continue
        text = path.read_text(encoding="utf-8")
        assert "assist_canonicalizer" not in text, str(path)
        assert "AssistCanonicalizer" not in text, str(path)
        assert "assist-canonicalizer" not in text, str(path)


def test_translation_jsons_are_parseable() -> None:
    """Translations remain valid JSON after project-wide identifier updates."""
    assert json.loads((INTEGRATION / "strings.json").read_text())
    for path in (INTEGRATION / "translations").glob("*.json"):
        assert isinstance(json.loads(path.read_text(encoding="utf-8")), dict)
