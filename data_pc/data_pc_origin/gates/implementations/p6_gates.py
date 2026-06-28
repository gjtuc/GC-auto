# -*- coding: utf-8
"""P6 L4 gate bodies — importlib mock adapter."""

from __future__ import annotations

from pathlib import Path

from data_pc_origin.gates.registry import P6_DEPS, register_gate
from data_pc_origin.o8_fixtures import OPJU_FX, fx_job_op_full
from data_pc_origin.o9_facade import update_from_dataframe
from data_pc_origin.p0_types import WorkflowMode, WorkflowOptions
from data_pc_origin.p6_catalyst_adapter import (
    CatalystLoadError,
    default_catalyst_path,
    load_catalyst_module,
    make_stage2_runner,
    make_stage3_runner,
    run_workflow_with_catalyst,
)

_FIXTURE = (
    Path(__file__).resolve().parents[2]
    / "tests"
    / "fixtures"
    / "catalyst_mock_module.py"
)


def _assert(condition: bool, msg: str = "") -> None:
    if not condition:
        raise AssertionError(msg or "assertion failed")


def _mock_origin(payload):
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


def _gate_p6_a_01_a_1() -> None:
    p = default_catalyst_path()
    _assert(p.name.endswith(".py"))
    _assert(p.is_file())


def _gate_p6_a_02_a_1() -> None:
    mod = load_catalyst_module(_FIXTURE)
    _assert(hasattr(mod, "process_excel"))


def _gate_p6_a_03_a_1() -> None:
    mod = load_catalyst_module(_FIXTURE)
    s2 = make_stage2_runner(mod)(r"G:\in.xlsx")
    _assert(s2 is not None)
    _assert("mock" in s2.metadata.sample_name)


def _gate_p6_a_04_a_1() -> None:
    mod = load_catalyst_module(_FIXTURE)
    s2 = make_stage2_runner(mod)(r"G:\in.xlsx")
    assert s2 is not None
    s3 = make_stage3_runner(mod)(r"G:\in.xlsx", s2)
    _assert(s3 is not None and s3.target_opju.endswith(".opju"))


def _gate_p6_a_05_a_1() -> None:
    mod = load_catalyst_module(_FIXTURE)
    res = run_workflow_with_catalyst(
        r"G:\in.xlsx",
        WorkflowOptions(),
        module=mod,
        origin_runner=_mock_origin,
    )
    _assert(res.ok is True)
    _assert(res.mode == WorkflowMode.FULL_ARCHIVE)
    assert res.stage4 is not None and res.stage4.origin is not None
    _assert(res.stage4.origin.sheets_updated == 8)


def _gate_p6_r_01_a_1() -> None:
    try:
        load_catalyst_module(Path(r"G:\no_such_catalyst.py"))
        _assert(False, "expected CatalystLoadError")
    except CatalystLoadError:
        pass


def _gate_p6_r_02_a_1() -> None:
    mod = load_catalyst_module(_FIXTURE)
    s2 = make_stage2_runner(mod)(r"G:\in_fail.xlsx")
    _assert(s2 is None)


def _gate_p6_r_03_a_1() -> None:
    mod = load_catalyst_module(_FIXTURE)
    res = run_workflow_with_catalyst(
        r"G:\in.xlsx",
        WorkflowOptions(opju_path=OPJU_FX),
        module=mod,
        origin_runner=_mock_origin,
    )
    _assert(res.ok is True)
    _assert(res.mode == WorkflowMode.OPJU_ONLY)


_P6_GATES: list[tuple[str, object]] = [
    ("P6-A-01-a-1", _gate_p6_a_01_a_1),
    ("P6-A-02-a-1", _gate_p6_a_02_a_1),
    ("P6-A-03-a-1", _gate_p6_a_03_a_1),
    ("P6-A-04-a-1", _gate_p6_a_04_a_1),
    ("P6-A-05-a-1", _gate_p6_a_05_a_1),
    ("P6-R-01-a-1", _gate_p6_r_01_a_1),
    ("P6-R-02-a-1", _gate_p6_r_02_a_1),
    ("P6-R-03-a-1", _gate_p6_r_03_a_1),
]


def register_p6_gates() -> None:
    for gate_id, fn in _P6_GATES:
        register_gate(gate_id, fn, depends=P6_DEPS[gate_id], layer="P6")  # type: ignore[arg-type]
