# -*- coding: utf-8
import json
import unittest
from pathlib import Path

from data_pc_origin.live_merge_readiness import ARTIFACT_NAME, run_live_merge_readiness
from data_pc_origin.p28_merge_readiness import (
    build_merge_readiness_manifest,
    validate_merge_readiness_artifact,
)


class TestP28MergeReadiness(unittest.TestCase):
    def test_manifest_ready(self) -> None:
        script_dir = str(Path(__file__).resolve().parents[2])
        m = build_merge_readiness_manifest(script_dir)
        self.assertTrue(m.ready)
        self.assertTrue(m.ops_ready)
        self.assertIn("data_pc_only_diff", m.checks)


class TestLiveMergeReadiness(unittest.TestCase):
    def test_run_artifact(self) -> None:
        script_dir = str(Path(__file__).resolve().parents[2])
        root = Path(__file__).resolve().parents[1]
        out = run_live_merge_readiness(artifact_dir=root, script_dir=script_dir)
        self.assertEqual(out["status"], "ok")
        self.assertTrue(validate_merge_readiness_artifact(out))
        data = json.loads((root / ARTIFACT_NAME).read_text(encoding="utf-8"))
        self.assertTrue(data["manifest"]["ready"])


if __name__ == "__main__":
    unittest.main()
