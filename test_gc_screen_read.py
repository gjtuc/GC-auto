"""gc_screen_read 단위 테스트 — OCR 없이 좌표·확대만."""
import json
import os
import tempfile
import unittest

from gc_screen_read import (
    Box,
    box_from_fraction,
    load_config,
    resolve_region_box,
    upscale_image,
)


class TestGcScreenRead(unittest.TestCase):
    def test_box_from_fraction(self):
        parent = Box(100, 200, 1000, 800)
        child = box_from_fraction(parent, [0.1, 0.2, 0.5, 0.3])
        self.assertEqual(child.left, 200)
        self.assertEqual(child.top, 360)
        self.assertEqual(child.width, 500)
        self.assertEqual(child.height, 240)

    def test_resolve_region_chain(self):
        cfg_path = os.path.join(
            os.path.dirname(__file__), "deploy", "screen_regions.gc1.json"
        )
        cfg = load_config(cfg_path)
        win = Box(0, 0, 1920, 1080)
        box, chain = resolve_region_box(cfg, "bottom_peak_table_fine", win)
        self.assertIn("autochro_window", chain)
        self.assertIn("bottom_peak_table", chain)
        self.assertEqual(chain[-1], "bottom_peak_table_fine")
        self.assertGreater(box.height, 50)

    def test_upscale_doubles_size(self):
        from PIL import Image

        img = Image.new("RGB", (100, 40), color=(255, 255, 255))
        up = upscale_image(img, 2.5)
        self.assertEqual(up.size, (250, 100))


if __name__ == "__main__":
    unittest.main()
