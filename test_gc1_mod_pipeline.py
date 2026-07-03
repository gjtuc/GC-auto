# -*- coding: utf-8 -*-
"""
T87 — ``run_gc1_mod_pipeline.py`` 검증.

정적: ``run_mod_pipeline`` step 구조
실행: default JSON + ready MOD temp JSON + CLI subprocess

실행:
  python -m unittest test_gc1_mod_pipeline -v
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import unittest

REPO = os.path.dirname(os.path.abspath(__file__))
DEFAULT_JSON = os.path.join(REPO, "deploy", "gc1_mod_slots.json")
_SAMPLE_ATOM = "Ω.A.L4.P3.06"


from gc1_runtime.mod_pipeline import run_mod_pipeline  # noqa: E402


def _base_slots() -> dict:
    with open(DEFAULT_JSON, encoding="utf-8") as fh:
        return json.load(fh)


class TestModPipelineStatic(unittest.TestCase):
    def test_default_report_ok_no_ready(self):
        report = run_mod_pipeline(DEFAULT_JSON)
        self.assertTrue(report.ok)
        self.assertEqual(len(report.ready_mod_ids), 0)
        self.assertGreaterEqual(len(report.pending_mod_ids), 1)
        names = [s.name for s in report.steps]
        self.assertIn("validate_registry", names)
        self.assertIn("apply_plan_dry_run", names)


class TestModPipelineExecution(unittest.TestCase):
    def test_ready_mod_produces_plan(self):
        data = _base_slots()
        for slot in data["slots"]:
            if slot["mod_id"] == "MOD-1":
                slot.update(
                    {
                        "status": "ready",
                        "title": "pipe test",
                        "summary": "pipeline",
                        "leaf_ids": [_SAMPLE_ATOM],
                        "atom_ids": [_SAMPLE_ATOM],
                    }
                )
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "mod.json")
            with open(path, "w", encoding="utf-8") as fh:
                json.dump(data, fh)
            report = run_mod_pipeline(path)
            self.assertTrue(report.ok)
            self.assertIn("MOD-1", report.ready_mod_ids)
            self.assertIsNotNone(report.apply)
            assert report.apply is not None
            self.assertEqual(len(report.apply.plans), 1)

    def test_cli_subprocess_default(self):
        proc = subprocess.run(
            [sys.executable, os.path.join(REPO, "scripts", "run_gc1_mod_pipeline.py")],
            cwd=REPO,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=60,
        )
        self.assertEqual(proc.returncode, 0, msg=proc.stderr + proc.stdout)
        self.assertIn("PASS", proc.stdout)
        self.assertIn("intake_gc1_mod", proc.stdout)


if __name__ == "__main__":
    unittest.main()
