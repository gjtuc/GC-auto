# -*- coding: utf-8 -*-
"""FID/TCD 탭이면 이름으로 시트를 나누고, 장비는 TCD H2만 고른다."""

import importlib.util
import os
import sys
import tempfile
import unittest

import pandas as pd

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
if SCRIPT_DIR not in sys.path:
    sys.path.insert(0, SCRIPT_DIR)


def _load_calc_module():
    path = os.path.join(SCRIPT_DIR, "촉매 반응 계산.py")
    spec = importlib.util.spec_from_file_location("catalyst_calc_tab", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _peak_row(time, area):
    return {"#": "", "Time": time, "Area": area, "Height": 1, "Width": 0.1, "Area%": 1, "Symmetry": 1}


class FidTcdTabTests(unittest.TestCase):
    def test_stray_fid_peak_does_not_drop_gc3_fid(self):
        calc = _load_calc_module()
        fid = pd.DataFrame(
            [
                _peak_row(1.801, 50),
                _peak_row(3.398, 1200),
                _peak_row(5.360, 800),
            ]
        )
        tcd = pd.DataFrame(
            [
                _peak_row(0.714, 9000),
                _peak_row(2.018, 1600),
                _peak_row(6.309, 500),
            ]
        )
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "20260909 DRME(3)@600C Ni.xlsx")
            with pd.ExcelWriter(path) as writer:
                fid.to_excel(writer, sheet_name="FID", index=False)
                tcd.to_excel(writer, sheet_name="TCD", index=False)
            xls = pd.ExcelFile(path)
            try:
                named = calc._classify_named_fid_tcd(xls)
            finally:
                xls.close()
            self.assertEqual(named[0], "GC3")
            df, _out, warnings, _feed = calc.process_excel(path)
        self.assertIsNotNone(df)
        self.assertGreater(float(df["CH4 Area"].iloc[0]), 0)
        self.assertGreater(float(df["C2H6 Area"].iloc[0]), 0)
        self.assertNotIn("장비 판별 실패", " ".join(warnings))

    def test_gc1_h2_stays_gc1(self):
        calc = _load_calc_module()
        fid = pd.DataFrame([_peak_row(1.4, 100), _peak_row(1.8, 200)])
        tcd = pd.DataFrame([_peak_row(2.0, 9000), _peak_row(6.2, 100), _peak_row(16.0, 80)])
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "20260101 DRE(1.5)@600C Ni.xlsx")
            with pd.ExcelWriter(path) as writer:
                fid.to_excel(writer, sheet_name="FID", index=False)
                tcd.to_excel(writer, sheet_name="TCD", index=False)
            xls = pd.ExcelFile(path)
            try:
                named = calc._classify_named_fid_tcd(xls)
            finally:
                xls.close()
            self.assertEqual(named[0], "GC1")


if __name__ == "__main__":
    unittest.main()
