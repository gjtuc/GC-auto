# -*- coding: utf-8
import json
import os
import unittest
from pathlib import Path

from data_pc_origin.live_full_native import run_live_full_native
from data_pc_origin.tests._helpers import without_skip_origin

KCH_INBOX = (
    r"c:\Users\user\Desktop\.cursor\KCH\inbox"
    r"\20260620 DRE(1.5) 600C Ni5_Ce5_Al2O3.xlsx"
)


class TestLiveFullNative(unittest.TestCase):
    def test_skipped_writes_artifact(self) -> None:
        root = Path(__file__).resolve().parents[1]
        out = run_live_full_native("", artifact_dir=root)
        self.assertEqual(out["status"], "skipped")
        self.assertEqual(out["mode"], "full_archive")
        self.assertTrue(out.get("native_stage3"))

    def test_dry_run_with_kch(self) -> None:
        if not Path(KCH_INBOX).is_file():
            self.skipTest("KCH inbox sample missing")
        root = Path(__file__).resolve().parents[1]
        with without_skip_origin():
            out = run_live_full_native(KCH_INBOX, artifact_dir=root, dry_run=True)
        self.assertEqual(out["status"], "dry_run")
        self.assertIn("experiment_basename", out)
        data = json.loads(
            (root / "live_full_native_result.json").read_text(encoding="utf-8")
        )
        self.assertEqual(data["reaction_type"], "DRE")

    @unittest.skipUnless(
        Path(KCH_INBOX).is_file() and os.path.isdir("G:\\"),
        "KCH sample or G: missing",
    )
    def test_live_full_native_if_ready(self) -> None:
        if os.getenv("DATA_PC_SKIP_ORIGIN", "").strip().lower() in ("1", "true", "yes"):
            self.skipTest("SKIP_ORIGIN=1")
        root = Path(__file__).resolve().parents[1]
        out = run_live_full_native(KCH_INBOX, artifact_dir=root)
        self.assertEqual(out["status"], "ok")
        self.assertGreater(out.get("row_count", 0), 0)
        self.assertTrue(str(out.get("target_opju", "")).endswith(".opju"))
        self.assertTrue(out.get("save_in_place"))


if __name__ == "__main__":
    unittest.main()
