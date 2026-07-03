# -*- coding: utf-8
import json
import unittest
from pathlib import Path
from unittest.mock import patch

from data_pc_origin.live_p31_merge_pr import ARTIFACT_NAME, run_live_p31_merge_pr
from data_pc_origin.p31_merge_pr import (
    gh_available,
    plan_merge_pr_post30,
    validate_merge_pr_artifact,
)


class TestP31MergePr(unittest.TestCase):
    def test_plan_real(self) -> None:
        script_dir = str(Path(__file__).resolve().parents[2])
        plan = plan_merge_pr_post30(script_dir)
        self.assertGreaterEqual(plan.gate_count, 222)
        self.assertTrue(plan.push_ready)
        self.assertTrue(plan.remote_synced)

    def test_gh_available_false_when_logged_out(self) -> None:
        with patch("data_pc_origin.p31_merge_pr.subprocess.run") as mock_run:
            mock_run.return_value.returncode = 1
            mock_run.return_value.stdout = ""
            mock_run.return_value.stderr = "not logged in"
            self.assertFalse(gh_available())


class TestLiveP31MergePr(unittest.TestCase):
    def test_dry_artifact(self) -> None:
        script_dir = str(Path(__file__).resolve().parents[2])
        root = Path(__file__).resolve().parents[1]
        out = run_live_p31_merge_pr(artifact_dir=root, script_dir=script_dir)
        self.assertIn(out["status"], ("ok", "partial"))
        self.assertTrue(validate_merge_pr_artifact(out))
        data = json.loads((root / ARTIFACT_NAME).read_text(encoding="utf-8"))
        self.assertTrue(data["plan"]["structural_ready"])


if __name__ == "__main__":
    unittest.main()
