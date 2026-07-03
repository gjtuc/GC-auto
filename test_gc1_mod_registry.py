# -*- coding: utf-8 -*-
"""
T70 — MOD 슬롯 registry 검증 (기초 인프라).

정적: JSON 스키마·ID 정규식·validate_mod_registry
실행: CLI·ready/pending 판별·filled slot 시뮬레이션

실행:
  python -m unittest test_gc1_mod_registry -v
  python scripts/validate_gc1_mod_slots.py
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

from gc1_runtime.mod_registry import (  # noqa: E402
    ModSlot,
    load_mod_slots,
    pending_slots,
    ready_for_impl,
    validate_mod_registry,
)


class TestModRegistryStatic(unittest.TestCase):
    """정적 검증 — deploy JSON·스키마."""

    def test_default_json_loads(self):
        slots = load_mod_slots(DEFAULT_JSON)
        self.assertEqual(len(slots), 3)
        self.assertEqual(slots[0].mod_id, "MOD-1")

    def test_validate_default_registry_ok(self):
        slots = load_mod_slots(DEFAULT_JSON)
        result = validate_mod_registry(slots)
        self.assertTrue(result.ok, msg=result.errors)

    def test_all_slots_pending_awaiting_user(self):
        slots = load_mod_slots(DEFAULT_JSON)
        self.assertEqual(len(pending_slots(slots)), 3)
        self.assertEqual(len(ready_for_impl(slots)), 0)


class TestModRegistryExecution(unittest.TestCase):
    """실행 검증 — ready 슬롯·CLI."""

    def test_ready_slot_when_filled(self):
        slot = ModSlot(
            mod_id="MOD-1",
            queue_task="T70",
            status="ready",
            title="Test mod",
            summary="Change P4 verify gate",
            leaf_ids=["Ω.A.L4.P4.08"],
            atom_ids=["Ω.A.L4.P4.08"],
        )
        result = validate_mod_registry([slot])
        self.assertTrue(result.ok)
        self.assertTrue(slot.is_ready_for_impl)

    def test_invalid_leaf_id_fails(self):
        slot = ModSlot(
            mod_id="MOD-1",
            queue_task="T70",
            status="ready",
            title="x",
            summary="y",
            leaf_ids=["BAD-ID"],
        )
        result = validate_mod_registry([slot])
        self.assertFalse(result.ok)

    def test_cli_subprocess(self):
        proc = subprocess.run(
            [sys.executable, os.path.join(REPO, "scripts", "validate_gc1_mod_slots.py")],
            cwd=REPO,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=30,
        )
        self.assertEqual(proc.returncode, 0, msg=proc.stderr + proc.stdout)
        self.assertIn("MOD-1", proc.stdout)
        self.assertIn("[OK]", proc.stdout)

    def test_temp_json_roundtrip(self):
        """실행 검증 — 임시 JSON write/load/validate."""
        data = {
            "version": 1,
            "slots": [
                {
                    "mod_id": "MOD-9",
                    "queue_task": "T99",
                    "status": "pending",
                    "title": "",
                    "summary": "",
                    "leaf_ids": [],
                    "atom_ids": [],
                    "r_change": False,
                }
            ],
        }
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "mod.json")
            with open(path, "w", encoding="utf-8") as fh:
                json.dump(data, fh)
            slots = load_mod_slots(path)
            self.assertTrue(validate_mod_registry(slots).ok)


if __name__ == "__main__":
    unittest.main()
