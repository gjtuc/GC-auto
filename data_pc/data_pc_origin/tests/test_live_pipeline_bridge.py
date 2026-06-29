# -*- coding: utf-8 -*-
"""Phase 8 live_pipeline_bridge harness tests."""
from __future__ import annotations

import json
import unittest
from pathlib import Path

from data_pc_origin.live_pipeline_bridge import (
    ARTIFACT_NAME,
    plan_pipeline_bridge,
    run_live_pipeline_bridge,
    validate_pipeline_bridge_artifact,
    verify_catalyst_delegation,
)


class TestLivePipelineBridge(unittest.TestCase):
    def test_plan_ready(self) -> None:
        root = str(Path(__file__).resolve().parents[1].parent)
        plan = plan_pipeline_bridge(root)
        self.assertTrue(plan.ready, plan.reason)
        self.assertTrue(plan.delegates_to_bridge)
        self.assertIn("catalyst_script", plan.checks)

    def test_delegation_execution(self) -> None:
        """실행 검증 — 촉매 update_origin 이 run_origin_update 를 1회 호출."""
        out = verify_catalyst_delegation()
        self.assertTrue(out["ok"], out.get("reason"))
        self.assertEqual(out["sheets_updated"], 8)
        self.assertEqual(out.get("df_row_count"), 107)
        self.assertTrue(out.get("save_in_place"))

    def test_harness_writes_artifact(self) -> None:
        root = Path(__file__).resolve().parents[1]
        out = run_live_pipeline_bridge(artifact_dir=root, script_dir=str(root.parent))
        self.assertIn(out["status"], ("ok", "partial"))
        path = root / ARTIFACT_NAME
        self.assertTrue(path.is_file())
        data = json.loads(path.read_text(encoding="utf-8"))
        self.assertTrue(validate_pipeline_bridge_artifact(data), data)


if __name__ == "__main__":
    unittest.main()
