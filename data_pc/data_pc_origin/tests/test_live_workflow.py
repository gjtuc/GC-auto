# -*- coding: utf-8
import json
import os
import unittest
from pathlib import Path

from data_pc_origin.live_workflow import (
    ARTIFACT_NAME,
    prepare_live_workflow,
    run_live_workflow,
)
from data_pc_origin.tests._helpers import without_skip_origin

LIVE_OPJU = (
    r"G:\연구소\실험\실험데이터\촉매 반응\DRE 반응(C2H6)"
    r"\20260626 DRE(1.5) 600C Ni5_Ce5_Al2O3_test"
    r"\20260626 DRE(1.5) 600C Ni5_Ce5_Al2O3_test.opju"
)


class TestLiveWorkflow(unittest.TestCase):
    def test_prepare_no_path(self) -> None:
        prep = prepare_live_workflow("")
        self.assertFalse(prep.ready)

    def test_run_skipped_writes_artifact(self) -> None:
        root = Path(__file__).resolve().parents[1]
        out = run_live_workflow("", artifact_dir=root)
        self.assertEqual(out["status"], "skipped")
        data = json.loads((root / ARTIFACT_NAME).read_text(encoding="utf-8"))
        self.assertIn("prep", data)
        self.assertEqual(data["mode"], "opju_only")

    @unittest.skipUnless(os.path.isdir("G:\\"), "G: not mounted")
    def test_dry_run_if_live_opju(self) -> None:
        if not Path(LIVE_OPJU).is_file():
            self.skipTest("live opju not on disk")
        root = Path(__file__).resolve().parents[1]
        with without_skip_origin():
            out = run_live_workflow(LIVE_OPJU, artifact_dir=root, dry_run=True)
        self.assertEqual(out["status"], "dry_run")
        self.assertGreater(out.get("row_count", 0), 0)


if __name__ == "__main__":
    unittest.main()
