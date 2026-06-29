# -*- coding: utf-8
import json
import unittest
from pathlib import Path

from data_pc_origin.live_autostart import ARTIFACT_NAME, run_live_autostart
from data_pc_origin.p22_autostart import (
    build_autostart_manifest,
    validate_autostart_artifact,
    verify_watchdog_delegation,
)


class TestP22Autostart(unittest.TestCase):
    def test_manifest_ready(self) -> None:
        script_dir = str(Path(__file__).resolve().parents[2])
        m = build_autostart_manifest(script_dir)
        self.assertTrue(m.ready)
        self.assertEqual(m.watch_mode, "runtime_origin")

    def test_watchdog_delegates(self) -> None:
        script_dir = str(Path(__file__).resolve().parents[2])
        chk = verify_watchdog_delegation(script_dir)
        self.assertTrue(chk.ok)


class TestLiveAutostart(unittest.TestCase):
    def test_run_artifact(self) -> None:
        script_dir = str(Path(__file__).resolve().parents[2])
        root = Path(__file__).resolve().parents[1]
        out = run_live_autostart(artifact_dir=root, script_dir=script_dir)
        self.assertEqual(out["status"], "ok")
        self.assertTrue(validate_autostart_artifact(out))
        data = json.loads((root / ARTIFACT_NAME).read_text(encoding="utf-8"))
        self.assertTrue(data["manifest"]["ready"])


if __name__ == "__main__":
    unittest.main()
