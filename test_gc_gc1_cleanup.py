# -*- coding: utf-8 -*-
"""
T60 — cleanup_superseded_gc1_files CL.j.05 verbatim PDF 오판 재현·수정 검증.

실행: python -m unittest test_gc_gc1_cleanup -v
"""
from __future__ import annotations

import os
import tempfile
import unittest
from unittest import mock

from gc_gc1 import (
    Gc1PdfReport,
    _experiment_group_key,
    cleanup_superseded_gc1_files,
)


def _fake_report(pdf_path: str, *, n_cycles: int, area_offset: float = 0.0) -> Gc1PdfReport:
    """주입 수·area_offset 으로 서로 다른 실험 fingerprint 시뮬레이션."""
    fid = [[{"name": "CH4", "Area": float(i + 1) + area_offset}] for i in range(n_cycles)]
    tcd = [[{"name": "H2", "Area": 100.0 + area_offset + i}] for i in range(n_cycles)]
    return Gc1PdfReport(
        pdf_path=pdf_path,
        fid_cycles=fid,
        tcd_cycles=tcd,
        analysis_date="20260629",
        default_sample_name="dre",
        total_injections=n_cycles,
    )


class TestExperimentGroupKey(unittest.TestCase):
    def test_yyyymmdd_stems_do_not_share_six_digit_prefix(self):
        """CL.05 버그 — 6자리만 쓰면 서로 다른 실험이 한 그룹이 됨."""
        new_stem = "20260629 dre(3) ni-ce-la"
        old_stem = "202606 24dre(5)-ni(부스터)"
        self.assertNotEqual(_experiment_group_key(new_stem), _experiment_group_key(old_stem))
        self.assertEqual(_experiment_group_key(new_stem), "20260629")
        self.assertEqual(_experiment_group_key(old_stem), "20260624")


class TestCleanupSupersededGc1Files(unittest.TestCase):
    def setUp(self) -> None:
        self._tmpdir = tempfile.TemporaryDirectory()
        self.folder = self._tmpdir.name

    def tearDown(self) -> None:
        self._tmpdir.cleanup()

    def _touch_pdf(self, name: str) -> str:
        path = os.path.join(self.folder, name)
        with open(path, "wb") as fh:
            fh.write(b"%PDF-1.4 minimal")
        return path

    def test_verbatim_kept_not_deleted_when_old_has_more_cycles(self):
        """
        force export 재현 — 새 ``20260629 dre(3) ni-ce-la.pdf`` 가
        옛 ``202606 24dre(5)-ni(부스터).pdf`` (주입 많음) 때문에 삭제되면 안 됨.
        """
        kept = self._touch_pdf("20260629 dre(3) ni-ce-la.pdf")
        old = self._touch_pdf("202606 24dre(5)-ni(부스터).pdf")

        reports = {
            os.path.normpath(kept): _fake_report(kept, n_cycles=2, area_offset=0.0),
            os.path.normpath(old): _fake_report(old, n_cycles=196, area_offset=5000.0),
        }

        with mock.patch("gc_gc1._try_parse_gc1_pdf_quiet", side_effect=lambda p: reports.get(os.path.normpath(p))):
            removed, surviving = cleanup_superseded_gc1_files(self.folder, kept, log_fn=lambda _m: None)

        self.assertTrue(os.path.isfile(kept), "verbatim export PDF must survive")
        self.assertEqual(os.path.normpath(surviving), os.path.normpath(kept))
        self.assertEqual(removed, 0)
        self.assertTrue(os.path.isfile(old), "unrelated old PDF must not be deleted without fingerprint match")

    def test_truncated_stem_still_removed(self):
        """잘린 파일명은 verbatim kept 가 있을 때 삭제."""
        kept = self._touch_pdf("20260629 dre(3) ni-ce-la.pdf")
        truncated = self._touch_pdf("20260629 dre(3) ni.pdf")
        reports = {
            os.path.normpath(kept): _fake_report(kept, n_cycles=5),
            os.path.normpath(truncated): _fake_report(truncated, n_cycles=5),
        }
        with mock.patch("gc_gc1._try_parse_gc1_pdf_quiet", side_effect=lambda p: reports.get(os.path.normpath(p))):
            removed, surviving = cleanup_superseded_gc1_files(self.folder, kept, log_fn=lambda _m: None)

        self.assertTrue(os.path.isfile(kept))
        self.assertFalse(os.path.isfile(truncated))
        self.assertGreaterEqual(removed, 1)
        self.assertEqual(os.path.normpath(surviving), os.path.normpath(kept))

    def test_fingerprint_duplicate_drops_fewer_cycles_not_kept(self):
        """동일 fingerprint — kept 가 아닌 쪽 중 주입 적은 PDF 만 삭제."""
        kept = self._touch_pdf("20260629 dre(3) ni-ce-la.pdf")
        dup = self._touch_pdf("20260629 dre(3) ni-ce-la-old.pdf")
        # prefix 일치 fingerprint — 2 vs 5 주입
        rep_kept = _fake_report(kept, n_cycles=2)
        rep_dup = _fake_report(dup, n_cycles=5)
        # dup 의 앞 2주입을 kept 와 동일 area 로 맞춤
        for i in range(2):
            rep_dup.fid_cycles[i] = list(rep_kept.fid_cycles[i])
            rep_dup.tcd_cycles[i] = list(rep_kept.tcd_cycles[i])

        reports = {
            os.path.normpath(kept): rep_kept,
            os.path.normpath(dup): rep_dup,
        }
        with mock.patch("gc_gc1._try_parse_gc1_pdf_quiet", side_effect=lambda p: reports.get(os.path.normpath(p))):
            removed, surviving = cleanup_superseded_gc1_files(self.folder, kept, log_fn=lambda _m: None)

        self.assertTrue(os.path.isfile(kept))
        self.assertEqual(os.path.normpath(surviving), os.path.normpath(kept))
        self.assertFalse(os.path.isfile(dup), "duplicate with more cycles must not replace verbatim kept")


if __name__ == "__main__":
    unittest.main()
