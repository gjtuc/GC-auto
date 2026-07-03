# -*- coding: utf-8
import json
import os
import unittest
import unittest.mock
from pathlib import Path

from data_pc_origin.live_imap import run_imap_probe, run_live_imap
from data_pc_origin.p13_imap_adapter import mask_email, prepare_imap, reconcile_processed_unseen_mails

IMAP_LIVE = os.getenv("DATA_PC_IMAP_LIVE", "").strip().lower() in ("1", "true", "yes")


class TestP13ImapAdapter(unittest.TestCase):
    def test_mask_email(self) -> None:
        self.assertIn("@", mask_email("user@example.com"))
        self.assertNotIn("user", mask_email("user@example.com"))

    def test_prepare_imap(self) -> None:
        prep = prepare_imap()
        self.assertIn("email_masked", prep.to_dict())

    def test_reconcile_no_creds_returns_zero(self) -> None:
        with unittest.mock.patch(
            "data_pc_origin.p13_imap_adapter.prepare_imap",
            return_value=type(
                "P",
                (),
                {
                    "ready": False,
                    "to_dict": lambda self: {"ready": False},
                },
            )(),
        ):
            self.assertEqual(reconcile_processed_unseen_mails(), 0)


class TestLiveImap(unittest.TestCase):
    def test_probe_dry(self) -> None:
        root = Path(__file__).resolve().parents[1]
        out = run_imap_probe(artifact_dir=root, dry_run=True)
        self.assertEqual(out["status"], "dry_run")
        data = json.loads((root / "live_imap_result.json").read_text(encoding="utf-8"))
        self.assertEqual(data["mode"], "imap_probe")

    def test_live_imap_fetch_dry(self) -> None:
        root = Path(__file__).resolve().parents[1]
        out = run_live_imap(artifact_dir=root, dry_run=True, fetch_only=True)
        self.assertEqual(out["status"], "dry_run")
        self.assertEqual(out.get("entry"), "imap")

    @unittest.skipUnless(IMAP_LIVE, "set DATA_PC_IMAP_LIVE=1 for live IMAP tests")
    def test_imap_probe_live_if_creds(self) -> None:
        root = Path(__file__).resolve().parents[1]
        out = run_imap_probe(artifact_dir=root, dry_run=False)
        self.assertIn(out["status"], ("ok", "error"))
        if out["status"] == "ok":
            self.assertIn("total_pending", out)

    @unittest.skipUnless(IMAP_LIVE, "set DATA_PC_IMAP_LIVE=1 for live IMAP tests")
    def test_fetch_only_if_pending(self) -> None:
        root = Path(__file__).resolve().parents[1]
        probe = run_imap_probe(artifact_dir=root, dry_run=False)
        if probe.get("status") != "ok" or probe.get("total_pending", 0) == 0:
            self.skipTest("no pending IMAP mail")
        out = run_live_imap(artifact_dir=root, fetch_only=True, mark_seen=False)
        if out["status"] == "skipped":
            self.skipTest("no pending at fetch time")
        self.assertEqual(out["status"], "ok")
        self.assertTrue(out.get("attachment_exists"))


if __name__ == "__main__":
    unittest.main()
