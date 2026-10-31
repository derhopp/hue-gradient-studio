#!/usr/bin/env python3
"""Update manifest version and the visible JavaScript card version string."""
from __future__ import annotations
import json
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    if len(sys.argv) != 2 or not re.fullmatch(r"\d+\.\d+\.\d+", sys.argv[1]):
        sys.exit("Usage: python3 scripts/bump_version.py MAJOR.MINOR.PATCH")
    version = sys.argv[1]
    manifest = ROOT / 'custom_components/hue_gradient_studio/manifest.json'
    obj = json.loads(manifest.read_text(encoding='utf-8'))
    old = obj['version']
    if old == version:
        print(f'Already {version}')
        return
    obj['version'] = version
    manifest.write_text(json.dumps(obj, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')
    js = ROOT / 'custom_components/hue_gradient_studio/frontend/hue-gradient-studio.js'
    text = js.read_text(encoding='utf-8').replace('Hue Gradient Studio v'+old, 'Hue Gradient Studio v'+version)
    js.write_text(text, encoding='utf-8')
    print(f'Updated {old} -> {version}. Write release notes, run tests, and push to main. CI publishes a GitHub Release after validation succeeds.')


if __name__ == '__main__':
    main()
