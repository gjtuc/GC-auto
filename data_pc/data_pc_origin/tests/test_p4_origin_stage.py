# -*- coding: utf-8 -*-
import json
import unittest
from pathlib import Path

from data_pc_origin.o2_env import SKIP_ORIGIN_ENV
from data_pc_origin.o8_fixtures import OPJU_FX, SAMPLE_JOB, fx_job_df_full, fx_job_op_full
from data_pc_origin.o9_facade import update_from_dataframe
from data_pc_origin.p0_types import OriginJobPayload, WorkflowOptions
from data_pc_origin.p4_origin_stage import (
    bridge_kwargs_from_payload,
    maybe_run_stage4,
    run_stage4_origin,
)


def _mock_runner(payload: OriginJobPayload):
    op, _ = fx_job_op_full()
    return update_from_dataframe(
        payload.opju_path,
        payload.df,
        payload.sample_name,
        save_in_place=payload.save_in_place,
        identity_key=payload.identity_key,
        op=op,
        skip_gate=True,
        printer=lambda _m: None,
        log_fn=lambda _m: None,
    )


class TestP4OriginStage(unittest.TestCase):
    def _payload(self) -> OriginJobPayload:
        return OriginJobPayload(
            opju_path=OPJU_FX,
            sample_name=SAMPLE_JOB,
            identity_key=("20250601", "seed"),
            save_in_place=False,
            df=fx_job_df_full(),
        )

    def test_bridge_kwargs(self) -> None:
        kw = bridge_kwargs_from_payload(self._payload())
        self.assertEqual(kw["opju_path"], OPJU_FX)
        self.assertEqual(kw["sample_name"], SAMPLE_JOB)

    def test_mock_run_eight_sheets(self) -> None:
        res = run_stage4_origin(self._payload(), runner=_mock_runner)
        self.assertFalse(res.skipped)
        self.assertTrue(res.ok)
        self.assertIsNotNone(res.origin)
        assert res.origin is not None
        self.assertEqual(res.origin.sheets_updated, 8)

    def test_skip_env(self) -> None:
        res = maybe_run_stage4(
            self._payload(),
            environ={SKIP_ORIGIN_ENV: "1"},
        )
        self.assertTrue(res.skipped)
        self.assertIsNone(res.origin)

    def test_write_p4_smoke_artifact(self) -> None:
        payload = self._payload()
        executed = run_stage4_origin(payload, runner=_mock_runner)
        skipped = maybe_run_stage4(
            payload,
            options=WorkflowOptions(skip_stage4=True),
        )
        out = {
            "bridge_hook": "run_origin_update",
            "sheets_updated": executed.origin.sheets_updated if executed.origin else 0,
            "save_in_place": payload.save_in_place,
            "skipped_ok": skipped.ok,
            "skip_reason_nonempty": bool(skipped.skip_reason),
        }
        path = Path(__file__).resolve().parents[1] / "p4_origin_smoke.json"
        path.write_text(json.dumps(out, indent=2, ensure_ascii=False), encoding="utf-8")
        self.assertEqual(out["sheets_updated"], 8)
        self.assertTrue(out["skipped_ok"])
        self.assertTrue(out["skip_reason_nonempty"])


if __name__ == "__main__":
    unittest.main()
