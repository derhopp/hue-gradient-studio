"""Standalone check (run: python -m unittest discover -s tests -p 'test_encoder.py')."""
import unittest
import importlib.util
from pathlib import Path

P = Path(__file__).resolve().parents[1] / 'custom_components/hue_gradient_studio/gradient.py'
spec = importlib.util.spec_from_file_location('gradient', P)
gradient = importlib.util.module_from_spec(spec)
spec.loader.exec_module(gradient)


class EncoderTests(unittest.TestCase):
    def test_matches_old_card_for_four_presets(self):
        expected = [
            '500104000d3000000038e74453597c629b711800',
            '500104000d300000005ed56bf42366d3133d1800',
            '500104000d30000000f208512bf63ab415331800',
            '500104000d30000000927646a7985e5669781800',
        ]
        self.assertEqual([gradient.encode_gradient(p['colors']) for p in gradient.DEFAULT_PRESETS], expected)

    def test_valid_and_invalid_packets(self):
        packet = gradient.encode_gradient(['#ff0000','#00ff00','#0000ff'])
        self.assertEqual(len(packet), 40)
        self.assertTrue(packet.startswith('500104000d30000000'))
        self.assertTrue(packet.endswith('1800'))
        self.assertNotEqual(packet, gradient.encode_gradient(['#ff0000','#00ff00','#0000ff'], reverse=False))
        for bad in ([], ['#abc'], ['#ffffff']*4, ['red']*3):
            with self.assertRaises(ValueError):
                gradient.encode_gradient(bad)


if __name__ == '__main__':
    unittest.main()
