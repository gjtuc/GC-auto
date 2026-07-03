# -*- coding: utf-8 -*-
"""
T82 — ``gc1_rt_validate`` RT 검증 (정적 repo sync + 실행 xlsx).

정적: ``verify_repo_rt_sync`` — gc_gc1 · data_pc GC1_TIME_* 일치
실행: synthetic xlsx → ``validate_rt_summaries`` PASS/FAIL

실행:
  python -m py_compile gc1_rt_validate.py test_gc1_rt_validate.py
  python -m unittest test_gc1_rt_validate -v
  python scripts/validate_gc1_rt.py --sync-check
"""
from __future__ import annotations

import os
import subprocess
import sys
import tempfile
import unittest

import pandas as pd

REPO = os.path.dirname(os.path.abspath(__file__))

import gc1_rt_validate as rt  # noqa: E402


def _write_gc1_xlsx(path: str, fid_rows: list, tcd_rows: list) -> None:
    """테스트용 GC1 KCH xlsx — FID/TCD 2시트."""
    with pd.ExcelWriter(path, engine="openpyxl") as writer:
        pd.DataFrame(fid_rows).to_excel(writer, sheet_name="FID", index=False)
        pd.DataFrame(tcd_rows).to_excel(writer, sheet_name="TCD", index=False)


class TestGc1RtValidateStatic(unittest.TestCase):
    """정적 검증 — repo TIME 구간 동기화."""

    def test_repo_rt_windows_in_sync(self):
        sync = rt.verify_repo_rt_sync()
        if not sync.ok:
            self.fail("repo RT mismatch:\n" + "\n".join(sync.mismatches))

    def test_gc1_rt_reference_matches_gc_gc1(self):
        for gas, center, half in (
            ("H2", 2.0, 0.35),
            ("CO", 6.6, 0.8),
            ("CO2", 16.2, 1.2),
        ):
            self.assertEqual(rt.GC1_RT_REFERENCE["TCD"][gas], (center, half))
        for gas, center, half in (
            ("CH4", 1.4, 0.35),
            ("C2H6", 1.9, 0.35),
            ("C2H4", 2.3, 0.35),
        ):
            self.assertEqual(rt.GC1_RT_REFERENCE["FID"][gas], (center, half))


class TestGc1RtValidateExecution(unittest.TestCase):
    """실행 검증 — synthetic xlsx RT PASS/FAIL."""

    def test_validate_pass_at_reference_centers(self):
        fid = [
            {"#": 1, "Time": 1.4, "Area": 100, "분석된 원소": "CH4"},
            {"#": 2, "Time": 1.9, "Area": 200, "분석된 원소": "C2H6"},
            {"#": 3, "Time": 2.3, "Area": 50, "분석된 원소": "C2H4"},
        ]
        tcd = [
            {"#": 1, "Time": 2.0, "Area": 300, "분석된 원소": "H2"},
            {"#": 2, "Time": 6.6, "Area": 80, "분석된 원소": "CO"},
            {"#": 3, "Time": 16.2, "Area": 120, "분석된 원소": "CO2"},
        ]
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "gc1_test.xlsx")
            _write_gc1_xlsx(path, fid, tcd)
            summaries = rt.extract_rt_summaries(path)
            result = rt.validate_rt_summaries(summaries, tolerance_min=0.1)
            self.assertTrue(result.ok, msg=[i.message for i in result.issues])
            self.assertGreaterEqual(len(summaries), 6)

    def test_validate_fail_when_rt_drifts(self):
        fid = [{"#": 1, "Time": 3.5, "Area": 100, "분석된 원소": "CH4"}]
        tcd = [{"#": 1, "Time": 2.0, "Area": 100, "분석된 원소": "H2"}]
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "gc1_drift.xlsx")
            _write_gc1_xlsx(path, fid, tcd)
            summaries = rt.extract_rt_summaries(path)
            result = rt.validate_rt_summaries(summaries, tolerance_min=0.1)
            self.assertFalse(result.ok)
            gases = {i.gas for i in result.issues}
            self.assertIn("CH4", gases)

    def test_cli_sync_check_subprocess(self):
        proc = subprocess.run(
            [sys.executable, os.path.join(REPO, "scripts", "validate_gc1_rt.py"), "--sync-check"],
            cwd=REPO,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=60,
        )
        self.assertEqual(proc.returncode, 0, msg=proc.stdout + proc.stderr)
        self.assertIn("in sync", proc.stdout)

    def test_cli_validate_synthetic_pass(self):
        fid = [{"#": 1, "Time": 1.9, "Area": 1, "분석된 원소": "C2H6"}]
        tcd = [{"#": 1, "Time": 2.0, "Area": 1, "분석된 원소": "H2"}]
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "one_peak.xlsx")
            _write_gc1_xlsx(path, fid, tcd)
            proc = subprocess.run(
                [
                    sys.executable,
                    os.path.join(REPO, "scripts", "validate_gc1_rt.py"),
                    path,
                ],
                cwd=REPO,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=60,
            )
            self.assertEqual(proc.returncode, 0, msg=proc.stderr + proc.stdout)
            self.assertIn("PASS", proc.stdout)


if __name__ == "__main__":
    unittest.main()
