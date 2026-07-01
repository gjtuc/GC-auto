# -*- coding: utf-8 -*-
"""tree name token scoring."""
from __future__ import annotations

import unittest

from gc_screen_read import Box, OcrToken
from gc1_runtime.layer3_eye_guide import _pick_tree_name_token, _score_tree_name_token


class TestTreeNameScore(unittest.TestCase):
    def test_rejects_single_char(self):
        tok = OcrToken("성", 90, Box(0, 0, 10, 12))
        self.assertLess(_score_tree_name_token(tok, "20260630dre(5)ni"), 0)

    def test_prefers_date_prefix(self):
        good = OcrToken("20260630dre(5)ni", 80, Box(0, 40, 120, 14))
        bad = OcrToken("화면분석", 95, Box(0, 10, 60, 12))
        name = "20260630dre(5)ni(성형)-ce"
        self.assertGreater(
            _score_tree_name_token(good, name),
            _score_tree_name_token(bad, name),
        )

    def test_rejects_child_label(self):
        tok = OcrToken("시료정보", 90, Box(0, 50, 60, 12))
        self.assertLess(_score_tree_name_token(tok, "20260630dre(5)ni(성형)-ce"), 0)

    def test_pick_topmost_parent(self):
        parent = OcrToken("20260630dre(5)ni", 85, Box(10, 30, 100, 14))
        child = OcrToken("20260630dre(5)ni", 88, Box(10, 55, 100, 14))
        best = _pick_tree_name_token([child, parent], "20260630dre(5)ni(성형)-ce")
        self.assertIsNotNone(best)
        self.assertEqual(best.box.top, 30)


if __name__ == "__main__":
    unittest.main()
