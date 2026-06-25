# -*- coding: utf-8 -*-
"""GC3 Chem32 Report 파싱·병합 단위 테스트 (mock fixture, 실제 Chem32 PC 불필요)."""

import os
import unittest

from gc_console import setup_console_encoding

setup_console_encoding()

from gc_chem32 import (
    analysis_gaps_email_lines,
    build_merged_injection_cycles,
    collect_reported_injections,
    cycles_match,
    default_sample_name_from_folder,
    describe_cycle_mismatch,
    detect_analysis_gaps,
    estimate_missing_cycles_floor,
    find_active_sample_folder,
    find_sample_folders,
    find_sequence_folders,
    format_duration_korean,
    get_latest_sequence_datetime,
    parse_sequence_datetime,
    parse_report_txt,
    resolve_chemstation_mode,
)

FIXTURE_ROOT = os.path.join(
    os.path.dirname(__file__),
    "test_fixtures",
    "chem32",
)
MULTI_FIXTURE_ROOT = os.path.join(
    os.path.dirname(__file__),
    "test_fixtures",
    "chem32_multi",
)
REPORT_TXT = os.path.join(
    FIXTURE_ROOT,
    "20260101 sample DRM",
    "REACTION 2026-01-01 10-00-00",
    "001F0101.D",
    "Report.TXT",
)


