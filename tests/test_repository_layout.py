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
        self.assertEqual(manifest['integration_type'], 'hub')
        self.assertTrue((ROOT / 'scripts' / 'bump_version.py').is_file())
        self.assertFalse((ROOT / 'scripts' / 'prepare_repository.py').exists())

    def test_ui_only_setup_and_dashboard(self):
        backend = (COMPONENT / '__init__.py').read_text(encoding='utf-8')
        frontend = (COMPONENT / 'frontend' / 'hue-gradient-studio.js').read_text(encoding='utf-8')
        self.assertIn('async def async_setup_entry(', backend)
        self.assertNotIn('async def async_setup(', backend)
        self.assertNotIn('CONFIG_SCHEMA', backend)
        self.assertNotIn('import_legacy', backend)
        self.assertNotIn('import_legacy', frontend)
        self.assertNotIn('data-import', frontend)


if __name__ == '__main__':
    unittest.main()
