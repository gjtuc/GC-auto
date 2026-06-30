# -*- coding: utf-8 -*-
"""
T97 — ``layer0_live_e2e`` Step 8.3 live 계획 + ``run_gc1_step8_live`` CLI.

실행:
  python -m unittest test_gc1_live_e2e -v
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import unittest

from gc1_runtime.layer0_live_e2e import (
    Step83Mode,
    build_live_e2e_env,
    build_live_e2e_plan,
    contrast_with_83d,
    evaluate_live_preflight,
)


class TestLiveE2eStatic(unittest.TestCase):
    def test_build_env_live_not_dry(self):
        env = build_live_e2e_env(use_runtime=True, dry_run=False)
        self.assertEqual(env["AUTOCHRO_DRY_RUN"], "0")
        self.assertEqual(env["GC1_USE_RUNTIME"], "1")

    def test_build_env_legacy(self):
        env = build_live_e2e_env(use_runtime=False, dry_run=False)
        self.assertEqual(env["GC1_USE_RUNTIME"], "0")

    def test_plan_excel_argv(self):
        repo = os.path.dirname(os.path.abspath(__file__))
        plan = build_live_e2e_plan(repo, Step83Mode.EXCEL_ONLY)
        self.assertEqual(plan.step_ref, "8.3a")
        self.assertIn("--no-email", plan.argv)
        self.assertIn("--force", plan.argv)
        self.assertFalse(plan.requires_hotspot)

    def test_plan_mail_argv(self):
        repo = os.path.dirname(os.path.abspath(__file__))
        plan = build_live_e2e_plan(repo, Step83Mode.MAIL)
        self.assertEqual(plan.step_ref, "8.3b")
        self.assertNotIn("--no-email", plan.argv)
        self.assertTrue(plan.requires_hotspot)

    def test_contrast_83d(self):
        repo = os.path.dirname(os.path.abspath(__file__))
        plan = build_live_e2e_plan(repo, Step83Mode.MAIL)
        c = contrast_with_83d(plan)
        self.assertEqual(c["this_autochro_dry_run"], "0")
        self.assertIn("8.3d", c["dry_run_step"])

    def test_preflight_ok_gc1_ident(self):
        ident = {
            "repo_root_exists": True,
            "is_not_data_pc": True,
            "is_gc1_instance": True,
            "is_gc1_mode": True,
            "ok_for_gc1_autochro": True,
            "gc1_env_exists": True,
        }
        repo = os.path.dirname(os.path.abspath(__file__))
        plan = build_live_e2e_plan(repo, Step83Mode.EXCEL_ONLY)
        pre = evaluate_live_preflight(ident, plan)
        self.assertTrue(pre.ok, msg=pre.errors)

    def test_preflight_fail_data_pc(self):
        ident = {
            "repo_root_exists": True,
            "is_not_data_pc": False,
            "is_gc1_instance": False,
            "is_gc1_mode": False,
            "ok_for_gc1_autochro": False,
        }
        repo = os.path.dirname(os.path.abspath(__file__))
        plan = build_live_e2e_plan(repo, Step83Mode.EXCEL_ONLY)
        pre = evaluate_live_preflight(ident, plan)
        self.assertFalse(pre.ok)


class TestLiveE2eExecution(unittest.TestCase):
    def test_cli_preflight(self):
        repo = os.path.dirname(os.path.abspath(__file__))
        script = os.path.join(repo, "scripts", "run_gc1_step8_live.py")
        proc = subprocess.run(
            [sys.executable, script, "--preflight", "--mode", "excel"],
            cwd=repo,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=60,
        )
        self.assertIn(proc.returncode, (0, 2), msg=proc.stderr or proc.stdout)
        data = json.loads(proc.stdout)
        self.assertIn("plan", data)
        self.assertEqual(data["plan"]["mode"], "8.3a")
        self.assertEqual(data["plan"]["env"]["AUTOCHRO_DRY_RUN"], "0")

    def test_cli_plan_no_run(self):
        repo = os.path.dirname(os.path.abspath(__file__))
        script = os.path.join(repo, "scripts", "run_gc1_step8_live.py")
        proc = subprocess.run(
            [sys.executable, script, "--plan", "--mode", "mail"],
            cwd=repo,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=60,
        )
        self.assertEqual(proc.returncode, 0, msg=proc.stderr or proc.stdout)
        data = json.loads(proc.stdout)
        self.assertEqual(data["contrast_83d"]["this_autochro_dry_run"], "0")


if __name__ == "__main__":
    unittest.main()
