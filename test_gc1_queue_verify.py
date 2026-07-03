# -*- coding: utf-8 -*-
"""
T85 — ``run_gc1_queue_verify.py`` 메타 검증.

정적: 스크립트 존재·py_compile
실행: ``--quick`` 모드 subprocess (전체는 CI·수동)
"""
from __future__ import annotations

import os
import subprocess
import sys
import unittest

REPO = os.path.dirname(os.path.abspath(__file__))
VERIFY_SCRIPT = os.path.join(REPO, "scripts", "run_gc1_queue_verify.py")


class TestQueueVerifyScript(unittest.TestCase):
    def test_script_exists(self):
        self.assertTrue(os.path.isfile(VERIFY_SCRIPT))

    def test_quick_mode_exit_zero(self):
        proc = subprocess.run(
            [sys.executable, VERIFY_SCRIPT, "--quick"],
            cwd=REPO,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=180,
        )
        self.assertEqual(proc.returncode, 0, msg=proc.stdout[-2000:] + proc.stderr[-1000:])
        self.assertIn("PASS", proc.stdout)


if __name__ == "__main__":
    unittest.main()
