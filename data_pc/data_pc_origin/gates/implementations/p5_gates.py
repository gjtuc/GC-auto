# -*- coding: utf-8
"""P5 L4 gate bodies — route×skip mock workflow."""

from __future__ import annotations

from data_pc_origin.gates.registry import P5_DEPS, register_gate
from data_pc_origin.o8_fixtures import OPJU_FX, SAMPLE_JOB, fx_job_df_full, fx_job_op_full
from data_pc_origin.o9_facade import OriginUpdateResult, update_from_dataframe
from data_pc_origin.p0_types import Stage2Artifacts, WorkflowMode, WorkflowOptions
from data_pc_origin.p1_payload import Stage2Metadata, assemble_stage2_metadata
from data_pc_origin.p4_origin_stage import OriginRunner
from data_pc_origin.p5_workflow import (
    Stage2RunResult,
    Stage3Result,
    build_workflow_payload,
    plan_workflow_stages,
    run_workflow_stages,
)


def _assert(condition: bool, msg: str = "") -> None:
    if not condition:
        raise AssertionError(msg or "assertion failed")


def _fx_stage2() -> Stage2RunResult:
    art = Stage2Artifacts(fx_job_df_full(), r"G:\calc.xlsx")
    meta = assemble_stage2_metadata(
        sample_name=SAMPLE_JOB,
        identity_key=("20250601", "seed"),
        saved_excel=r"G:\calc.xlsx",
    )
    return Stage2RunResult(artifacts=art, metadata=meta)


def _mock_origin_runner() -> OriginRunner:
    def _run(payload):
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

    return _run


def _gate_p5_w_01_a_1() -> None:
    _assert(plan_workflow_stages(WorkflowMode.OPJU_ONLY) == (2, 4))


def _gate_p5_w_02_a_1() -> None:
    _assert(plan_workflow_stages(WorkflowMode.CALC_ONLY) == (2,))


def _gate_p5_w_03_a_1() -> None:
    _assert(plan_workflow_stages(WorkflowMode.FULL_ARCHIVE) == (2, 3, 4))


def _gate_p5_w_04_a_1() -> None:
    opts = WorkflowOptions(opju_path=OPJU_FX)
    res = run_workflow_stages(
        r"G:\in.xlsx",
        opts,
        stage2_runner=lambda _p: _fx_stage2(),
        origin_runner=_mock_origin_runner(),
    )
    _assert(res.ok is True)
    _assert(res.mode == WorkflowMode.OPJU_ONLY)
    _assert(res.stage3 is None)
    _assert(res.stage4 is not None and res.stage4.origin is not None)
    _assert(res.stage4.origin.sheets_updated == 8)


def _gate_p5_w_05_a_1() -> None:
    opts = WorkflowOptions(skip_stage4=True)
    res = run_workflow_stages(
        r"G:\in.xlsx",
        opts,
        stage2_runner=lambda _p: _fx_stage2(),
        stage3_runner=lambda _p, _s: Stage3Result(
            target_opju=OPJU_FX,
            archive_xlsx=r"G:\archive.xlsx",
        ),
    )
    _assert(res.ok is True)
    _assert(res.mode == WorkflowMode.FULL_ARCHIVE)
    _assert(res.stage4 is not None and res.stage4.skipped is True)


def _gate_p5_p_01_a_1() -> None:
    s2 = _fx_stage2()
    opju = build_workflow_payload(
        s2, opju_path=OPJU_FX, mode=WorkflowMode.OPJU_ONLY
    )
    full = build_workflow_payload(
        s2, opju_path=OPJU_FX, mode=WorkflowMode.FULL_ARCHIVE
    )
    _assert(opju.save_in_place is False)
    _assert(full.save_in_place is True)


def _gate_p5_r_01_a_1() -> None:
    opts = WorkflowOptions(auto_archive=False)
    res = run_workflow_stages(
        r"G:\in.xlsx",
        opts,
        stage2_runner=lambda _p: _fx_stage2(),
    )
    _assert(res.ok is True)
    _assert(res.mode == WorkflowMode.CALC_ONLY)
    _assert(res.stage3 is None and res.stage4 is None)


def _gate_p5_r_02_a_1() -> None:
    res = run_workflow_stages(
        r"G:\in.xlsx",
        WorkflowOptions(),
        stage2_runner=lambda _p: None,
    )
    _assert(res.ok is False)
    _assert(res.stage2 is None)


def _gate_p5_r_03_a_1() -> None:
    def fail(_payload) -> OriginUpdateResult:
        return OriginUpdateResult(
            ok=False,
            sheets_updated=0,
            row_count=0,
            warnings=(),
            opju_path=OPJU_FX,
            sample_name=SAMPLE_JOB,
        )

    res = run_workflow_stages(
        r"G:\in.xlsx",
        WorkflowOptions(opju_path=OPJU_FX),
        stage2_runner=lambda _p: _fx_stage2(),
        origin_runner=fail,
    )
    _assert(res.ok is False)
    _assert(res.stage4 is not None and res.stage4.ok is False)


_P5_GATES: list[tuple[str, object]] = [
    ("P5-W-01-a-1", _gate_p5_w_01_a_1),
    ("P5-W-02-a-1", _gate_p5_w_02_a_1),
    ("P5-W-03-a-1", _gate_p5_w_03_a_1),
    ("P5-W-04-a-1", _gate_p5_w_04_a_1),
    ("P5-W-05-a-1", _gate_p5_w_05_a_1),
    ("P5-P-01-a-1", _gate_p5_p_01_a_1),
    ("P5-R-01-a-1", _gate_p5_r_01_a_1),
    ("P5-R-02-a-1", _gate_p5_r_02_a_1),
    ("P5-R-03-a-1", _gate_p5_r_03_a_1),
]


def register_p5_gates() -> None:
    for gate_id, fn in _P5_GATES:
        register_gate(gate_id, fn, depends=P5_DEPS[gate_id], layer="P5")  # type: ignore[arg-type]
