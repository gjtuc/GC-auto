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

    def test_pick_best(self):
        tokens = [
            OcrToken("성", 90, Box(10, 40, 8, 12)),
            OcrToken("20260630dre", 75, Box(10, 80, 90, 14)),
        ]
        best = _pick_tree_name_token(tokens, "20260630dre(5)ni(성형)-ce")
        self.assertIsNotNone(best)
        self.assertIn("20260630", best.text)


if __name__ == "__main__":
    unittest.main()
