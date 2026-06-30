# -*- coding: utf-8 -*-
"""
T93 — ``layer0_resume`` PART6 Resume 정책 + ``apply_resume_from`` 실행 검증.

실행:
  python -m unittest test_gc1_resume_policy -v
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import unittest

from gc1_runtime.layer0_resume import (
    DEFAULT_RESUME_POLICY_PATH,
    atoms_before_resume,
    load_resume_policy,
    validate_resume_policy,
)
from gc1_runtime.layer1_state import AtomStatus, JobPaths, StateStore
from gc1_runtime.layer4_atoms_p8_p9 import P0_P9_ATOM_IDS
from gc1_runtime.layer4_job import apply_resume_from, ensure_job_state


class TestResumePolicyStatic(unittest.TestCase):
    def test_load_default_policy(self):
        doc = load_resume_policy(DEFAULT_RESUME_POLICY_PATH)
        self.assertEqual(len(doc.rules), 2)
        ids = {r.resume_from for r in doc.rules}
        self.assertIn("Ω.A.L4.P4.03", ids)
        self.assertIn("Ω.A.L4.P9.02", ids)

    def test_validate_default(self):
        doc = load_resume_policy(DEFAULT_RESUME_POLICY_PATH)
        result = validate_resume_policy(doc, P0_P9_ATOM_IDS)
        self.assertTrue(result.ok, msg=result.errors)

    def test_atoms_before_p9_02(self):
        skipped = atoms_before_resume("Ω.A.L4.P9.02", P0_P9_ATOM_IDS)
        self.assertIn("Ω.A.L4.P8.06", skipped)
        self.assertNotIn("Ω.A.L4.P9.02", skipped)
        self.assertNotIn("Ω.A.L4.P9.14", skipped)


class TestResumePolicyExecution(unittest.TestCase):
    def setUp(self) -> None:
        self._tmpdir = tempfile.TemporaryDirectory()
        self.store = StateStore(JobPaths(self._tmpdir.name))

    def tearDown(self) -> None:
        self._tmpdir.cleanup()

    def test_apply_resume_p9_02(self):
        """실행 검증 — P9.02 resume 시 P9.02 이전 atom 전부 ok+resume."""
        state = ensure_job_state(self.store, prep_enabled=True, force=False)
        state.resume_from = "Ω.A.L4.P9.02"
        self.store.save(state)
        apply_resume_from(self.store, self.store.load())
        state = self.store.load()
        for aid in atoms_before_resume("Ω.A.L4.P9.02", P0_P9_ATOM_IDS):
            rec = state.atoms[aid]
            self.assertEqual(rec.status, AtomStatus.OK, msg=aid)
            self.assertEqual(rec.probe_snapshot.get("skipped_reason"), "resume")
        self.assertNotEqual(
            state.atoms["Ω.A.L4.P9.02"].probe_snapshot.get("skipped_reason"),
            "resume",
        )

    def test_validate_cli_passes(self):
        repo = os.path.dirname(os.path.abspath(__file__))
        script = os.path.join(repo, "scripts", "validate_gc1_resume_policy.py")
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


if __name__ == "__main__":
    unittest.main()
