# -*- coding: utf-8 -*-
"""GC3 갭 마커 → 차헌 PC parse_gc_sheet E2E (장비 PC·차헌 PC 계약 검증)."""

import importlib.util
import os
import sys
import tempfile
import unittest
from datetime import datetime

from gc_console import setup_console_encoding

setup_console_encoding()

REPO = os.path.dirname(os.path.abspath(__file__))
DATA_PC = os.path.join(REPO, "data_pc")
if DATA_PC not in sys.path:
    sys.path.insert(0, DATA_PC)

from gc_gap_contract import (  # noqa: E402
    GAP_MARKER_FIRST_COL,
    parse_gap_missing_cycles,
)
from gc_chem32 import AnalysisGap, gap_marker_cycle, insert_analysis_gap_markers
from gc_kch import build_stacked_dataframe_chem32, write_chem32_excel


def _load_calc_module():
    path = os.path.join(DATA_PC, "촉매 반응 계산.py")
    spec = importlib.util.spec_from_file_location("catalyst_calc", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _tcd_peak(area=100.0):
    return {
        "#": 1,
        "Time": 0.7,
        "Area": area,
        "Height": 1.0,
        "Width": 1.0,
        "Area%": 1.0,
        "Symmetry": "",
    }


def _fid_peak(area=50.0):
    return {
        "#": 1,
        "Time": 3.5,
        "Area": area,
        "Height": 1.0,
        "Width": 1.0,
        "Area%": 1.0,
        "Symmetry": "",
    }


class TestGcGapContract(unittest.TestCase):
    def test_parse_gap_from_time_and_symmetry(self):
        import pandas as pd

        row = pd.Series(
            {
                "#": GAP_MARKER_FIRST_COL,
                "Time": "약 6사이클 미수집",
                "Area": "공백 1시간",
                "Symmetry": "GC_GAP:N=6",
            }
        )
        self.assertEqual(parse_gap_missing_cycles(row), 6)

    def test_gap_marker_cycle_includes_machine_symmetry(self):
        gap = AnalysisGap(
            after_injection_index=0,
            before_injection_index=1,
            after_sequence="A",
            before_sequence="B",
            gap_sec=3600.0,
            interval_sec=600.0,
            missing_cycles=6,
            remainder_sec=0.0,
            after_last_at=datetime(2026, 6, 1, 10, 0, 0),
            before_first_at=datetime(2026, 6, 1, 11, 0, 0),
        )
        marker = gap_marker_cycle(gap)[0]
        self.assertEqual(marker["#"], "중단")
        self.assertIn("6사이클", marker["Time"])
        self.assertEqual(marker["Symmetry"], "GC_GAP:N=6")


class TestGc3GapE2E(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.calc = _load_calc_module()

    def _build_gap_excel(self, missing=6):
        tcd = [[_tcd_peak(100 + i)] for i in range(5)]
        fid = [[_fid_peak(50 + i)] for i in range(5)]
        paths = [
            r"C:\s\SEQ_A\001F0101.D",
            r"C:\s\SEQ_A\001F0102.D",
            r"C:\s\SEQ_A\001F0103.D",
            r"C:\s\SEQ_B\001F0101.D",
            r"C:\s\SEQ_B\001F0102.D",
        ]
        gap = AnalysisGap(
            after_injection_index=2,
            before_injection_index=3,
            after_sequence="SEQ_A",
            before_sequence="SEQ_B",
            gap_sec=missing * 600.0,
            interval_sec=600.0,
            missing_cycles=missing,
            remainder_sec=0.0,
            after_last_at=datetime(2026, 6, 1, 10, 0, 0),
            before_first_at=datetime(2026, 6, 1, 11, 0, 0),
        )
        tcd_out, fid_out = insert_analysis_gap_markers(
            tcd,
            fid,
            paths,
            [gap],
            [(path, os.path.dirname(path)) for path in paths],
        )
        tmp = tempfile.NamedTemporaryFile(suffix=".xlsx", delete=False)
        tmp.close()
        write_chem32_excel(tmp.name, fid_out, tcd_out)
        return tmp.name

    def test_parse_gc_sheet_skips_gap_cycles(self):
        xlsx = self._build_gap_excel(missing=6)
        try:
            import pandas as pd

            xls = pd.ExcelFile(xlsx)
            df_t = pd.read_excel(xls, sheet_name="TCD", header=None)
            df_t.columns = ["#", "Time", "Area", "Height", "Width", "Area%", "Symmetry"]
            df_p, warnings, gap_cycles = self.calc.parse_gc_sheet(
                df_t, "TCD", "GC3", self.calc.GC3_TIME_TCD
            )
            self.assertEqual(gap_cycles, set(range(5, 11)))
            self.assertTrue(any("미수집" in w for w in warnings))
            real_cycles = [2, 3, 4, 11, 12]
            for cyc in real_cycles:
                self.assertIn(cyc, df_p.index)
                self.assertGreater(df_p.loc[cyc, "H2 Area"], 0)
            for cyc in gap_cycles:
                self.assertTrue(pd.isna(df_p.loc[cyc, "H2 Area"]))
        finally:
            try:
                os.unlink(xlsx)
            except OSError:
                pass

    def test_stacked_dataframe_roundtrip_shape(self):
        peak = [_tcd_peak()]
        gap = AnalysisGap(
            after_injection_index=1,
            before_injection_index=2,
            after_sequence="A",
            before_sequence="B",
            gap_sec=600.0,
            interval_sec=600.0,
            missing_cycles=2,
            remainder_sec=0.0,
            after_last_at=datetime(2026, 1, 1, 1, 0, 0),
            before_first_at=datetime(2026, 1, 1, 2, 0, 0),
        )
        cycles = [peak, peak, gap_marker_cycle(gap), peak]
        df = build_stacked_dataframe_chem32(cycles)
        self.assertEqual(len(df), 8)  # (hdr+pk)*3 + hdr+marker + hdr+pk
        self.assertEqual(str(df.iloc[5]["#"]), "중단")


if __name__ == "__main__":
    unittest.main()
