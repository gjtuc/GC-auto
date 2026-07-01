"""gc_screen_read 단위 테스트 — OCR 없이 좌표·확대만."""
import json
import os
import tempfile
import unittest

from gc_screen_read import (
    Box,
    OcrToken,
    box_from_fraction,
    find_menu_needle_tokens,
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

    def test_focus_overlay_default_on(self):
        from gc_screen_read import ensure_ocr_focus_visible, focus_overlay_enabled

        old = os.environ.pop("GC_SCREEN_SHOW_FOCUS", None)
        try:
            self.assertTrue(focus_overlay_enabled())
            os.environ["GC_SCREEN_SHOW_FOCUS"] = "0"
            self.assertFalse(focus_overlay_enabled())
            os.environ.pop("GC_SCREEN_SHOW_FOCUS", None)
            ensure_ocr_focus_visible(case_study=True)
            self.assertTrue(focus_overlay_enabled())
            self.assertEqual(os.environ.get("GC_SCREEN_FOCUS_MS"), "1000")
        finally:
            if old is None:
                os.environ.pop("GC_SCREEN_SHOW_FOCUS", None)
            else:
                os.environ["GC_SCREEN_SHOW_FOCUS"] = old
            os.environ.pop("GC_SCREEN_FOCUS_MS", None)

    def test_adaptive_crop_tightens_on_needle(self):
        from gc_screen_read import OcrToken, adaptive_crop_frac, zoom_pipeline_settings, load_config

        cfg_path = os.path.join(os.path.dirname(__file__), "deploy", "screen_regions.gc1.json")
        cfg = load_config(cfg_path)
        opts = zoom_pipeline_settings(cfg, "top_sample_table")
        tokens = [OcrToken("1.raw", 90, Box(200, 40, 48, 14))]
        frac = adaptive_crop_frac(tokens, 800, 300, opts=opts, needles=["raw"])
        self.assertLess(frac, 0.5)

    def test_adaptive_stop_on_high_conf_needle(self):
        from gc_screen_read import OcrToken, should_stop_adaptive_zoom, zoom_pipeline_settings, load_config

        cfg = load_config(
            os.path.join(os.path.dirname(__file__), "deploy", "screen_regions.gc1.json")
        )
        opts = zoom_pipeline_settings(cfg, "top_sample_table")
        tokens = [OcrToken("1.raw", 65, Box(10, 10, 40, 12))]
        self.assertFalse(
            should_stop_adaptive_zoom(
                tokens, opts=opts, needles=["raw"], depth=0, max_depth=5
            )
        )
        tokens = [OcrToken("1.raw", 95, Box(10, 10, 40, 12))]
        opts2 = dict(opts)
        opts2["stop_confidence"] = 70
        self.assertTrue(
            should_stop_adaptive_zoom(
                tokens, opts=opts2, needles=["raw"], depth=0, max_depth=5
            )
        )

    def test_track_zoom_crop_and_center(self):
        from PIL import Image

        from gc_screen_read import (
            OcrToken,
            crop_image_around_center,
            pick_track_center,
            screen_view_from_image_crop,
        )

        img = Image.new("RGB", (300, 200), (255, 255, 255))
        tokens = [
            OcrToken("1.raw", 90, Box(40, 30, 50, 14)),
            OcrToken("2.raw", 85, Box(42, 55, 48, 12)),
        ]
        cx, cy = pick_track_center(tokens, 300, 200, needles=["raw"])
        self.assertGreater(cx, 0)
        cropped, cl, ct = crop_image_around_center(img, cx, cy, 0.5)
        view = Box(100, 200, 300, 200)
        sub = screen_view_from_image_crop(view, img, cl, ct, cropped.size[0], cropped.size[1])
        self.assertLess(sub.width, view.width)
        self.assertGreaterEqual(sub.left, view.left)


class TestMenuNeedleTokens(unittest.TestCase):
    def test_split_initialize_token(self):
        tokens = [
            OcrToken("초기", 97.0, Box(10, 40, 30, 12)),
            OcrToken("지우기", 96.0, Box(10, 20, 40, 12)),
        ]
        hits = find_menu_needle_tokens(tokens, "초기화", forbid=("정량",))
        self.assertEqual(len(hits), 1)
        self.assertEqual(hits[0].text, "초기")


if __name__ == "__main__":
    unittest.main()
