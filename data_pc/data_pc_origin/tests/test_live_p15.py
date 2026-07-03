# -*- coding: utf-8
import json
import os
import unittest
from pathlib import Path

from data_pc_origin.live_supervisor import (
    ARTIFACT_NAME,
    build_dry_supervisor_tick,
    run_live_supervisor,
)
from data_pc_origin.p14_runtime_bridge import ORIGIN_PIPELINE_ENV

SUPERVISOR_LIVE = os.getenv("DATA_PC_SUPERVISOR_LIVE", "").strip().lower() in (
    "1",
    "true",
    "yes",
)


class TestP15SupervisorBridge(unittest.TestCase):
    def test_build_dry_supervisor_tick(self) -> None:
        script_dir = str(Path(__file__).resolve().parents[2])
        tick, _ = build_dry_supervisor_tick(
            script_dir,
            origin_pipeline=True,
            dry_run_pipeline=True,
        )
        self.assertEqual(tick["status_code"], "pipeline_done")

    def test_resolve_origin_env(self) -> None:
        script_dir = str(Path(__file__).resolve().parents[2])
        os.environ[ORIGIN_PIPELINE_ENV] = "1"
        tick, _ = build_dry_supervisor_tick(script_dir, origin_pipeline=True)
        self.assertIn("workflows=", str(tick.get("gate_detail", "")))


class TestLiveSupervisor(unittest.TestCase):
    def test_dry_tick_writes_artifact(self) -> None:
        root = Path(__file__).resolve().parents[1]
        out = run_live_supervisor(artifact_dir=root, dry_tick=True, origin_pipeline=True)
        self.assertEqual(out["status"], "ok")
        self.assertEqual(out["mode"], "dry_tick")
        data = json.loads((root / ARTIFACT_NAME).read_text(encoding="utf-8"))
        self.assertEqual(data["tick"]["status_code"], "pipeline_done")

    @unittest.skipUnless(
        SUPERVISOR_LIVE,
        "set DATA_PC_SUPERVISOR_LIVE=1 for live supervisor tick",
    )
    def test_live_tick_if_env(self) -> None:
        root = Path(__file__).resolve().parents[1]
        out = run_live_supervisor(artifact_dir=root, dry_tick=False, origin_pipeline=True)
        self.assertIn(out["status"], ("ok", "error"))


if __name__ == "__main__":
    unittest.main()
