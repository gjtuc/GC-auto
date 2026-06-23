# -*- coding: utf-8 -*-
"""GC3 Chem32 Report 파싱·병합 단위 테스트 (mock fixture, 실제 Chem32 PC 불필요)."""

import os
import unittest

from gc_console import setup_console_encoding

setup_console_encoding()

from gc_chem32 import (
    build_merged_injection_cycles,
    collect_reported_injections,
    cycles_match,
    default_sample_name_from_folder,
    find_active_sample_folder,
    parse_report_txt,
    resolve_chemstation_mode,
)

FIXTURE_ROOT = os.path.join(
    os.path.dirname(__file__),
    "test_fixtures",
    "chem32",
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


if __name__ == "__main__":
    unittest.main()
