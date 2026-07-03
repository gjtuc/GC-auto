# -*- coding: utf-8
import json
import os
import unittest
from pathlib import Path
from unittest.mock import patch

from data_pc_origin.live_production_e2e import ARTIFACT_NAME, run_live_production_e2e
from data_pc_origin.p14_runtime_bridge import ORIGIN_PIPELINE_ENV
from data_pc_origin.p18_production_e2e import (
    E2E_LIVE_ENV,
    PRODUCTION_STACK,
    apply_production_e2e_env,
    prepare_production_e2e,
)

E2E_LIVE = os.getenv("DATA_PC_E2E_LIVE", "").strip().lower() in ("1", "true", "yes")


class TestP18ProductionE2e(unittest.TestCase):
    def test_prep_stack(self) -> None:
        script_dir = str(Path(__file__).resolve().parents[2])
        prep = prepare_production_e2e(
            script_dir,
            environ={ORIGIN_PIPELINE_ENV: "1", "DATA_PC_SKIP_ORIGIN": "0"},
        )
        self.assertEqual(prep.stack, PRODUCTION_STACK)
        self.assertTrue(prep.full_e2e_ready)

    def test_skip_origin_blocks(self) -> None:
        script_dir = str(Path(__file__).resolve().parents[2])
        prep = prepare_production_e2e(
            script_dir,
            environ={ORIGIN_PIPELINE_ENV: "1", "DATA_PC_SKIP_ORIGIN": "1"},
        )
        self.assertFalse(prep.ready)

    def test_apply_env(self) -> None:
        apply_production_e2e_env()
        self.assertEqual(os.environ.get("DATA_PC_SKIP_ORIGIN"), "0")
        self.assertEqual(os.environ.get("DATA_PC_ORIGIN_PIPELINE"), "1")


class TestLiveProductionE2e(unittest.TestCase):
    def test_dry_prep_artifact(self) -> None:
        root = Path(__file__).resolve().parents[1]
        out = run_live_production_e2e(artifact_dir=root, dry_prep=True)
        self.assertEqual(out["status"], "ok")
        self.assertEqual(out["mode"], "dry_prep")
        data = json.loads((root / ARTIFACT_NAME).read_text(encoding="utf-8"))
        self.assertEqual(data["would_run"], PRODUCTION_STACK)

    def test_live_mock(self) -> None:
        with patch("data_pc_origin.live_production_e2e.e2e_live_enabled", return_value=True):
            with patch(
                "data_pc_origin.live_production_e2e.run_production_imap_once",
                return_value={"status": "ok", "workflow_ok": True},
            ):
                out = run_live_production_e2e(live=True)
        self.assertEqual(out["mode"], "live")

    @unittest.skipUnless(E2E_LIVE, "set DATA_PC_E2E_LIVE=1 for live production E2E")
    def test_prep_live_if_env(self) -> None:
        root = Path(__file__).resolve().parents[1]
        out = run_live_production_e2e(artifact_dir=root, prep_live=True)
        self.assertIn(out["status"], ("ok", "skipped", "error"))


if __name__ == "__main__":
    unittest.main()
