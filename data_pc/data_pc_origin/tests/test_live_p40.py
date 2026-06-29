# -*- coding: utf-8 -*-
import json
import unittest
from pathlib import Path
from unittest.mock import patch

from data_pc_origin.live_p40_merge_pr import ARTIFACT_NAME, run_live_p40_merge_pr
from data_pc_origin.p31_merge_pr import gh_available
from data_pc_origin.p40_merge_pr import (
    plan_merge_pr_post41,
    validate_merge_pr_post41_artifact,
)


class TestP40MergePr(unittest.TestCase):
    def test_plan_real(self) -> None:
        """코드 검증 — post-P41 merge plan (P-EXT 310 · stack 616)."""
        script_dir = str(Path(__file__).resolve().parents[2])
        plan = plan_merge_pr_post41(script_dir)
        self.assertGreaterEqual(plan.gate_count, 310)
        self.assertGreaterEqual(plan.stack_gate_count, 616)
        self.assertTrue(plan.push_ready)
        self.assertTrue(plan.remote_synced)
        self.assertTrue(plan.structural_ready)
        self.assertIn("stack_manifest_ready", plan.checks)

    def test_gh_available_false_when_logged_out(self) -> None:
        with patch("data_pc_origin.p31_merge_pr.subprocess.run") as mock_run:
            mock_run.return_value.returncode = 1
            mock_run.return_value.stdout = ""
            mock_run.return_value.stderr = "not logged in"
            self.assertFalse(gh_available())


class TestLiveP40MergePr(unittest.TestCase):
    def test_dry_artifact(self) -> None:
        """실행 검증 — live_p40_merge_pr_result.json artifact."""
        script_dir = str(Path(__file__).resolve().parents[2])
        root = Path(__file__).resolve().parents[1]
        out = run_live_p40_merge_pr(artifact_dir=root, script_dir=script_dir)
        self.assertIn(out["status"], ("ok", "partial"))
        self.assertTrue(validate_merge_pr_post41_artifact(out))
        data = json.loads((root / ARTIFACT_NAME).read_text(encoding="utf-8"))
        self.assertTrue(data["plan"]["structural_ready"])
        self.assertGreaterEqual(data["plan"]["gate_count"], 310)
        self.assertGreaterEqual(data["stack_manifest"]["stack_gate_count"], 616)


if __name__ == "__main__":
    unittest.main()
