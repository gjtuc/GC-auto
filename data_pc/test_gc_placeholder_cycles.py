# -*- coding: utf-8 -*-
"""빈 주입(# Time Area … 반복) → gap_cycles 미수집 처리 검증."""

import importlib.util
import os
import sys
import unittest

import pandas as pd

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
if SCRIPT_DIR not in sys.path:
    sys.path.insert(0, SCRIPT_DIR)

from gc_gap_contract import (  # noqa: E402
    GAP_MARKER_FIRST_COL,
    format_missing_cycle_warnings,
    is_empty_injection_placeholder_row,
)


def _load_calc_module():
    path = os.path.join(SCRIPT_DIR, "촉매 반응 계산.py")
    spec = importlib.util.spec_from_file_location("catalyst_calc", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _header_row():
    return pd.Series(
        {
            "#": "#",
            "Time": "Time",
            "Area": "Area",
            "Height": "Height",
            "Width": "Width",
            "Area%": "Area%",
            "Symmetry": "Symmetry",
        }
    )


def _peak_row(time=0.72, area=100.0):
    return pd.Series(
        {
            "#": 1,
            "Time": time,
            "Area": area,
            "Height": 1.0,
            "Width": 1.0,
            "Area%": 1.0,
            "Symmetry": "",
        }
    )


def _gap_row(n=2):
    return pd.Series(
        {
            "#": GAP_MARKER_FIRST_COL,
            "Time": f"약 {n}사이클 미수집",
            "Area": "공백",
            "Height": "",
            "Width": "",
            "Area%": "",
            "Symmetry": f"GC_GAP:N={n}",
        }
    )


class TestPlaceholderContract(unittest.TestCase):
    def test_placeholder_detected(self):
        self.assertTrue(is_empty_injection_placeholder_row(_header_row()))

    def test_peak_not_placeholder(self):
        self.assertFalse(is_empty_injection_placeholder_row(_peak_row()))

    def test_warning_range(self):
        msgs = format_missing_cycle_warnings(set(range(5, 14)), "피크 미기록 (빈 주입)")
        self.assertEqual(len(msgs), 1)
        self.assertIn("Cycle 5~13", msgs[0])
        self.assertIn("9사이클", msgs[0])


class TestParseGcSheetPlaceholders(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.calc = _load_calc_module()

    def test_nine_empty_injections_after_real_peak(self):
        rows = [
            _peak_row(),
            *[_header_row() for _ in range(9)],
            _peak_row(time=0.73, area=120.0),
        ]
        df = pd.DataFrame(rows)
        df_p, warnings, gap_cycles = self.calc.parse_gc_sheet(
            df, "TCD", "GC3", self.calc.GC3_TIME_TCD
        )
        self.assertEqual(gap_cycles, set(range(2, 11)))
        self.assertTrue(any("피크 미기록" in w for w in warnings))
        self.assertIn(1, df_p.index)
        self.assertIn(11, df_p.index)
        for cyc in range(2, 11):
            self.assertTrue(pd.isna(df_p.loc[cyc, "H2 Area"]))

    def test_placeholder_plus_gap_marker(self):
        rows = [
            _peak_row(),
            *[_header_row() for _ in range(9)],
            _header_row(),
            _gap_row(2),
            _peak_row(time=0.74, area=130.0),
        ]
        df = pd.DataFrame(rows)
        df_p, warnings, gap_cycles = self.calc.parse_gc_sheet(
            df, "TCD", "GC3", self.calc.GC3_TIME_TCD
        )
        self.assertEqual(gap_cycles, set(range(2, 13)))
        self.assertTrue(any("피크 미기록" in w for w in warnings))
        self.assertTrue(any("분석 중단" in w for w in warnings))
        self.assertIn(13, df_p.index)

    def test_header_with_peaks_not_gap(self):
        rows = [_header_row(), _peak_row(), _header_row(), _peak_row(time=0.75, area=90.0)]
        df = pd.DataFrame(rows)
        df_p, warnings, gap_cycles = self.calc.parse_gc_sheet(
            df, "TCD", "GC3", self.calc.GC3_TIME_TCD
        )
        self.assertEqual(gap_cycles, set())
        self.assertFalse(any("피크 미기록" in w for w in warnings))
        self.assertGreater(df_p.loc[2, "H2 Area"], 0)

    def test_single_header_run_before_peaks_is_delimiter(self):
        rows = [_peak_row(), _header_row(), _peak_row(time=0.73, area=120.0)]
        df = pd.DataFrame(rows)
        df_p, warnings, gap_cycles = self.calc.parse_gc_sheet(
            df, "TCD", "GC3", self.calc.GC3_TIME_TCD
        )
        self.assertEqual(gap_cycles, set())
        self.assertIn(2, df_p.index)
        self.assertGreater(df_p.loc[2, "H2 Area"], 0)


if __name__ == "__main__":
    unittest.main()
