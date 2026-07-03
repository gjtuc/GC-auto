# -*- coding: utf-8 -*-
"""P41 live harness tests."""
from __future__ import annotations

import json
import unittest
from pathlib import Path

from data_pc_origin.live_p41_manifest import ARTIFACT_NAME, run_live_p41_manifest
from data_pc_origin.p41_manifest import plan_stack_manifest_post40, validate_stack_manifest_artifact


class TestLiveP41(unittest.TestCase):
    def test_plan_ready(self) -> None:
        root = str(Path(__file__).resolve().parents[1].parent)
        plan = plan_stack_manifest_post40(root)
        self.assertGreaterEqual(plan.stack_gate_count, 302)
        self.assertEqual(plan.o0_gate_count, 71)
        self.assertTrue(plan.ready, plan.reason)

    def test_harness_writes_artifact(self) -> None:
        root = Path(__file__).resolve().parents[1]
        out = run_live_p41_manifest(artifact_dir=root, script_dir=str(root.parent))
        self.assertIn(out["status"], ("ok", "partial"))
        path = root / ARTIFACT_NAME
        self.assertTrue(path.is_file())
        data = json.loads(path.read_text(encoding="utf-8"))
        self.assertTrue(validate_stack_manifest_artifact(data))


if __name__ == "__main__":
    unittest.main()
