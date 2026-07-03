# -*- coding: utf-8 -*-
"""GC1 reaction gate 단위 테스트 — python -m unittest test_gc1_reaction_gate"""
from __future__ import annotations

import unittest

from gc1_reaction_gate import (
    Gc1ReactionAvailability,
    build_trim_empty_fail_reason,
    classify_gc1_report,
)
from gc_gc1 import Gc1PdfReport, trim_reduction_and_first_reaction


def _tcd(*, h2=None, co=None):
    rows = []
    if h2 is not None:
        rows.append({"name": "H2", "Area": h2})
    if co is not None:
        rows.append({"name": "CO", "Area": co})
    return rows


def _report_from_trim(fid, tcd, *, total=None):
    kept_fid, kept_tcd, skipped_pre, skipped_red, skipped_trans, skipped_first, _ = (
        trim_reduction_and_first_reaction(fid, tcd, quiet=True)
    )
    inj = total if total is not None else max(len(fid), len(tcd))
    return Gc1PdfReport(
        pdf_path="synthetic.pdf",
        fid_cycles=kept_fid,
        tcd_cycles=kept_tcd,
        analysis_date="20260629",
        default_sample_name="TEST",
        total_injections=inj,
        skipped_pre_reduction_count=skipped_pre,
        skipped_reduction_count=skipped_red,
        skipped_transition_count=skipped_trans,
        skipped_first_reaction_count=skipped_first,
    )


class TestGc1ReactionGate(unittest.TestCase):
    def test_has_reaction_data_after_trim(self):
        fid = [[], [], [], [{"name": "CH4", "Area": 1.0}], [{"name": "CH4", "Area": 2.0}]]
        tcd = [
            _tcd(h2=50, co=10),
            _tcd(h2=20000, co=10),
            _tcd(h2=500, co=50),
            _tcd(h2=1000, co=500),
            _tcd(h2=1200, co=600),
        ]
        gate = classify_gc1_report(_report_from_trim(fid, tcd))
        self.assertEqual(gate.availability, Gc1ReactionAvailability.HAS_REACTION_DATA)
        self.assertTrue(gate.can_write_excel)
        self.assertIsNone(gate.fail_reason)
        self.assertEqual(gate.kept_injections, 2)

    def test_reduction_stage_no_reaction_yet(self):
        """환원만 있고 반응 시작 전 - 현재 환원 단계 시나리오."""
        fid = [[], []]
        tcd = [_tcd(h2=20000, co=10), _tcd(h2=500, co=50)]
        gate = classify_gc1_report(_report_from_trim(fid, tcd))
        self.assertEqual(gate.availability, Gc1ReactionAvailability.REDUCTION_STAGE)
        self.assertFalse(gate.can_write_excel)
        self.assertIn("남은 데이터 없음", gate.fail_reason or "")
        self.assertGreater(gate.skipped_reduction_count, 0)
        self.assertEqual(gate.kept_injections, 0)

    def test_no_peaks_empty_pdf(self):
        report = Gc1PdfReport(
            pdf_path="empty.pdf",
            fid_cycles=[],
            tcd_cycles=[],
            analysis_date="20260629",
            default_sample_name="",
            total_injections=0,
        )
        gate = classify_gc1_report(report)
        self.assertEqual(gate.availability, Gc1ReactionAvailability.NO_PEAKS)
        self.assertEqual(build_trim_empty_fail_reason(report), "PDF 에서 FID/TCD 피크를 찾지 못함")

    def test_trim_empty_without_reduction_marker(self):
        """환원 H2 마커 없이 사전노이즈만 - reduction_stage 가 아님."""
        fid = [[], []]
        tcd = [_tcd(h2=50, co=10), _tcd(h2=80, co=12)]
        gate = classify_gc1_report(_report_from_trim(fid, tcd))
        self.assertEqual(gate.availability, Gc1ReactionAvailability.TRIM_EMPTY)
        self.assertFalse(gate.can_write_excel)


if __name__ == "__main__":
    unittest.main()
