# -*- coding: utf-8
import json
import os
import unittest
from pathlib import Path

from data_pc_origin.live_full_archive import run_live_full_archive
from data_pc_origin.live_mail import run_live_mail
from data_pc_origin.tests._helpers import with_live_e2e_env

LIVE_OPJU = (
    r"G:\연구소\실험\실험데이터\촉매 반응\DRE 반응(C2H6)"
    r"\20260626 DRE(1.5) 600C Ni5_Ce5_Al2O3_test"
    r"\20260626 DRE(1.5) 600C Ni5_Ce5_Al2O3_test.opju"
)


class TestLiveFullArchive(unittest.TestCase):
    def test_skipped_writes_artifact(self) -> None:
        root = Path(__file__).resolve().parents[1]
        out = run_live_full_archive("", artifact_dir=root)
        self.assertEqual(out["status"], "skipped")
        self.assertEqual(out["mode"], "full_archive")

    @unittest.skipUnless(os.path.isdir("G:\\"), "G: not mounted")
    def test_dry_run_if_live(self) -> None:
        if not Path(LIVE_OPJU).is_file():
            self.skipTest("live opju missing")
        root = Path(__file__).resolve().parents[1]
        with with_live_e2e_env():
            out = run_live_full_archive(LIVE_OPJU, artifact_dir=root, dry_run=True)
        self.assertEqual(out["status"], "dry_run")
        self.assertEqual(out["mode"], "full_archive")


class TestLiveMail(unittest.TestCase):
    def test_skipped_writes_artifact(self) -> None:
        root = Path(__file__).resolve().parents[1]
        out = run_live_mail("", artifact_dir=root)
        self.assertEqual(out["status"], "skipped")
        self.assertEqual(out.get("entry"), "mail")

    @unittest.skipUnless(os.path.isdir("G:\\"), "G: not mounted")
    def test_dry_run_if_live(self) -> None:
        if not Path(LIVE_OPJU).is_file():
            self.skipTest("live opju missing")
        root = Path(__file__).resolve().parents[1]
        with with_live_e2e_env():
            out = run_live_mail(None, opju_path=LIVE_OPJU, artifact_dir=root, dry_run=True)
        self.assertEqual(out["status"], "dry_run")
        data = json.loads((root / "live_mail_result.json").read_text(encoding="utf-8"))
        self.assertIn("attachment", data)


if __name__ == "__main__":
    unittest.main()
