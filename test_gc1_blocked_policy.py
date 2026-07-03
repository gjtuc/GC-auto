# -*- coding: utf-8 -*-
"""
T96 — ``layer0_blocked`` PART6 BLOCKED + agent_queue_state 실행 검증.

실행:
  python -m unittest test_gc1_blocked_policy -v
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import unittest

from gc1_runtime.layer0_blocked import (
    DEFAULT_BLOCKED_POLICY_PATH,
    apply_agent_queue_blocked,
    build_agent_queue_blocked_patch,
    infer_blocked_code_from_text,
    is_hook_followup_suppressed,
    load_blocked_policy,
    merge_agent_queue_state,
    read_agent_queue_state,
    validate_blocked_policy,
)


class TestBlockedPolicyStatic(unittest.TestCase):
    def test_load_default_policy(self):
        doc = load_blocked_policy(DEFAULT_BLOCKED_POLICY_PATH)
        self.assertEqual(len(doc.rules), 4)
        codes = {r.code for r in doc.rules}
        self.assertIn("autochro_live_ui", codes)
        self.assertIn("origin_gui", codes)

    def test_validate_default(self):
        doc = load_blocked_policy(DEFAULT_BLOCKED_POLICY_PATH)
        result = validate_blocked_policy(doc)
        self.assertTrue(result.ok, msg=result.errors)

    def test_build_patch_fields(self):
        doc = load_blocked_policy(DEFAULT_BLOCKED_POLICY_PATH)
        rule = doc.rules[0]
        patch = build_agent_queue_blocked_patch(rule, last_task="T96")
        self.assertEqual(patch["status"], "blocked")
        self.assertFalse(patch["request_quit_cursor"])
        self.assertEqual(patch["blocked_code"], rule.code)
        self.assertEqual(patch["last_task"], "T96")

    def test_infer_from_text(self):
        self.assertEqual(infer_blocked_code_from_text("need Autochro window"), "autochro_live_ui")
        self.assertEqual(infer_blocked_code_from_text("originpro COM failed"), "origin_gui")
        self.assertIsNone(infer_blocked_code_from_text(""))

    def test_hook_suppressed_when_blocked(self):
        self.assertTrue(is_hook_followup_suppressed({"status": "blocked"}))
        self.assertFalse(is_hook_followup_suppressed({"status": "running"}))


class TestBlockedPolicyExecution(unittest.TestCase):
    def test_apply_dry_run(self):
        with tempfile.TemporaryDirectory() as tmp:
            state_path = os.path.join(tmp, "agent_queue_state.json")
            policy_path = DEFAULT_BLOCKED_POLICY_PATH
            result = apply_agent_queue_blocked(
                "gdrive_secuyou",
                policy_path=policy_path,
                state_path=state_path,
                last_task="T96",
                dry_run=True,
            )
            self.assertTrue(result.ok)
            self.assertEqual(result.state["status"], "blocked")
            self.assertFalse(os.path.isfile(state_path))

    def test_apply_writes_state(self):
        with tempfile.TemporaryDirectory() as tmp:
            state_path = os.path.join(tmp, "agent_queue_state.json")
            with open(state_path, "w", encoding="utf-8") as fh:
                json.dump({"armed": True, "status": "running"}, fh)
            result = apply_agent_queue_blocked(
                "autochro_live_ui",
                state_path=state_path,
                last_task="T96",
            )
            self.assertTrue(result.ok)
            on_disk = read_agent_queue_state(state_path)
            self.assertIsNotNone(on_disk)
            assert on_disk is not None
            self.assertEqual(on_disk["status"], "blocked")
            self.assertEqual(on_disk["blocked_code"], "autochro_live_ui")
            self.assertTrue(on_disk["armed"])

    def test_merge_preserves_unknown_keys(self):
        merged = merge_agent_queue_state(
            {"armed": True, "extra": 1},
            build_agent_queue_blocked_patch(load_blocked_policy().rules[0]),
        )
        self.assertEqual(merged["extra"], 1)
        self.assertEqual(merged["status"], "blocked")

    def test_unknown_code_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            state_path = os.path.join(tmp, "s.json")
            result = apply_agent_queue_blocked("not_a_real_code", state_path=state_path, dry_run=True)
            self.assertFalse(result.ok)

    def test_validate_cli_passes(self):
        repo = os.path.dirname(os.path.abspath(__file__))
        script = os.path.join(repo, "scripts", "validate_gc1_blocked_policy.py")
        proc = subprocess.run(
            [sys.executable, script],
            cwd=repo,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=30,
        )
        self.assertEqual(proc.returncode, 0, msg=proc.stderr or proc.stdout)
        self.assertIn("[PASS]", proc.stdout)

    def test_apply_cli_dry_run(self):
        repo = os.path.dirname(os.path.abspath(__file__))
        script = os.path.join(repo, "scripts", "apply_agent_queue_blocked.py")
        proc = subprocess.run(
            [sys.executable, script, "--code", "origin_gui", "--dry-run"],
            cwd=repo,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=30,
        )
        self.assertEqual(proc.returncode, 0, msg=proc.stderr or proc.stdout)
        self.assertIn("blocked", proc.stdout)


if __name__ == "__main__":
    unittest.main()
