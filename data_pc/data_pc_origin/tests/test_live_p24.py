# -*- coding: utf-8
import json
import unittest
from pathlib import Path

from data_pc_origin.live_ops_rollup import ARTIFACT_NAME, run_live_ops_rollup
from data_pc_origin.p24_ops_rollup import (
    build_ops_rollup_manifest,
    validate_ops_rollup_artifact,
)


class TestP24OpsRollup(unittest.TestCase):
    def test_manifest_layers(self) -> None:
        script_dir = str(Path(__file__).resolve().parents[2])
        m = build_ops_rollup_manifest(script_dir)
        self.assertIn("readiness", m.layers)
        self.assertIn("github", m.layers)
        self.assertGreaterEqual(m.gate_count, 166)

    def test_production_ready(self) -> None:
        script_dir = str(Path(__file__).resolve().parents[2])
        m = build_ops_rollup_manifest(script_dir)
        self.assertTrue(m.production_ready)


class TestLiveOpsRollup(unittest.TestCase):
    def test_run_artifact(self) -> None:
        script_dir = str(Path(__file__).resolve().parents[2])
        root = Path(__file__).resolve().parents[1]
        out = run_live_ops_rollup(artifact_dir=root, script_dir=script_dir)
        self.assertIn(out["status"], ("ok", "partial"))
        self.assertTrue(validate_ops_rollup_artifact(out))
        data = json.loads((root / ARTIFACT_NAME).read_text(encoding="utf-8"))
        self.assertTrue(data["manifest"]["production_ready"])


if __name__ == "__main__":
    unittest.main()
