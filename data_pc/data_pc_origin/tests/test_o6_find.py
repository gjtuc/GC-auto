# -*- coding: utf-8 -*-
import json
import unittest
from pathlib import Path

from data_pc_origin.o6_find import find_column_by_identity, find_column_exact_comment
from data_pc_origin.o6_fixtures import (
    IDENTITY_KEY,
    SAMPLE_EXACT,
    SAMPLE_NEW,
    fx_wks_exact_match,
    fx_wks_identity_match,
)
from data_pc_origin.o6_plan import plan_insert_index, sample_sort_date
from data_pc_origin.o6_scan import dated_columns


class TestO6Find(unittest.TestCase):
    def test_exact_hit(self) -> None:
        wks = fx_wks_exact_match()
        self.assertEqual(find_column_exact_comment(wks, SAMPLE_EXACT), 2)

    def test_exact_miss(self) -> None:
        wks = fx_wks_exact_match()
        self.assertIsNone(find_column_exact_comment(wks, "missing"))

    def test_identity_hit(self) -> None:
        wks = fx_wks_identity_match()
        self.assertEqual(find_column_by_identity(wks, IDENTITY_KEY), 2)

    def test_write_find_artifact(self) -> None:
        wks = fx_wks_exact_match()
        out = {
            "exact_col": find_column_exact_comment(wks, SAMPLE_EXACT),
            "identity_col": find_column_by_identity(fx_wks_identity_match(), IDENTITY_KEY),
            "sample_date": sample_sort_date(SAMPLE_NEW),
            "insert_at": plan_insert_index(
                dated_columns(wks),
                sample_sort_date(SAMPLE_NEW),
            ),
        }
        p = Path(__file__).resolve().parent.parent / "o6_find_smoke.json"
        p.write_text(json.dumps(out, indent=2), encoding="utf-8")
        self.assertEqual(out["exact_col"], 2)
        self.assertEqual(out["insert_at"], 2)


if __name__ == "__main__":
    unittest.main()
