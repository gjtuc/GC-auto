# -*- coding: utf-8 -*-
"""GC2 시료 폴더명 정규화·활성 시료 선택·시퀀스 병합 테스트."""
from __future__ import annotations

import os
import tempfile
import unittest

from gc_sanitize import (
    is_chemstation_auto_sequence_name,
    normalize_gc2_folder_sample_name,
)
from gc_chemstation import (
    collect_acam_injections,
    find_8860_sequence_folders,
    find_active_sample_folder_8860,
    newest_injection_datetime,
)


def _touch_acam(injection_dir: str) -> str:
    os.makedirs(injection_dir, exist_ok=True)
    acam = os.path.join(injection_dir, "sequence.acam_")
    with open(acam, "wb") as handle:
        handle.write(b"<ACAML/>")
    return acam


class TestNormalizeGc2FolderName(unittest.TestCase):
    def test_compact_to_spaced(self):
        self.assertEqual(
            normalize_gc2_folder_sample_name("20260724DRE(1.5)600CNi5-Al2O3"),
            "20260724 DRE(1.5%)@600C Ni5-Al2O3",
        )

    def test_drm_compact(self):
        self.assertEqual(
            normalize_gc2_folder_sample_name("20260710DRM(5)700CNi5-Al2O3"),
            "20260710 DRM(5%)@700C Ni5-Al2O3",
        )

    def test_already_spaced(self):
        self.assertEqual(
            normalize_gc2_folder_sample_name("20260724 DRE(1.5%)@600C Ni5-Al2O3"),
            "20260724 DRE(1.5%)@600C Ni5-Al2O3",
        )

    def test_auto_sequence_returns_none(self):
        self.assertTrue(
            is_chemstation_auto_sequence_name("20251221 sequence 2026-07-24 15-23-24")
        )
        self.assertIsNone(
            normalize_gc2_folder_sample_name("20251221 sequence 2026-07-24 15-23-24")
        )


class TestActiveSampleFolder8860(unittest.TestCase):
    def test_picks_sample_by_newest_f_datetime(self):
        with tempfile.TemporaryDirectory() as data:
            old = os.path.join(data, "20260701DRE(1)600Cold")
            old_seq = os.path.join(old, "20251221 sequence 2026-07-01 10-00-07")
            _touch_acam(os.path.join(old_seq, "F-2026-07-01-10-00-07-x.D"))

            new = os.path.join(data, "20260724DRE(1.5)600CNi5-Al2O3")
            new_seq = os.path.join(new, "20251221 sequence 2026-07-24 15-23-24")
            _touch_acam(os.path.join(new_seq, "F-2026-07-24-15-23-24-x.D"))

            active = find_active_sample_folder_8860(data)
            self.assertEqual(active, new)
            self.assertEqual(
                newest_injection_datetime(active).strftime("%Y-%m-%d %H:%M:%S"),
                "2026-07-24 15:23:24",
            )

    def test_merges_multiple_sequences_under_sample(self):
        with tempfile.TemporaryDirectory() as data:
            sample = os.path.join(data, "20260724DRE(1.5)600CNi5-Al2O3")
            seq1 = os.path.join(sample, "20251221 sequence 2026-07-24 15-23-24")
            seq2 = os.path.join(sample, "20251221 sequence 2026-07-24 18-00-00")
            inj1 = os.path.join(seq1, "F-2026-07-24-15-23-24-a.D")
            inj2 = os.path.join(seq2, "F-2026-07-24-18-00-00-b.D")
            _touch_acam(inj1)
            _touch_acam(inj2)

            self.assertEqual(len(find_8860_sequence_folders(sample)), 2)
            items = collect_acam_injections(sample)
            self.assertEqual(len(items), 2)
            self.assertEqual(items[0][0], inj1)
            self.assertEqual(items[1][0], inj2)
            self.assertEqual(find_active_sample_folder_8860(data), sample)

    def test_flat_auto_sequence_is_sample(self):
        with tempfile.TemporaryDirectory() as data:
            seq = os.path.join(data, "20251221 sequence 2026-07-01 10-00-07")
            _touch_acam(os.path.join(seq, "F-2026-07-01-10-00-07-x.D"))
            self.assertEqual(find_active_sample_folder_8860(data), seq)
            self.assertIsNone(
                normalize_gc2_folder_sample_name(os.path.basename(seq))
            )


if __name__ == "__main__":
    unittest.main()
