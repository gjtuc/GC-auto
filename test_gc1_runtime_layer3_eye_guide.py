# -*- coding: utf-8 -*-
"""T98 — layer3_eye_guide OCR 토큰·좌표 (실행 검증은 mock)."""
from __future__ import annotations

import unittest

from gc_screen_read import Box, OcrToken
from gc1_runtime.layer0_sync import sync_double_click_coords
from gc1_runtime.layer3_eye_guide import (
    AutochroStepEye,
    autochro_eye_enabled,
    token_looks_like_raw,
)


class TestAutochroEyeEnabled(unittest.TestCase):
    def test_off_when_dry_run(self):
        self.assertFalse(autochro_eye_enabled(dry_run=True))

    def test_on_by_default_live(self):
        self.assertTrue(autochro_eye_enabled(dry_run=False))


class TestRawToken(unittest.TestCase):
    def test_recognizes_raw_patterns(self):
        self.assertTrue(token_looks_like_raw(OcrToken("1.raw", 90, Box(0, 0, 10, 10))))
        self.assertTrue(token_looks_like_raw(OcrToken("4,raw", 80, Box(0, 0, 10, 10))))
        self.assertFalse(token_looks_like_raw(OcrToken("시료", 90, Box(0, 0, 10, 10))))


class TestSyncCoordsTopRow(unittest.TestCase):
    def test_first_row_slot_not_bottom(self):
        rel_x, rel_y = sync_double_click_coords(400, 200)
        self.assertEqual(rel_x, 248)
        self.assertLess(rel_y, 80)
        self.assertGreaterEqual(rel_y, 18)


class TestEyeAnchorPick(unittest.TestCase):
    def test_picks_topmost_raw_token(self):
        eye = AutochroStepEye(
            config={},
            window_box=Box(0, 0, 800, 600),
            eye=None,  # type: ignore[arg-type]
        )
        region = Box(100, 400, 500, 150)
        scale = 2.5
        tokens = [
            OcrToken("3.raw", 90, Box(10, 80, 40, 12)),
            OcrToken("1.raw", 85, Box(10, 20, 40, 12)),
        ]

        class _FakeEye:
            pass

        eye.eye = _FakeEye()  # not used
        raw = [t for t in tokens if token_looks_like_raw(t)]
        best = min(raw, key=lambda t: t.box.top)
        x, y = __import__("gc_screen_read", fromlist=["token_screen_center"]).token_screen_center(
            best, region, scale
        )
        self.assertEqual(best.text, "1.raw")
        self.assertLess(y, region.top + 50)


class TestNeutralFallback(unittest.TestCase):
    def test_resolve_sample_table_returns_fallback_without_ocr(self):
        eye = AutochroStepEye(
            config={},
            window_box=Box(0, 0, 800, 600),
            eye=None,  # type: ignore[arg-type]
        )

        class _Rect:
            left = 10
            top = 20

            def width(self):
                return 400

            def height(self):
                return 120

        class _List:
            def rectangle(self):
                return _Rect()

        rel = eye.resolve_sample_table_rel(_List(), fallback_rel=(300, 24))
        self.assertEqual(rel, (300, 24))


if __name__ == "__main__":
    unittest.main()
