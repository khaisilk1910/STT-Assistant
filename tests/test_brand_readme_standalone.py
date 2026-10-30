"""Stdlib-only regression checks for docs and Home Assistant brand assets."""

import json
import struct
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BRAND = ROOT / "custom_components" / "stt_assistant" / "brand"
REPO = "https://github.com/khaisilk1910/STT-Assistant"


def test_readme_bilingual_install_links() -> None:
    for filename in ("README.md", "README.en.md"):
        text = (ROOT / filename).read_text(encoding="utf-8")
        assert "README.md" in text and "README.en.md" in text
        assert REPO in text
        assert "my.home-assistant.io/badges/hacs_repository.svg" in text
        assert "owner=khaisilk1910&repository=STT-Assistant&category=integration" in text
        assert "custom_components/stt_assistant" in text
        assert "assist_canonicalizer" in text  # Migration warning.
        assert "logger:" in text
        assert "luuquangvu" not in text


def test_manifest_points_to_project_repo() -> None:
    manifest = json.loads((ROOT / "custom_components/stt_assistant/manifest.json").read_text())
    assert manifest["domain"] == "stt_assistant"
    assert manifest["documentation"] == REPO
    assert manifest["issue_tracker"] == REPO + "/issues"
    assert manifest["codeowners"] == ["@khaisilk1910"]


def test_brand_dimensions_and_transparency() -> None:
    for prefix, dimensions in (
        ("icon", (256, 256)),
        ("logo", (960, 240)),
        ("dark_icon", (256, 256)),
        ("dark_logo", (960, 240)),
    ):
        for scale, suffix in ((1, ""), (2, "@2x")):
            image = BRAND / f"{prefix}{suffix}.png"
            content = image.read_bytes()
            assert content[:8] == b"\x89PNG\r\n\x1a\n"
            assert content[12:16] == b"IHDR"
            width, height, bit_depth, colour_type = struct.unpack(">IIBB", content[16:26])
            assert (width, height) == tuple(value * scale for value in dimensions)
            assert bit_depth == 8
            assert colour_type == 6  # PNG RGBA.
