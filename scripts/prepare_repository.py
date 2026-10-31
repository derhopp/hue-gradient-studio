#!/usr/bin/env python3
"""Fill in repository metadata before the first publication.

Usage: python3 scripts/prepare_repository.py GITHUB_USERNAME [REPOSITORY_NAME]
"""
from __future__ import annotations
import json
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    if len(sys.argv) not in (2, 3):
        sys.exit("Usage: python3 scripts/prepare_repository.py GITHUB_USERNAME [REPOSITORY_NAME]")
    username = sys.argv[1]
    repo = sys.argv[2] if len(sys.argv) == 3 else "hue-gradient-studio"
    if not re.fullmatch(r"[A-Za-z\d](?:[A-Za-z\d-]{0,37}[A-Za-z\d])?", username):
        sys.exit("Invalid GitHub user/organization name")
    if not re.fullmatch(r"[A-Za-z\d_.-]{1,100}", repo):
        sys.exit("Invalid GitHub repository name")
    manifest = ROOT / "custom_components/hue_gradient_studio/manifest.json"
    data = json.loads(manifest.read_text(encoding="utf-8"))
    data["documentation"] = f"https://github.com/{username}/{repo}"
    data["issue_tracker"] = f"https://github.com/{username}/{repo}/issues"
    # A normal GitHub user can be a codeowner. For GitHub organizations,
    # adapt this to the account/team maintaining the project.
    data["codeowners"] = [f"@{username}"]
    manifest.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    readme = ROOT / "README.md"
    content = readme.read_text(encoding="utf-8")
    content = content.replace("YOUR_GITHUB_USERNAME", username).replace("hue-gradient-studio.git", f"{repo}.git")
    content = content.replace(f"/{username}/hue-gradient-studio", f"/{username}/{repo}")
    readme.write_text(content, encoding="utf-8")
    print(f"Repository metadata set to https://github.com/{username}/{repo}")
    print("Check manifest.json and README.md, then commit and publish.")


if __name__ == "__main__":
    main()
