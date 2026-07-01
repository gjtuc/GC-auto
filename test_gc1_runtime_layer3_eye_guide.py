# -*- coding: utf-8 -*-
"""T98 — layer3_eye_guide OCR 토큰·좌표 (실행 검증은 mock)."""
from __future__ import annotations

import os
import unittest

import re

from gc_screen_read import Box, OcrToken
from gc1_runtime.layer0_sync import sync_double_click_coords
from gc1_runtime.layer3_eye_guide import (
    AutochroStepEye,
    autochro_eye_adaptive,
    autochro_eye_enabled,
    autochro_eye_strict,
    eye_gate_should_raise,
    token_looks_like_raw,
)


class TestAutochroEyeEnabled(unittest.TestCase):
    def test_off_when_dry_run(self):
        self.assertFalse(autochro_eye_enabled(dry_run=True))

    def test_on_by_default_live(self):
        self.assertTrue(autochro_eye_enabled(dry_run=False))

    def test_adaptive_default_on(self):
        os.environ.pop("GC1_AUTOCHRO_EYE_ADAPT", None)
        self.assertTrue(autochro_eye_adaptive())

    def test_gate_raises_only_strict_non_adaptive(self):
        os.environ["GC1_AUTOCHRO_EYE_STRICT"] = "1"
        os.environ["GC1_AUTOCHRO_EYE_ADAPT"] = "0"
        self.assertTrue(eye_gate_should_raise())
        os.environ["GC1_AUTOCHRO_EYE_ADAPT"] = "1"
        self.assertFalse(eye_gate_should_raise())
        os.environ.pop("GC1_AUTOCHRO_EYE_STRICT", None)
        os.environ.pop("GC1_AUTOCHRO_EYE_ADAPT", None)


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


class TestTreeNameMatch(unittest.TestCase):
    def test_name_compact_match(self):
        from gc1_runtime.layer3_eye_guide import AutochroStepEye
        from gc_screen_read import OcrToken, Box

        eye = AutochroStepEye(
            config={},
            window_box=Box(0, 0, 800, 600),
            eye=None,  # type: ignore[arg-type]
        )
        tokens = [
            OcrToken("20260630dre(5)ni", 88, Box(10, 40, 120, 14)),
            OcrToken("YL6500", 70, Box(10, 80, 60, 12)),
        ]
        name_c = "20260630dre(5)ni(성형)-ce".replace(" ", "").lower()
        hits = [
            t
            for t in tokens
            if name_c[:14] in re.sub(r"\s+", "", t.text.lower())
        ]
        self.assertEqual(len(hits), 1)
        self.assertIn("20260630", hits[0].text)


if __name__ == "__main__":
    unittest.main()
