"""Repository packaging/metadata smoke test for HACS releases."""
from pathlib import Path
import json
import re
import unittest

ROOT = Path(__file__).resolve().parents[1]
COMPONENT = ROOT / 'custom_components' / 'hue_gradient_studio'


class RepositoryStructureTests(unittest.TestCase):
    def test_required_metadata_and_bundled_assets(self):
        hacs = json.loads((ROOT / 'hacs.json').read_text(encoding='utf-8'))
        manifest = json.loads((COMPONENT / 'manifest.json').read_text(encoding='utf-8'))
        self.assertEqual(manifest['domain'], COMPONENT.name)
        self.assertTrue(manifest['version'])
        self.assertRegex(manifest['version'], r'^\d+\.\d+\.\d+$')
        for key in ('documentation', 'issue_tracker', 'codeowners', 'name', 'version'):
            self.assertIn(key, manifest)
        self.assertEqual(manifest['config_flow'], True)
        self.assertTrue(hacs['render_readme'])
        self.assertTrue((COMPONENT / 'frontend' / 'hue-gradient-studio.js').is_file())
        self.assertTrue((COMPONENT / 'config_flow.py').is_file())
        self.assertTrue((COMPONENT / 'frontend_resources.py').is_file())
        self.assertEqual(len(list((ROOT / 'custom_components').iterdir())), 1)


if __name__ == '__main__':
    unittest.main()
