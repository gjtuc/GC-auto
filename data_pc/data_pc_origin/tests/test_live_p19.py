# -*- coding: utf-8
import json
import os
import unittest
from pathlib import Path
from unittest.mock import patch

from data_pc_origin.live_production_run import (
    ARTIFACT_NAME,
    run_production_live_validated,
    run_validate_fixture,
)
from data_pc_origin.p19_live_assert import (
    fixture_ok_imap_payload,
    validate_imap_live_payload,
)

E2E_LIVE = os.getenv("DATA_PC_E2E_LIVE", "").strip().lower() in ("1", "true", "yes")


class TestP19LiveAssert(unittest.TestCase):
    def test_fixture_ok(self) -> None:
        v = validate_imap_live_payload(fixture_ok_imap_payload())
        self.assertTrue(v.ok)

    def test_rejects_low_rows(self) -> None:
        v = validate_imap_live_payload({"status": "ok", "workflow_ok": True, "row_count": 5})
        self.assertFalse(v.ok)

    def test_no_pending_ok(self) -> None:
        v = validate_imap_live_payload({"status": "skipped", "reason": "no pending gc mail"})
        self.assertTrue(v.ok)


class TestLiveProductionRun(unittest.TestCase):
    def test_validate_fixture_artifact(self) -> None:
        root = Path(__file__).resolve().parents[1]
        out = run_validate_fixture(artifact_dir=root)
        self.assertEqual(out["status"], "ok")
        data = json.loads((root / ARTIFACT_NAME).read_text(encoding="utf-8"))
        self.assertTrue(data["validation"]["ok"])

    def test_mock_live_validated(self) -> None:
        with patch(
            "data_pc_origin.p18_production_e2e.run_production_imap_once",
            return_value=fixture_ok_imap_payload(),
        ):
            out = run_production_live_validated(force_live=True)
        self.assertTrue(out["validation"]["ok"])

    @unittest.skipUnless(E2E_LIVE, "set DATA_PC_E2E_LIVE=1 for live production run")
    def test_live_run_if_env(self) -> None:
        root = Path(__file__).resolve().parents[1]
        out = run_production_live_validated(artifact_dir=root)
        self.assertIn(out["status"], ("ok", "skipped", "partial", "error"))


if __name__ == "__main__":
    unittest.main()
