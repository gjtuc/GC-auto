# -*- coding: utf-8
import json
import unittest
from pathlib import Path
from unittest.mock import patch

from data_pc_origin.live_watch_resident import ARTIFACT_NAME, run_live_watch_resident
from data_pc_origin.p26_watch_resident import (
    prep_watch_resident_smoke,
    run_watch_resident_delegate,
    validate_watch_resident_artifact,
)


class TestP26WatchResident(unittest.TestCase):
    def test_prep_ready(self) -> None:
        script_dir = str(Path(__file__).resolve().parents[2])
        prep = prep_watch_resident_smoke(script_dir)
        self.assertTrue(prep.ready)
        self.assertEqual(prep.watch_mode, "runtime_origin")

    def test_delegate_once(self) -> None:
        script_dir = str(Path(__file__).resolve().parents[2])
        state = {"n": 0}

        def _once(_sd: str) -> None:
            state["n"] += 1

        with patch("data_pc_runtime.layer4_supervisor.run_supervisor", side_effect=_once):
            run_watch_resident_delegate(script_dir, skip_wifi_check=True)
        self.assertEqual(state["n"], 1)


class TestLiveWatchResident(unittest.TestCase):
    def test_prep_artifact(self) -> None:
        script_dir = str(Path(__file__).resolve().parents[2])
        root = Path(__file__).resolve().parents[1]
        out = run_live_watch_resident(artifact_dir=root, script_dir=script_dir)
        self.assertIn(out["status"], ("ok", "partial"))
        self.assertTrue(validate_watch_resident_artifact(out))

    def test_delegate_harness(self) -> None:
        root = Path(__file__).resolve().parents[1]
        script_dir = str(Path(__file__).resolve().parents[2])
        out = run_live_watch_resident(artifact_dir=root, script_dir=script_dir, delegate=True)
        self.assertEqual(out["status"], "ok")
        self.assertTrue(out.get("supervisor_called"))
        data = json.loads((root / ARTIFACT_NAME).read_text(encoding="utf-8"))
        self.assertEqual(data["mode"], "delegate")


if __name__ == "__main__":
    unittest.main()