class TestGcChem32(unittest.TestCase):
    def test_resolve_chemstation_mode_from_path(self):
        self.assertEqual(resolve_chemstation_mode(r"C:\Chem32\1\Data", "auto"), "chem32")
        self.assertEqual(
            resolve_chemstation_mode(r"C:\Users\Public\Documents\ChemStation\1\Data", "auto"),
            "8860",
        )

    def test_parse_report_txt_fid_tcd(self):
        parsed = parse_report_txt(REPORT_TXT)
        self.assertEqual(len(parsed["FID"]), 2)
        self.assertEqual(len(parsed["TCD"]), 2)
        self.assertAlmostEqual(parsed["FID"][0]["Time"], 0.523, places=3)
        self.assertAlmostEqual(parsed["TCD"][0]["Area"], 5500.0, places=1)

    def test_find_active_sample_folder(self):
        folder = find_active_sample_folder(FIXTURE_ROOT)
        self.assertIsNotNone(folder)
        self.assertIn("sample DRM", folder)

    def test_default_sample_name_from_folder(self):
        name = default_sample_name_from_folder(
            os.path.join(FIXTURE_ROOT, "20260101 sample DRM")
        )
        self.assertIn("sample DRM", name)

    def test_collect_and_merge_cycles(self):
        sample = os.path.join(FIXTURE_ROOT, "20260101 sample DRM")
        injections = collect_reported_injections(sample)
        self.assertEqual(len(injections), 1)
        fid_cycles, tcd_cycles, matched, skipped = build_merged_injection_cycles(sample)
        self.assertEqual(skipped, 0)
        self.assertEqual(len(fid_cycles), 1)
        self.assertEqual(len(tcd_cycles), 1)
        self.assertEqual(len(fid_cycles[0]), 2)
        self.assertEqual(len(matched), 1)

    def test_cycles_match_same_signature(self):
        peaks = parse_report_txt(REPORT_TXT)["FID"]
        self.assertTrue(cycles_match(peaks, peaks))

    def test_sliding_allows_cumulative_area_drift(self):
        peak_a = {
            "#": 1,
            "Time": 1.0,
            "Area": 100.0,
            "Height": 1.0,
            "Width": 1.0,
            "Area%": 1.0,
            "Symmetry": 1.0,
        }
        peak_b = dict(peak_a, Area=87.0)
        peak_c = dict(peak_a, Area=82.0)
        self.assertFalse(cycles_match([peak_a], [peak_b]))
        self.assertTrue(cycles_match([peak_b], [peak_c]))
        self.assertIn("Area", describe_cycle_mismatch([peak_a], [peak_b]))

    def test_parse_report_peak_scientific_area_percent(self):
        """Chem32 가 100% 를 1.000e2 로 쓰는 경우 — FID 누락 방지."""
        import re
        from gc_chem32 import REPORT_PEAK_LINE, _peak_row

        line = "   1   3.464 BB    0.0207  169.02991  124.32259 1.000e2"
        match = REPORT_PEAK_LINE.match(line)
        self.assertIsNotNone(match)
        peak = _peak_row(
            1,
            float(match.group(2)),
            float(match.group(4)),
            float(match.group(5)),
            float(match.group(6)),
            float(match.group(7)),
        )
        self.assertAlmostEqual(peak["Area%"], 100.0, places=1)

    def test_merged_fid_tcd_cycle_count_equal(self):
        sample = os.path.join(FIXTURE_ROOT, "20260101 sample DRM")
        fid_cycles, tcd_cycles, matched, _skipped = build_merged_injection_cycles(sample)
        self.assertEqual(len(fid_cycles), len(tcd_cycles))
        self.assertEqual(len(fid_cycles), len(matched))

    def test_parse_sequence_datetime_trailing_only(self):
        dt = parse_sequence_datetime(
            r"C:\Data\sample\20260608 REACTION 2026-06-09 10-26-46"
        )
        self.assertIsNotNone(dt)
        self.assertEqual(dt.strftime("%Y-%m-%d %H:%M:%S"), "2026-06-09 10:26:46")
        tcd = parse_sequence_datetime(
            r"C:\Data\sample\REACTION_TCD-FID 297 CYCLE 2026-06-05 17-26-24"
        )
        self.assertEqual(tcd.strftime("%Y-%m-%d %H:%M:%S"), "2026-06-05 17:26:24")

    def test_default_sample_name_yymmdd_underscore(self):
        name = default_sample_name_from_folder(
            os.path.join(MULTI_FIXTURE_ROOT, "260521_DRME_OLD")
        )
        self.assertEqual(name, "DRME_OLD")

    def test_find_active_sample_by_latest_sequence_not_folder_mtime(self):
        active = find_active_sample_folder(MULTI_FIXTURE_ROOT)
        self.assertIsNotNone(active)
        self.assertIn("20260620 DRE active", active)
        ranked = find_sample_folders(MULTI_FIXTURE_ROOT)
        self.assertIn("20260620 DRE active", ranked[0])

    def test_merge_multiple_sequences_inside_active_sample(self):
        sample = os.path.join(MULTI_FIXTURE_ROOT, "20260620 DRE active")
        sequences = find_sequence_folders(sample)
        self.assertEqual(len(sequences), 3)
        self.assertEqual(
            os.path.basename(sequences[0]),
            "20260608 REACTION 2026-06-09 11-00-00",
        )
        self.assertEqual(
            os.path.basename(sequences[-1]),
            "20260608 REACTION 2026-06-09 13-53-26",
        )
        injections = collect_reported_injections(sample)
        self.assertEqual(len(injections), 3)
        latest = get_latest_sequence_datetime(sample)
        self.assertEqual(latest.strftime("%Y-%m-%d %H:%M:%S"), "2026-06-09 13:53:26")

    def test_estimate_missing_cycles_floor_remainder_discarded(self):
        gap_sec = 3 * 3600 + 15 * 60
        interval_sec = 58 * 60 + 23
        missing, remainder = estimate_missing_cycles_floor(gap_sec, interval_sec)
        self.assertEqual(missing, 3)
        self.assertGreaterEqual(remainder, 19 * 60)
        self.assertLess(remainder, 20 * 60)

    def test_short_gap_counts_as_zero_missing(self):
        interval_sec = 58 * 60 + 23
        missing, remainder = estimate_missing_cycles_floor(39 * 60, interval_sec)
        self.assertEqual(missing, 0)
        self.assertAlmostEqual(remainder, 39 * 60, delta=1)

    def test_detect_analysis_gaps_on_gc3_e2e_sample(self):
        sample = os.path.join(
            os.path.dirname(__file__),
            "testdata",
            "gc3_e2e",
            "Chem32",
            "1",
            "DATA",
            "20260611 DRME 600C Ni0.1g8g_Ni5_Ce5",
        )
        if not os.path.isdir(sample):
            self.skipTest("gc3_e2e fixture missing")
        gaps, interval = detect_analysis_gaps(sample)
        self.assertIsNotNone(interval)
        self.assertGreater(interval, 3000)
        self.assertGreaterEqual(len(gaps), 1)
        total = sum(gap.missing_cycles for gap in gaps)
        self.assertGreaterEqual(total, 20)
        lines = analysis_gaps_email_lines(gaps, interval)
        self.assertTrue(any("미수집" in line for line in lines))
        self.assertIn("버림", "\n".join(lines))


if __name__ == "__main__":
    unittest.main()
