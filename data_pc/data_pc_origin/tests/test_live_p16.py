# -*- coding: utf-8
import json
import os
import unittest
from pathlib import Path
from unittest.mock import patch

from data_pc_origin.live_watch import ARTIFACT_NAME, run_live_watch
from data_pc_origin.p16_watch_bridge import (
    LEGACY_WATCH_ENV,
    describe_watch_mode,
    should_use_runtime_watch,
)

ORIGIN_PIPELINE_ENV = "DATA_PC_ORIGIN_PIPELINE"


class TestP16WatchBridge(unittest.TestCase):
    def test_default_runtime_watch(self) -> None:
        self.assertTrue(should_use_runtime_watch({LEGACY_WATCH_ENV: "0"}))

    def test_legacy_opt_out(self) -> None:
        self.assertFalse(should_use_runtime_watch({LEGACY_WATCH_ENV: "1"}))
        self.assertEqual(describe_watch_mode({LEGACY_WATCH_ENV: "1"}), "legacy")

    def test_origin_mode_label(self) -> None:
        self.assertEqual(
            describe_watch_mode({ORIGIN_PIPELINE_ENV: "1"}),
            "runtime_origin",
        )


class TestLiveWatch(unittest.TestCase):
    def test_dry_tick_writes_artifact(self) -> None:
        root = Path(__file__).resolve().parents[1]
        out = run_live_watch(artifact_dir=root, dry_tick=True, origin_pipeline=True)
        self.assertEqual(out["status"], "ok")
        self.assertEqual(out["mode"], "dry_tick")
        data = json.loads((root / ARTIFACT_NAME).read_text(encoding="utf-8"))
        self.assertEqual(data["tick"]["status_code"], "pipeline_done")

    def test_run_data_pc_watch_delegates(self) -> None:
        from data_pc_watch import run_data_pc_watch

        script_dir = str(Path(__file__).resolve().parents[2])
        os.environ[LEGACY_WATCH_ENV] = "0"
        os.environ[ORIGIN_PIPELINE_ENV] = "1"
        with patch("data_pc_origin.p16_watch_bridge.run_watch_via_runtime") as mocked:
            mocked.return_value = None
            run_data_pc_watch(script_dir, skip_wifi_check=True)
        self.assertTrue(mocked.called)


if __name__ == "__main__":
    unittest.main()
