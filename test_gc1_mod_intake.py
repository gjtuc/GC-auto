# -*- coding: utf-8 -*-
"""
T86 — MOD intake CLI 검증.

정적: ``parse_leaf_list`` · ``apply_intake_to_slots``
실행: temp JSON intake → validate → plan

실행:
  python -m unittest test_gc1_mod_intake -v
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import unittest

REPO = os.path.dirname(os.path.abspath(__file__))
_SAMPLE_ATOM = "Ω.A.L4.P3.06"


from gc1_runtime.mod_intake import (  # noqa: E402
    ModIntakeRequest,
    apply_intake_to_slots,
    intake_mod_slot,
    parse_leaf_list,
)
from gc1_runtime.mod_registry import load_mod_slots  # noqa: E402


def _base_slots_json() -> dict:
    with open(os.path.join(REPO, "deploy", "gc1_mod_slots.json"), encoding="utf-8") as fh:
        return json.load(fh)


class TestModIntakeStatic(unittest.TestCase):
    def test_parse_leaf_comma_and_repeat(self):
        ids = parse_leaf_list(["Ω.A.L4.P3.06,Ω.A.L4.P4.08", "Ω.A.L4.P1.01"])
        self.assertEqual(len(ids), 3)

    def test_apply_intake_updates_slot(self):
        slots = load_mod_slots(os.path.join(REPO, "deploy", "gc1_mod_slots.json"))
        req = ModIntakeRequest(
            mod_id="MOD-1",
            title="t",
            summary="s",
            leaf_ids=[_SAMPLE_ATOM],
            atom_ids=[_SAMPLE_ATOM],
        )
        apply_intake_to_slots(slots, req)
        mod1 = next(s for s in slots if s.mod_id == "MOD-1")
        self.assertEqual(mod1.title, "t")
        self.assertEqual(mod1.leaf_ids, [_SAMPLE_ATOM])


class TestModIntakeExecution(unittest.TestCase):
    def test_intake_writes_and_plans(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "mod.json")
            with open(path, "w", encoding="utf-8") as fh:
                json.dump(_base_slots_json(), fh)
            req = ModIntakeRequest(
                mod_id="MOD-1",
                title="Peak verify",
                summary="P3.06 stricter",
                leaf_ids=[_SAMPLE_ATOM],
                atom_ids=[_SAMPLE_ATOM],
                status="ready",
            )
            result = intake_mod_slot(req, path)
            self.assertTrue(result.ok, msg=result.validation_errors)
            self.assertEqual(result.plan_atom_count, 1)
            slots = load_mod_slots(path)
            mod1 = next(s for s in slots if s.mod_id == "MOD-1")
            self.assertEqual(mod1.status, "ready")

    def test_intake_cli_subprocess(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "mod.json")
            with open(path, "w", encoding="utf-8") as fh:
                json.dump(_base_slots_json(), fh)
            proc = subprocess.run(
                [
                    sys.executable,
                    os.path.join(REPO, "scripts", "intake_gc1_mod.py"),
                    "--mod",
                    "MOD-2",
                    "--title",
                    "CLI intake",
                    "--summary",
                    "test",
                    "--leaf",
                    "Ω.A.L4.P4.08",
                    "--atom",
                    "Ω.A.L4.P4.08",
                    "--json",
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
            self.assertIn("[OK]", proc.stdout)
            slots = load_mod_slots(path)
            mod2 = next(s for s in slots if s.mod_id == "MOD-2")
            self.assertEqual(mod2.status, "ready")
            self.assertIn("P4.08", mod2.atom_ids[0])


if __name__ == "__main__":
    unittest.main()
