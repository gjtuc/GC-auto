# -*- coding: utf-8 -*-
"""
T71 — MOD apply plan (dry-run) 검증.

정적: ``resolve_target_atom_ids`` · ``verify_atoms_in_registry``
실행: filled MOD JSON · CLI ``apply_gc1_mod.py --dry-run``

실행:
  python -m unittest test_gc1_mod_apply -v
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

from gc1_runtime.mod_apply import (  # noqa: E402
    build_plan,
    load_known_atom_ids,
    plan_from_json,
    plan_ready_mods,
    resolve_target_atom_ids,
)
from gc1_runtime.mod_registry import ModSlot, load_mod_slots  # noqa: E402

# 실제 런타임에 존재하는 atom (T62 eye gate)
_SAMPLE_ATOM = "Ω.A.L4.P4.08"


class TestModApplyStatic(unittest.TestCase):
    """정적 검증 — atom ID 해석·레지스트리."""

    def test_sample_atom_in_registry(self):
        known = load_known_atom_ids()
        self.assertIn(_SAMPLE_ATOM, known)

    def test_resolve_from_leaf_ids(self):
        slot = ModSlot(
            mod_id="MOD-2",
            queue_task="T71",
            status="ready",
            title="t",
            summary="s",
            leaf_ids=[f"{_SAMPLE_ATOM}.W32.click"],
        )
        ids = resolve_target_atom_ids(slot)
        self.assertEqual(ids, [_SAMPLE_ATOM])

    def test_build_plan_ok(self):
        slot = ModSlot(
            mod_id="MOD-2",
            queue_task="T71",
            status="ready",
            title="Peak verify",
            summary="Stricter P4 post gate",
            atom_ids=[_SAMPLE_ATOM],
            leaf_ids=[_SAMPLE_ATOM],
        )
        plan, errors = build_plan(slot, load_known_atom_ids())
        self.assertEqual(errors, [])
        self.assertIsNotNone(plan)
        assert plan is not None
        self.assertEqual(plan.phases, ["P4"])


class TestModApplyExecution(unittest.TestCase):
    """실행 검증 — JSON·CLI."""

    def test_default_json_no_ready_plans(self):
        result = plan_from_json(DEFAULT_JSON)
        self.assertTrue(result.ok)
        self.assertEqual(len(result.plans), 0)
        self.assertGreaterEqual(result.skipped_pending, 1)

    def test_ready_mod_in_temp_json(self):
        data = {
            "version": 1,
            "slots": [
                {
                    "mod_id": "MOD-2",
                    "queue_task": "T71",
                    "status": "ready",
                    "title": "Test MOD-2",
                    "summary": "Dry-run plan only",
                    "leaf_ids": [_SAMPLE_ATOM],
                    "atom_ids": [_SAMPLE_ATOM],
                    "r_change": False,
                }
            ],
        }
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "mod.json")
            with open(path, "w", encoding="utf-8") as fh:
                json.dump(data, fh)
            slots = load_mod_slots(path)
            result = plan_ready_mods(slots, load_known_atom_ids())
            self.assertTrue(result.ok)
            self.assertEqual(len(result.plans), 1)
            self.assertEqual(result.plans[0].mod_id, "MOD-2")

    def test_unknown_atom_fails(self):
        slot = ModSlot(
            mod_id="MOD-2",
            queue_task="T71",
            status="ready",
            title="x",
            summary="y",
            atom_ids=["Ω.A.L4.P99.99"],
        )
        _, errors = build_plan(slot, load_known_atom_ids())
        self.assertTrue(errors)

    def test_cli_dry_run_default_json(self):
        proc = subprocess.run(
            [
                sys.executable,
                os.path.join(REPO, "scripts", "apply_gc1_mod.py"),
                "--dry-run",
            ],
            cwd=REPO,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=30,
        )
        self.assertEqual(proc.returncode, 0, msg=proc.stderr + proc.stdout)
        self.assertIn("no ready MOD plans", proc.stdout)

    def test_cli_ready_mod_plan(self):
        data = {
            "version": 1,
            "slots": [
                {
                    "mod_id": "MOD-2",
                    "queue_task": "T71",
                    "status": "ready",
                    "title": "CLI test",
                    "summary": "plan output",
                    "leaf_ids": [_SAMPLE_ATOM],
                    "atom_ids": [_SAMPLE_ATOM],
                    "r_change": False,
                }
            ],
        }
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "mod.json")
            with open(path, "w", encoding="utf-8") as fh:
                json.dump(data, fh)
            proc = subprocess.run(
                [
                    sys.executable,
                    os.path.join(REPO, "scripts", "apply_gc1_mod.py"),
                    "--dry-run",
                    "--json",
                    path,
                    "--mod",
                    "MOD-2",
                ],
                cwd=REPO,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=30,
            )
            self.assertEqual(proc.returncode, 0, msg=proc.stderr + proc.stdout)
            self.assertIn("[PLAN] MOD-2", proc.stdout)
            self.assertIn("P4.08", proc.stdout)
            self.assertIn("phases:  P4", proc.stdout)


if __name__ == "__main__":
    unittest.main()
