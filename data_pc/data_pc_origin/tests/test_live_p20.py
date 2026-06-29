# -*- coding: utf-8
import json
import unittest
from pathlib import Path

from data_pc_origin.live_readiness import ARTIFACT_NAME, run_live_readiness
from data_pc_origin.p20_readiness import build_readiness_manifest, validate_readiness_artifact


class TestP20Readiness(unittest.TestCase):
    def test_manifest_layers(self) -> None:
        script_dir = str(Path(__file__).resolve().parents[2])
        m = build_readiness_manifest(
            script_dir,
            environ={"DATA_PC_ORIGIN_PIPELINE": "1"},
        )
        self.assertIn("env", m.layers)
        self.assertIn("runtime_bridge", m.layers)

    def test_dry_tick(self) -> None:
        script_dir = str(Path(__file__).resolve().parents[2])
        m = build_readiness_manifest(script_dir, dry_tick=True)
        self.assertIn("supervisor_dry_tick", m.checks)


class TestLiveReadiness(unittest.TestCase):
    def test_run_artifact(self) -> None:
        root = Path(__file__).resolve().parents[1]
        out = run_live_readiness(artifact_dir=root)
        self.assertTrue(out.get("artifact_valid"))
        data = json.loads((root / ARTIFACT_NAME).read_text(encoding="utf-8"))
        self.assertIn("manifest", data)

    def test_tick_mode(self) -> None:
        root = Path(__file__).resolve().parents[1]
        out = run_live_readiness(artifact_dir=root, dry_tick=True)
        tick = out["manifest"]["layers"].get("supervisor_tick", {})
        self.assertTrue(tick.get("ok"))
        self.assertTrue(validate_readiness_artifact(out))


if __name__ == "__main__":
    unittest.main()
