# -*- coding: utf-8
import json
import os
import unittest
from pathlib import Path

from data_pc_origin.live_kch import run_live_kch
from data_pc_origin.tests._helpers import without_skip_origin

KCH_INBOX = (
    r"c:\Users\user\Desktop\.cursor\KCH\inbox"
    r"\20260620 DRE(1.5) 600C Ni5_Ce5_Al2O3.xlsx"
)
LIVE_OPJU = (
    r"G:\연구소\실험\실험데이터\촉매 반응\DRE 반응(C2H6)"
    r"\20260626 DRE(1.5) 600C Ni5_Ce5_Al2O3_test"
    r"\20260626 DRE(1.5) 600C Ni5_Ce5_Al2O3_test.opju"
)


class TestLiveKch(unittest.TestCase):
    def test_skipped_writes_artifact(self) -> None:
        root = Path(__file__).resolve().parents[1]
        out = run_live_kch("", artifact_dir=root, stage2_only=True)
        self.assertEqual(out["status"], "skipped")
        self.assertEqual(out["data_source"], "kch_raw")

    def test_dry_run_with_kch(self) -> None:
        if not Path(KCH_INBOX).is_file():
            self.skipTest("KCH inbox sample missing")
        root = Path(__file__).resolve().parents[1]
        out = run_live_kch(KCH_INBOX, artifact_dir=root, stage2_only=True, dry_run=True)
        self.assertEqual(out["status"], "dry_run")
        data = json.loads((root / "live_kch_result.json").read_text(encoding="utf-8"))
        self.assertIn("kch_basename", data)

    @unittest.skipUnless(Path(KCH_INBOX).is_file(), "KCH inbox sample missing")
    def test_stage2_only_live(self) -> None:
        root = Path(__file__).resolve().parents[1]
        out = run_live_kch(KCH_INBOX, artifact_dir=root, stage2_only=True)
        self.assertEqual(out["status"], "ok")
        self.assertGreater(out.get("row_count", 0), 0)
        self.assertTrue(str(out.get("saved_excel", "")).endswith(".xlsx"))

    @unittest.skipUnless(os.path.isdir("G:\\"), "G: not mounted")
    def test_full_opju_dry_if_live(self) -> None:
        if not Path(KCH_INBOX).is_file() or not Path(LIVE_OPJU).is_file():
            self.skipTest("live fixtures missing")
        root = Path(__file__).resolve().parents[1]
        with without_skip_origin():
            out = run_live_kch(
                KCH_INBOX,
                opju_path=LIVE_OPJU,
                artifact_dir=root,
                dry_run=True,
            )
        self.assertEqual(out["status"], "dry_run")


if __name__ == "__main__":
    unittest.main()
