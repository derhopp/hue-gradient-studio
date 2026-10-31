"""Tests for the maintainer-only version bump helper (no Home Assistant required)."""

import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
SOURCE_SCRIPT = ROOT / "scripts" / "bump_version.py"
SOURCE_COMPONENT = ROOT / "custom_components" / "hue_gradient_studio"


class VersionBumpTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.root = Path(self.directory.name)
        script = self.root / "scripts" / "bump_version.py"
        script.parent.mkdir(parents=True)
        shutil.copyfile(SOURCE_SCRIPT, script)
        self.script = script

        self.component = self.root / "custom_components" / "hue_gradient_studio"
        frontend = self.component / "frontend"
        frontend.mkdir(parents=True)
        self.manifest_path = self.component / "manifest.json"
        self.card_path = frontend / "hue-gradient-studio.js"
        shutil.copyfile(SOURCE_COMPONENT / "manifest.json", self.manifest_path)
        shutil.copyfile(
            SOURCE_COMPONENT / "frontend" / "hue-gradient-studio.js",
            self.card_path,
        )
        self.current = json.loads(self.manifest_path.read_text())["version"]
        major, minor, patch = map(int, self.current.split("."))
        self.next_version = f"{major}.{minor}.{patch + 1}"

    def _run(self, argument):
        return subprocess.run(
            [sys.executable, str(self.script), argument],
            cwd=self.root,
            capture_output=True,
            text=True,
            check=False,
        )

    def test_changes_all_version_references_and_is_idempotent(self):
        result = self._run(self.next_version)
        self.assertEqual(result.returncode, 0, result.stderr)
        manifest = json.loads(self.manifest_path.read_text())
        card = self.card_path.read_text()
        self.assertEqual(manifest["version"], self.next_version)
        self.assertEqual(card.count(f"Hue Gradient Studio v{self.next_version}"), 2)
        self.assertIn(
            f"from './i18n.js?v={self.next_version}'",
            card,
        )
        self.assertNotIn(f"from './i18n.js?v={self.current}'", card)
        before = (self.manifest_path.read_bytes(), self.card_path.read_bytes())
        second = self._run(self.next_version)
        self.assertEqual(second.returncode, 0, second.stderr)
        self.assertEqual(
            (self.manifest_path.read_bytes(), self.card_path.read_bytes()),
            before,
        )

    def test_rejects_missing_i18n_reference_without_changing_files(self):
        original = self.card_path.read_text()
        self.card_path.write_text(
            original.replace(
                f"from './i18n.js?v={self.current}'",
                "from './i18n.js?v=unexpected'",
            )
        )
        before = (self.manifest_path.read_bytes(), self.card_path.read_bytes())
        result = self._run(self.next_version)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("refusing a partial update", result.stderr)
        self.assertEqual(
            (self.manifest_path.read_bytes(), self.card_path.read_bytes()),
            before,
        )

    def test_invalid_version_is_rejected_without_changes(self):
        before = (self.manifest_path.read_bytes(), self.card_path.read_bytes())
        result = self._run("not-a-version")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("Usage:", result.stderr)
        self.assertEqual(
            (self.manifest_path.read_bytes(), self.card_path.read_bytes()),
            before,
        )


if __name__ == "__main__":
    unittest.main()
