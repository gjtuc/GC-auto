# -*- coding: utf-8 -*-
"""Phase 8 #154 live_phase8_origin harness tests."""
from __future__ import annotations

import json
import unittest
from pathlib import Path

from data_pc_origin.live_phase8_origin import (
    ARTIFACT_NAME,
    plan_phase8_origin,
    run_live_phase8_origin,
    validate_phase8_origin_artifact,
    verify_fixture_o9_e2e,
    verify_pipeline_bridge_fixture,
)
from data_pc_origin.tests._helpers import without_skip_origin


class TestLivePhase8Origin(unittest.TestCase):
    def test_plan_ready(self) -> None:
        with without_skip_origin():
            plan = plan_phase8_origin()
        self.assertTrue(plan.ready, plan.reason)
        self.assertTrue(plan.origin_feature_enabled)
        self.assertFalse(plan.catalyst_skip_origin)
        self.assertIn("o2_origin_feature_enabled", plan.checks)

    def test_fixture_o9_execution(self) -> None:
        """실행 검증 — mock op 8 sheets."""
        out = verify_fixture_o9_e2e()
        self.assertTrue(out["ok"], out.get("reason"))
        self.assertEqual(out["sheets_updated"], 8)
        self.assertEqual(out["row_count"], 107)

    def test_bridge_fixture_execution(self) -> None:
        out = verify_pipeline_bridge_fixture()
        self.assertTrue(out["ok"], out.get("reason"))
        self.assertGreaterEqual(out["sheets_updated"], 8)

    def test_harness_writes_artifact(self) -> None:
        root = Path(__file__).resolve().parents[1]
        out = run_live_phase8_origin(artifact_dir=root)
        self.assertIn(out["status"], ("ok", "partial"))
        self.assertEqual(out["live_tier"], "fixture_only")
        path = root / ARTIFACT_NAME
        self.assertTrue(path.is_file())
        data = json.loads(path.read_text(encoding="utf-8"))
        self.assertTrue(validate_phase8_origin_artifact(data), data)


if __name__ == "__main__":
    unittest.main()
