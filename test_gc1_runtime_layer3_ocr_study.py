# -*- coding: utf-8 -*-
"""성숙도·마우스 가드·스터디 세션 단위 테스트."""
from __future__ import annotations

import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from gc1_runtime.layer3_ocr_maturity import (
    MATURITY_RATE,
    MIN_ATTEMPTS,
    is_skill_mature,
    record_outcome,
    skill_key,
)
from gc1_runtime.layer3_user_mouse_guard import UserMouseGuard


class TestMaturity(unittest.TestCase):
    def test_mature_at_threshold(self):
        with tempfile.TemporaryDirectory() as tmp:
            learn = Path(tmp) / "learn"
            learn.mkdir()
            with mock.patch("gc1_runtime.layer3_ocr_maturity.learnings_dir", return_value=learn):
                key = skill_key("P3.menu", "context_menu_popup", "초기화")
                for _ in range(MIN_ATTEMPTS):
                    record_outcome(key, success=True, method="ocr_click")
                self.assertTrue(is_skill_mature(key))

    def test_demote_on_failure(self):
        with tempfile.TemporaryDirectory() as tmp:
            learn = Path(tmp) / "learn"
            learn.mkdir()
            with mock.patch("gc1_runtime.layer3_ocr_maturity.learnings_dir", return_value=learn):
                key = skill_key("P4", "left_analysis_tree", "불러오기")
                for _ in range(MIN_ATTEMPTS):
                    record_outcome(key, success=True)
                self.assertTrue(is_skill_mature(key))
                record_outcome(key, success=False)
                self.assertFalse(is_skill_mature(key))


class TestMouseGuard(unittest.TestCase):
    def test_vibration_does_not_pause(self):
        g = UserMouseGuard()
        g._last = (100, 100)
        g._last = (100, 100)
        # simulate small jitter
        for i in range(5):
            g._last = (100 + i * 3, 100)
            dx = 3
            g._moves.append((__import__("time").time(), dx))
        self.assertFalse(g.paused)

    def test_swipe_pauses(self):
        g = UserMouseGuard()
        g._last = (0, 0)
        g._trigger("test")
        self.assertTrue(g.paused)


if __name__ == "__main__":
    unittest.main()
