#!/usr/bin/env python3
"""Update all release version references for Hue Gradient Studio.

Development helper only. HACS and GitHub Actions do not run this script.
Run from anywhere: python3 scripts/bump_version.py MAJOR.MINOR.PATCH
"""
from __future__ import annotations

import json
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
COMPONENT = ROOT / "custom_components" / "hue_gradient_studio"


def main() -> None:
    if len(sys.argv) != 2 or not re.fullmatch(r"\d+\.\d+\.\d+", sys.argv[1]):
        sys.exit("Usage: python3 scripts/bump_version.py MAJOR.MINOR.PATCH")

    version = sys.argv[1]
    manifest_path = COMPONENT / "manifest.json"
    card_path = COMPONENT / "frontend" / "hue-gradient-studio.js"

    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    old = manifest["version"]

    if old == version:
        print(f"Already {version}")
        return

    card = card_path.read_text(encoding="utf-8")
    old_label = f"Hue Gradient Studio v{old}"
    old_import = f"from './i18n.js?v={old}'"

    # Validate before writing either file, to avoid partially updated versions.
    if card.count(old_label) != 2:
        sys.exit(
            f"Expected two JavaScript version labels ({old_label!r}); "
            "refusing a partial update."
        )
    if card.count(old_import) != 1:
        sys.exit(
            f"Expected one JavaScript i18n import ({old_import!r}); "
            "refusing a partial update."
        )

    updated_card = card.replace(old_label, f"Hue Gradient Studio v{version}")
    updated_card = updated_card.replace(old_import, f"from './i18n.js?v={version}'")

    manifest["version"] = version
    manifest_path.write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    card_path.write_text(updated_card, encoding="utf-8")

    print(f"Updated {old} -> {version} in manifest, card labels and i18n cache URL.")
    print("Next: write release notes, run tests and push to main.")


if __name__ == "__main__":
    main()
