"""Validate bundled brand assets without third-party dependencies."""
from pathlib import Path
import struct
import unittest
import zlib


ROOT = Path(__file__).resolve().parents[1]
ICON = ROOT / "custom_components" / "hue_gradient_studio" / "brand" / "icon.png"


class BrandAssetsTests(unittest.TestCase):
    def test_icon_png_integrity(self):
        data = ICON.read_bytes()
        self.assertTrue(data.startswith(b"\x89PNG\r\n\x1a\n"))
        self.assertGreater(len(data), 10000, "Icon appears incomplete or too small")

        position = 8
        dimensions = None
        compressed = bytearray()
        saw_end = False
        while position + 12 <= len(data):
            length = struct.unpack_from(">I", data, position)[0]
            position += 4
            chunk_type = data[position:position + 4]
            position += 4
            self.assertLessEqual(position + length + 4, len(data))
            body = data[position:position + length]
            position += length
            checksum = struct.unpack_from(">I", data, position)[0]
            position += 4
            self.assertEqual(zlib.crc32(chunk_type + body) & 0xFFFFFFFF, checksum)
            if chunk_type == b"IHDR":
                dimensions = struct.unpack(">IIBBBBB", body)
            elif chunk_type == b"IDAT":
                compressed.extend(body)
            elif chunk_type == b"IEND":
                saw_end = True
                break

        self.assertTrue(saw_end, "PNG missing IEND")
        self.assertEqual(position, len(data), "Unexpected bytes after IEND")
        self.assertEqual(dimensions, (256, 256, 8, 6, 0, 0, 0))
        raw = zlib.decompress(compressed)
        self.assertEqual(len(raw), 256 * (1 + 4 * 256))


if __name__ == "__main__":
    unittest.main()
