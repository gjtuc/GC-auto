# -*- coding: utf-8 -*-
import json
import unittest
from pathlib import Path

from data_pc_origin.o0_mapping import DEFAULT_ORIGIN_MAPPING
from data_pc_origin.o0_series import GapPolicy
from data_pc_origin.o7_fixtures import SAMPLE_WRITE, MockWriteWks, fx_df_two_cols, gc3_gap_series
from data_pc_origin.o7_policy import prepare_column_list, select_gap_policy
from data_pc_origin.o7_write import write_h2_column, write_mapping_columns


class TestO7Write(unittest.TestCase):
    def test_gap_policy_default(self) -> None:
        self.assertEqual(select_gap_policy(environ={}), GapPolicy.AS_EMPTY)

    def test_h2_gap_rows(self) -> None:
        wks = MockWriteWks()
        _, vals, _ = write_h2_column(
            wks,
            2,
            gc3_gap_series(),
            SAMPLE_WRITE,
            gap_policy=GapPolicy.AS_EMPTY,
        )
        self.assertEqual(vals[99], "")
        self.assertEqual(vals[100], "")
        self.assertNotEqual(vals[99], 0.0)

    def test_write_mapping_artifact(self) -> None:
        wks = MockWriteWks()
        df = fx_df_two_cols()
        recs = write_mapping_columns(wks, 2, df, DEFAULT_ORIGIN_MAPPING, SAMPLE_WRITE)
        h2_rec = next(r for r in recs if len(r[1]) == 107)
        out = {
            "write_count": len(recs),
            "h2_len": len(h2_rec[1]),
            "gap_99": h2_rec[1][99],
            "gap_100": h2_rec[1][100],
            "comments": wks.writes[0][2],
            "prepared_head": prepare_column_list([1.0, float("nan")])[0:2],
        }
        p = Path(__file__).resolve().parent.parent / "o7_write_smoke.json"
        p.write_text(json.dumps(out, indent=2), encoding="utf-8")
        self.assertEqual(out["write_count"], 2)
        self.assertEqual(out["h2_len"], 107)
        self.assertEqual(out["gap_99"], "")


if __name__ == "__main__":
    unittest.main()
