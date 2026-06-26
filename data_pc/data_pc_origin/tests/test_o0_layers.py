# -*- coding: utf-8 -*-
"""O0 — 순수 로직 단위 테스트 (originpro 불필요)."""

from __future__ import annotations

import math
import unittest

import pandas as pd

from data_pc_origin.o0_comments import comment_matches_identity, parse_comment_date
from data_pc_origin.o0_identity import identity_match_tokens
from data_pc_origin.o0_keys import normalize_origin_key
from data_pc_origin.o0_mapping import (
    DEFAULT_ORIGIN_MAPPING,
    MappingValidationError,
    validate_mapping,
)
from data_pc_origin.o0_series import GapPolicy, column_to_origin_list


class TestO0Keys(unittest.TestCase):
    def test_normalize_strips_spaces_and_lower(self):
        self.assertEqual(normalize_origin_key("H2 yield"), "h2yield")
        self.assertEqual(normalize_origin_key("  CO2   conversion "), "co2conversion")

    def test_normalize_empty(self):
        self.assertEqual(normalize_origin_key(""), "")
        self.assertEqual(normalize_origin_key(None), "")


class TestO0Comments(unittest.TestCase):
    def test_parse_comment_date(self):
        self.assertEqual(
            parse_comment_date("20260620 DRE(1.5)@600°C Ni5"),
            "20260620",
        )
        self.assertIsNone(parse_comment_date("no date here"))

    def test_comment_matches_identity(self):
        key = ("20260620", "dre(1.5) 600c ni5_ce5_al2o3")
        comment = "20260620 DRE(1.5)@600°C 600CNi5_Ce5_Al2O3"
        self.assertTrue(comment_matches_identity(comment, key))
        self.assertFalse(comment_matches_identity("20260619 other", key))


class TestO0Identity(unittest.TestCase):
    def test_tokens_nonempty(self):
        tokens = identity_match_tokens("dre(1.5) 600c ni5_ce5_al2o3")
        self.assertIn("dre", tokens)
        self.assertTrue(len(tokens) >= 2)


class TestO0Series(unittest.TestCase):
    def test_gap_as_empty_preserves_length(self):
        series = [1.0, float("nan"), float("nan"), 4.0]
        out = column_to_origin_list(series, gap_policy=GapPolicy.AS_EMPTY)
        self.assertEqual(len(out), 4)
        self.assertEqual(out[0], 1.0)
        self.assertEqual(out[1], "")
        self.assertEqual(out[2], "")
        self.assertEqual(out[4 - 1], 4.0)

    def test_gap_as_nan(self):
        out = column_to_origin_list([1.0, float("nan")], gap_policy=GapPolicy.AS_NAN)
        self.assertEqual(len(out), 2)
        self.assertTrue(math.isnan(out[1]))

    def test_gap_skip_rows_shortens(self):
        out = column_to_origin_list([1.0, float("nan"), 3.0], gap_policy=GapPolicy.SKIP_ROWS)
        self.assertEqual(out, [1.0, 3.0])

    def test_pandas_series_input(self):
        s = pd.Series([10.0, None])
        out = column_to_origin_list(s.tolist(), gap_policy=GapPolicy.AS_EMPTY)
        self.assertEqual(out, [10.0, ""])


class TestO0Mapping(unittest.TestCase):
    def test_default_mapping_valid(self):
        m = validate_mapping()
        self.assertIn("H2 Yield (%)", m)
        self.assertEqual(m["H2 Yield (%)"], "H2 yield")

    def test_default_matches_calc_count(self):
        self.assertEqual(len(DEFAULT_ORIGIN_MAPPING), 8)

    def test_reject_empty_key(self):
        with self.assertRaises(MappingValidationError):
            validate_mapping({"": "H2 yield"})

    def test_worksheet_keyword_match_via_normalize(self):
        """O5 미구현 — O0에서 키 매칭 가능 여부만 검증."""
        keyword = "H2 yield"
        search = "Book1 H2yield Sheet1"
        self.assertIn(normalize_origin_key(keyword), normalize_origin_key(search))


if __name__ == "__main__":
    unittest.main()
