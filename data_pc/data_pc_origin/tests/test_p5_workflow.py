# -*- coding: utf-8
import json
import unittest
from pathlib import Path

from data_pc_origin.o8_fixtures import OPJU_FX, SAMPLE_JOB, fx_job_df_full, fx_job_op_full
from data_pc_origin.o9_facade import update_from_dataframe
from data_pc_origin.p0_types import Stage2Artifacts, WorkflowMode, WorkflowOptions
from data_pc_origin.p1_payload import assemble_stage2_metadata
from data_pc_origin.p5_workflow import (
    Stage2RunResult,
    Stage3Result,
    plan_workflow_stages,
    run_workflow_stages,
)
from data_pc_origin.tests._helpers import WORKFLOW_TEST_ENV, without_skip_origin


def _fx_stage2() -> Stage2RunResult:
    art = Stage2Artifacts(fx_job_df_full(), r"G:\calc.xlsx")
    meta = assemble_stage2_metadata(
        sample_name=SAMPLE_JOB,
        identity_key=("20250601", "seed"),
        saved_excel=r"G:\calc.xlsx",
    )
    return Stage2RunResult(artifacts=art, metadata=meta)


def _mock_origin_runner(payload):
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


class TestP5Workflow(unittest.TestCase):
    def test_plan_modes(self) -> None:
        self.assertEqual(plan_workflow_stages(WorkflowMode.CALC_ONLY), (2,))
        self.assertEqual(plan_workflow_stages(WorkflowMode.OPJU_ONLY), (2, 4))
        self.assertEqual(plan_workflow_stages(WorkflowMode.FULL_ARCHIVE), (2, 3, 4))

    def test_full_archive_mock(self) -> None:
        res = run_workflow_stages(
            r"G:\in.xlsx",
            WorkflowOptions(),
            stage2_runner=lambda _p: _fx_stage2(),
            stage3_runner=lambda _p, _s: Stage3Result(
                target_opju=OPJU_FX,
                archive_xlsx=r"G:\archive.xlsx",
            ),
            origin_runner=_mock_origin_runner,
            explicit_skip=False,
            environ=WORKFLOW_TEST_ENV,
        )
        self.assertTrue(res.ok)
        self.assertEqual(res.mode, WorkflowMode.FULL_ARCHIVE)
        assert res.stage4 is not None and res.stage4.origin is not None
        self.assertEqual(res.stage4.origin.sheets_updated, 8)

    def test_write_p5_smoke_artifact(self) -> None:
        opju = run_workflow_stages(
            r"G:\in.xlsx",
            WorkflowOptions(opju_path=OPJU_FX),
            stage2_runner=lambda _p: _fx_stage2(),
            origin_runner=_mock_origin_runner,
            explicit_skip=False,
            environ=WORKFLOW_TEST_ENV,
        )
        calc = run_workflow_stages(
            r"G:\in.xlsx",
            WorkflowOptions(auto_archive=False),
            stage2_runner=lambda _p: _fx_stage2(),
            explicit_skip=False,
            environ=WORKFLOW_TEST_ENV,
        )
        out = {
            "opju_only_ok": opju.ok,
            "opju_only_sheets": (
                opju.stage4.origin.sheets_updated
                if opju.stage4 and opju.stage4.origin
                else 0
            ),
            "calc_only_ok": calc.ok,
            "calc_only_no_stage4": calc.stage4 is None,
            "full_plan": list(plan_workflow_stages(WorkflowMode.FULL_ARCHIVE)),
        }
        path = Path(__file__).resolve().parents[1] / "p5_workflow_smoke.json"
        path.write_text(json.dumps(out, indent=2, ensure_ascii=False), encoding="utf-8")
        self.assertTrue(out["opju_only_ok"])
        self.assertEqual(out["opju_only_sheets"], 8)
        self.assertTrue(out["calc_only_ok"])
        self.assertTrue(out["calc_only_no_stage4"])
        self.assertEqual(out["full_plan"], [2, 3, 4])


if __name__ == "__main__":
    unittest.main()
