# -*- coding: utf-8 -*-
"""
T72 — MOD lifecycle (status/close) + 파이프라인 E2E dry-run.

정적: ``summarize_mod_queue`` · ``transition_status`` 규칙
실행: ``mark_implemented`` JSON 갱신 · CLI · validate→apply→close 체인

실행:
  python -m unittest test_gc1_mod_lifecycle -v
  python scripts/status_gc1_mod.py
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
_SAMPLE_ATOM = "Ω.A.L4.P4.08"


from gc1_runtime.mod_apply import plan_from_json  # noqa: E402
from gc1_runtime.mod_lifecycle import (  # noqa: E402
    all_user_mods_resolved,
    load_mod_slots,
    mark_implemented,
    save_mod_slots,
    summarize_mod_queue,
    transition_status,
)
from gc1_runtime.mod_registry import ModSlot, validate_mod_registry  # noqa: E402


class TestModLifecycleStatic(unittest.TestCase):
    """정적 검증 — 집계·전이 규칙."""

    def test_default_queue_not_resolved(self):
        slots = load_mod_slots(DEFAULT_JSON)
        summary = summarize_mod_queue(slots)
        self.assertEqual(summary.total, 3)
        self.assertEqual(summary.awaiting_user, 3)
        self.assertFalse(all_user_mods_resolved(slots))

    def test_transition_pending_to_ready_ok(self):
        slot = ModSlot(
            mod_id="MOD-3",
            queue_task="T72",
            status="pending",
            title="",
            summary="",
        )
        r = transition_status(slot, "ready")
        self.assertTrue(r.ok)

    def test_transition_pending_to_implemented_fails(self):
        slot = ModSlot(
            mod_id="MOD-3",
            queue_task="T72",
            status="pending",
            title="",
            summary="",
        )
        r = transition_status(slot, "implemented")
        self.assertFalse(r.ok)


class TestModLifecycleExecution(unittest.TestCase):
    """실행 검증 — JSON 저장·CLI·파이프라인."""

    def _ready_mod3_json(self, tmp: str) -> str:
        path = os.path.join(tmp, "mod.json")
        data = {
            "version": 1,
            "slots": [
                {
                    "mod_id": "MOD-3",
                    "queue_task": "T72",
                    "status": "ready",
                    "title": "Lifecycle test",
                    "summary": "close after atom patch",
                    "leaf_ids": [_SAMPLE_ATOM],
                    "atom_ids": [_SAMPLE_ATOM],
                    "r_change": False,
                }
            ],
        }
        with open(path, "w", encoding="utf-8") as fh:
            json.dump(data, fh)
        return path

    def test_mark_implemented_updates_json(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = self._ready_mod3_json(tmp)
            result = mark_implemented("MOD-3", path)
            self.assertTrue(result.ok, msg=result.message)
            slots = load_mod_slots(path)
            self.assertEqual(slots[0].status, "implemented")
            self.assertTrue(all_user_mods_resolved(slots))

    def test_pipeline_validate_apply_close(self):
        """실행 E2E — registry validate → apply plan → close (synthetic MOD-3)."""
        with tempfile.TemporaryDirectory() as tmp:
            path = self._ready_mod3_json(tmp)
            slots = load_mod_slots(path)
            self.assertTrue(validate_mod_registry(slots).ok)
            plan = plan_from_json(path)
            self.assertTrue(plan.ok)
            self.assertEqual(len(plan.plans), 1)
            close = mark_implemented("MOD-3", path)
            self.assertTrue(close.ok)
            self.assertTrue(all_user_mods_resolved(load_mod_slots(path)))

    def test_status_cli_default(self):
        proc = subprocess.run(
            [sys.executable, os.path.join(REPO, "scripts", "status_gc1_mod.py")],
            cwd=REPO,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=30,
        )
        self.assertEqual(proc.returncode, 0)
        self.assertIn("MOD-3", proc.stdout)
        self.assertIn("WAIT", proc.stdout)

    def test_close_cli_requires_ready_content(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "empty.json")
            save_mod_slots(
                [
                    ModSlot(
                        mod_id="MOD-3",
                        queue_task="T72",
                        status="pending",
                        title="",
                        summary="",
                    )
                ],
                path,
            )
            proc = subprocess.run(
                [
                    sys.executable,
                    os.path.join(REPO, "scripts", "close_gc1_mod.py"),
                    "--mod",
                    "MOD-3",
                    "--json",
                    path,
                ],
                cwd=REPO,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=30,
            )
            self.assertEqual(proc.returncode, 1)


if __name__ == "__main__":
    unittest.main()
