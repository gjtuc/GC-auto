# -*- coding: utf-8 -*-
"""O6-G equipment-day 가드 — 실행 검증 (artifact + O9 경로)."""
from __future__ import annotations

import json
import unittest
from pathlib import Path

from data_pc_origin.live_equipment_day_guard import (
    ARTIFACT_NAME,
    run_live_equipment_day_guard,
)
from data_pc_origin.o8_fixtures import (
    OCM_NEW_SAME_DAY,
    OPJU_FX,
    fx_job_df_full,
    fx_job_op_equipment_day_guard,
)
from data_pc_origin.o9_facade import update_from_dataframe


class TestLiveEquipmentDayGuard(unittest.TestCase):
    def test_harness_all_scenarios_ready(self) -> None:
        root = Path(__file__).resolve().parents[1]
        out = run_live_equipment_day_guard(artifact_dir=root)
        self.assertTrue(out["ready"], out.get("reason"))
        self.assertTrue(out["artifact_valid"])
        path = root / ARTIFACT_NAME
        self.assertTrue(path.is_file())
        data = json.loads(path.read_text(encoding="utf-8"))
        self.assertEqual(data["status"], "ok")
        names = {s["name"] for s in data["scenarios"]}
        self.assertIn("same_date", names)
        self.assertIn("facade_writes_with_confirm", names)

    def test_o9_same_day_blocks_then_confirms(self) -> None:
        """실행 검증 — O9 facade 가 O6-G 를 O8 job 경로로 적용."""
        op, sheets = fx_job_op_equipment_day_guard()
        blocked = update_from_dataframe(
            OPJU_FX,
            fx_job_df_full(),
            OCM_NEW_SAME_DAY,
            op=op,
            skip_gate=True,
            skip_equipment_day_guard=False,
            column_guard_confirm=None,
            printer=lambda _m: None,
        )
        self.assertFalse(blocked.ok)
        self.assertTrue(
            any(w.code == "equipment_day_guard" for w in blocked.warnings),
        )
        self.assertEqual(len(sheets[0].writes), 0)

        op2, sheets2 = fx_job_op_equipment_day_guard()
        ok = update_from_dataframe(
            OPJU_FX,
            fx_job_df_full(),
            OCM_NEW_SAME_DAY,
            op=op2,
            skip_gate=True,
            skip_equipment_day_guard=False,
            column_guard_confirm=lambda _g: True,
            printer=lambda _m: None,
        )
        self.assertTrue(ok.ok)
        self.assertGreater(len(sheets2[0].writes), 0)


if __name__ == "__main__":
    unittest.main()
