# -*- coding: utf-8 -*-
import json
import unittest
from pathlib import Path

from data_pc_origin.live_run import ARTIFACT_NAME, prepare_live_e2e, run_live_e2e


class TestLiveRun(unittest.TestCase):
    def test_prepare_no_path(self) -> None:
        prep = prepare_live_e2e("")
        self.assertFalse(prep.ready)
        self.assertIn("path", prep.reason.lower())

    def test_run_skipped_writes_artifact(self) -> None:
        root = Path(__file__).resolve().parents[1]
        out = run_live_e2e("", artifact_dir=root)
        self.assertEqual(out["status"], "skipped")
        artifact = root / ARTIFACT_NAME
        self.assertTrue(artifact.is_file())
        data = json.loads(artifact.read_text(encoding="utf-8"))
        self.assertIn("prep", data)
        self.assertFalse(data["prep"]["ready"])


if __name__ == "__main__":
    unittest.main()
