# -*- coding: utf-8 -*-
"""
T84 — GC2 회귀 스크립트 ``run_gc2_regression.ps1`` dry-run 주석·플래그 검증.

정적 검증: PS1 파일에 dry-run tier 표·``-DryRunOnly`` 파라미터·STEP9 교차 참조 존재
실행 검증: ``-DryRunOnly`` 로 9.8 force 미호출·스크립트 정상 종료(비 GC2 PC 에서도)

실행:
  python -m py_compile test_gc2_regression_script.py
  python -m unittest test_gc2_regression_script -v
"""
from __future__ import annotations

import os
import subprocess
import sys
import unittest

REPO = os.path.dirname(os.path.abspath(__file__))
PS1_PATH = os.path.join(REPO, "scripts", "run_gc2_regression.ps1")

# 정적 검증 — 주석·문서 회귀 마커 (T84 의도)
_STATIC_MARKERS = (
    "dry-run 구분",
    "9.8",
    "--force --no-email",
    "DryRunOnly",
    "SkipForce",
    "STEP9",
    "ChemStation",
    "AUTOCHRO_DRY_RUN",
    "9.6",
    "9.7",
)


class TestGc2RegressionScriptStatic(unittest.TestCase):
    """정적 검증 — PS1 텍스트·파라미터 블록 (실행과 별개)."""

    @classmethod
    def setUpClass(cls) -> None:
        with open(PS1_PATH, encoding="utf-8") as fh:
            cls.ps1_text = fh.read()

    def test_file_exists(self):
        self.assertTrue(os.path.isfile(PS1_PATH))

    def test_dry_run_comment_markers(self):
        for marker in _STATIC_MARKERS:
            self.assertIn(marker, self.ps1_text, msg=f"missing marker: {marker!r}")

    def test_dry_run_only_param_declared(self):
        self.assertRegex(self.ps1_text, r"\[switch\]\$DryRunOnly")

    def test_skip_pipeline_logic(self):
        self.assertIn("$skipPipeline = $DryRunOnly -or $SkipForce", self.ps1_text)

    def test_step98_inside_skip_pipeline_guard(self):
        """``--force --no-email`` 는 ``if (-not $skipPipeline)`` 블록 안에만 있어야 함."""
        text = self.ps1_text
        guard_idx = text.find("if (-not $skipPipeline)")
        force_idx = text.find("python gc_automation.py --force --no-email")
        self.assertGreater(guard_idx, -1)
        self.assertGreater(force_idx, guard_idx)


class TestGc2RegressionScriptExecution(unittest.TestCase):
    """실행 검증 — PowerShell ``-DryRunOnly`` (GC2 장비 PC 아니어도 스크립트 완료)."""

    def _run_ps1(self, *extra_args: str) -> subprocess.CompletedProcess[str]:
        cmd = [
            "powershell",
            "-NoProfile",
            "-ExecutionPolicy",
            "Bypass",
            "-File",
            PS1_PATH,
            *extra_args,
        ]
        return subprocess.run(
            cmd,
            cwd=REPO,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=120,
        )

    def test_dry_run_only_skips_step98_banner(self):
        proc = self._run_ps1("-DryRunOnly")
        combined = proc.stdout + proc.stderr
        self.assertIn("DryRunOnly", combined)
        self.assertIn("SKIPPED", combined)
        self.assertIn("9.8", combined)
        # 9.8 실행 배너(needs hotspot)는 DryRunOnly 에서 없어야 함
        self.assertNotIn("needs hotspot + ChemStation acam", combined)

    def test_dry_run_only_does_not_crash(self):
        proc = self._run_ps1("-DryRunOnly")
        # GC1 PC 에서는 verify 실패로 exit 1 가능 — 크래시(비정상 종료) 아님
        self.assertIn(proc.returncode, (0, 1), msg=proc.stderr[:500])

    def test_full_mode_invokes_step98_section(self):
        """``-SkipForce`` 없이 실행 시 9.8 섹션 헤더 출력 (실패해도 호출됨)."""
        proc = self._run_ps1()
        combined = proc.stdout + proc.stderr
        self.assertIn("Step 9.8", combined)
        self.assertIn("--force --no-email", combined)


if __name__ == "__main__":
    unittest.main()
