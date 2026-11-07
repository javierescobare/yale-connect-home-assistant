"""Check distributable metadata and translations without contacting any service."""

from __future__ import annotations

import ast
import json
import struct
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
COMPONENT = ROOT / "custom_components" / "yale_connect"


def translation_paths(value: dict, prefix: str = "") -> set[str]:
    """Return translation leaf paths to detect missing or unexpected keys."""
    paths = set()
    for key, child in value.items():
        path = f"{prefix}.{key}" if prefix else key
        if isinstance(child, dict):
            paths.update(translation_paths(child, path))
        else:
            if not isinstance(child, str):
                raise ValueError(f"Translation must be a string: {path}")
            paths.add(path)
    return paths


def main() -> None:
    """Validate metadata, syntax and the minimal local brand images."""
    for source in COMPONENT.rglob("*.py"):
        ast.parse(source.read_text(encoding="utf-8"), filename=str(source))
    for source in COMPONENT.rglob("*.json"):
        json.loads(source.read_text(encoding="utf-8"))

    manifest = json.loads((COMPONENT / "manifest.json").read_text())
    assert manifest["domain"] == "yale_connect"
    assert manifest["codeowners"], "At least one code owner is required"
    assert manifest["config_flow"] is True
    assert manifest["iot_class"] == "cloud_polling"
    assert manifest["version"]
    for key in ("documentation", "issue_tracker"):
        assert manifest[key].startswith("https://github.com/"), key

    hacs = json.loads((ROOT / "hacs.json").read_text())
    assert hacs["name"] == manifest["name"]
    assert hacs["homeassistant"] == "2026.10.4"

    strings = json.loads((COMPONENT / "strings.json").read_text())
    english = json.loads((COMPONENT / "translations" / "en.json").read_text())
    assert strings == english, "The base strings must match the English translation"
    for source in (COMPONENT / "translations").glob("*.json"):
        translated = json.loads(source.read_text())
        assert translation_paths(translated) == translation_paths(strings), source.name

    for name, size in (("icon.png", 256), ("icon@2x.png", 512)):
        raw = (COMPONENT / "brand" / name).read_bytes()
        assert raw[:8] == b"\x89PNG\r\n\x1a\n", name
        assert struct.unpack(">II", raw[16:24]) == (size, size), name

    for name in (
        "README.md",
        "LICENSE",
        ".gitignore",
        "CONTRIBUTING.md",
        "SECURITY.md",
    ):
        assert (ROOT / name).is_file(), f"Missing project file: {name}"
    assert (ROOT / "docs" / "limitations.md").is_file()
    print("Repository metadata, Python syntax, translations and icons are valid.")


if __name__ == "__main__":
    main()
