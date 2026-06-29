# -*- coding: utf-8
import json
import unittest
from pathlib import Path

from data_pc_origin.live_merge_readiness import ARTIFACT_NAME, run_live_merge_readiness
from data_pc_origin.p28_merge_readiness import (
    build_merge_readiness_manifest,
    merge_structural_ready,
    validate_merge_readiness_artifact,
)


class TestP28MergeReadiness(unittest.TestCase):
    def test_manifest_structural(self) -> None:
        script_dir = str(Path(__file__).resolve().parents[2])
        m = build_merge_readiness_manifest(script_dir)
        self.assertTrue(merge_structural_ready(m), m.failures)
        self.assertIn("data_pc_only_diff", m.checks)

    def test_deploy_example_allowed_in_diff(self) -> None:
        """Task B — deploy/gc_automation.env.*.example 는 merge diff 허용."""
        from data_pc_origin.p28_merge_readiness import ALLOWED_PREFIXES

        self.assertIn("deploy/", ALLOWED_PREFIXES)


class TestLiveMergeReadiness(unittest.TestCase):
    def test_run_artifact(self) -> None:
        script_dir = str(Path(__file__).resolve().parents[2])
        root = Path(__file__).resolve().parents[1]
        out = run_live_merge_readiness(artifact_dir=root, script_dir=script_dir)
        self.assertIn(out["status"], ("ok", "partial"))
        self.assertTrue(validate_merge_readiness_artifact(out))
        data = json.loads((root / ARTIFACT_NAME).read_text(encoding="utf-8"))
        self.assertIn("checks", data["manifest"])


if __name__ == "__main__":
    unittest.main()
