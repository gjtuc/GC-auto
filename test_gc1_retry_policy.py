# -*- coding: utf-8 -*-
"""
T90 — ``layer0_retry`` + ``gc1_atom_retry_policy.json`` 검증.

정적: JSON 로드·중복·delay 파싱
실행: L4 ATOM_SPECS 병합 대조 · validate CLI subprocess

실행:
  python -m unittest test_gc1_retry_policy -v
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import unittest

from gc1_runtime.layer0_retry import (
    DEFAULT_RETRY_POLICY_PATH,
    RetryPolicyEntry,
    atoms_with_runtime_retry,
    load_retry_policy,
    merge_l4_atom_specs,
    validate_retry_policy,
)


class TestRetryPolicyStatic(unittest.TestCase):
    """정적 검증 — JSON 구조."""

    def test_default_policy_loads(self):
        doc = load_retry_policy(DEFAULT_RETRY_POLICY_PATH)
        self.assertGreaterEqual(doc.schema_version, 1)
        self.assertGreater(len(doc.policies), 10)
        ids = [p.atom_id for p in doc.policies]
        self.assertEqual(len(ids), len(set(ids)))

    def test_duplicate_atom_id_raises(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "dup.json")
            payload = {
                "schema_version": 1,
                "policies": [
                    {"atom_id": "Ω.A.L4.P0.02", "max_attempt": 2, "retry_delay_ms": 1000, "fail_code": "E_WIN_NONE"},
                    {"atom_id": "Ω.A.L4.P0.02", "max_attempt": 2, "retry_delay_ms": 1000, "fail_code": "E_WIN_NONE"},
                ],
            }
            with open(path, "w", encoding="utf-8") as fh:
                json.dump(payload, fh)
            with self.assertRaises(ValueError):
                load_retry_policy(path)

    def test_retry_policy_entry_has_retry(self):
        e = RetryPolicyEntry("Ω.A.L4.P2.03", 3, 500, "E_P2_FOCUS")
        self.assertTrue(e.has_retry)
        poll = RetryPolicyEntry("Ω.A.L4.P9.11", 1, 500, "E_P9_READY", delay_kind="poll")
        self.assertFalse(poll.has_retry)


class TestRetryPolicyExecution(unittest.TestCase):
    """실행 검증 — L4 코드 대조."""

    def test_merge_l4_specs_non_empty(self):
        specs = merge_l4_atom_specs()
        self.assertIn("Ω.A.L4.P0.02", specs)
        self.assertIn("Ω.A.L4.P9.14", specs)

    def test_default_policy_matches_code(self):
        doc = load_retry_policy(DEFAULT_RETRY_POLICY_PATH)
        specs = merge_l4_atom_specs()
        result = validate_retry_policy(doc, specs)
        if not result.ok:
            self.fail("\n".join(result.errors))
        self.assertGreater(result.checked, 10)

    def test_mismatch_detected(self):
        doc = load_retry_policy(DEFAULT_RETRY_POLICY_PATH)
        specs = merge_l4_atom_specs()
        # 인위적 불일치
        bad_policy = RetryPolicyEntry(
            atom_id="Ω.A.L4.P0.02",
            max_attempt=99,
            retry_delay_ms=1000,
            fail_code="E_WIN_NONE",
        )
        doc.policies = [bad_policy]
        result = validate_retry_policy(doc, specs)
        self.assertFalse(result.ok)
        self.assertTrue(any("max_attempt" in e for e in result.errors))

    def test_validate_cli_passes(self):
        repo = os.path.dirname(os.path.abspath(__file__))
        script = os.path.join(repo, "scripts", "validate_gc1_retry_policy.py")
        proc = subprocess.run(
            [sys.executable, script],
            cwd=repo,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=60,
        )
        self.assertEqual(proc.returncode, 0, msg=proc.stderr or proc.stdout)
        self.assertIn("[PASS]", proc.stdout)

    def test_runtime_retry_atoms_subset_of_policy(self):
        doc = load_retry_policy(DEFAULT_RETRY_POLICY_PATH)
        specs = merge_l4_atom_specs()
        policy_ids = {p.atom_id for p in doc.policies}
        for aid in atoms_with_runtime_retry(specs):
            self.assertIn(aid, policy_ids, msg=f"{aid} missing from policy json")


if __name__ == "__main__":
    unittest.main()
