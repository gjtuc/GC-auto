# -*- coding: utf-8
import json
import unittest
from pathlib import Path
from unittest.mock import patch

from data_pc_origin.live_native_production import ARTIFACT_NAME, run_live_native_production
from data_pc_origin.p25_native_live import (
    NATIVE_LIVE_ENV,
    prep_native_production_live,
    validate_native_live_artifact,
)


class TestP25NativeLive(unittest.TestCase):
    def test_prep_native_env(self) -> None:
        script_dir = str(Path(__file__).resolve().parents[2])
        prep = prep_native_production_live(script_dir)
        self.assertFalse(prep.skip_origin)
        self.assertTrue(prep.ops_ready)

    def test_no_override_on_imap(self) -> None:
        with patch("data_pc_origin.p18_production_e2e.apply_production_e2e_env") as mocked:
            with patch(
                "data_pc_origin.live_imap.run_live_imap",
                return_value={"status": "skipped", "reason": "no pending"},
            ):
                from data_pc_origin.p25_native_live import run_native_production_imap_once

                run_native_production_imap_once()
        self.assertFalse(mocked.called)


class TestLiveNativeProduction(unittest.TestCase):
    def test_prep_artifact(self) -> None:
        root = Path(__file__).resolve().parents[1]
        out = run_live_native_production(artifact_dir=root)
        self.assertIn(out["status"], ("ok", "partial"))
        self.assertTrue(validate_native_live_artifact(out))
        data = json.loads((root / ARTIFACT_NAME).read_text(encoding="utf-8"))
        self.assertTrue(data["prep"]["skip_origin"] is False)

    def test_live_gate(self) -> None:
        out = run_live_native_production(live=True)
        self.assertEqual(out["status"], "skipped")


if __name__ == "__main__":
    unittest.main()
