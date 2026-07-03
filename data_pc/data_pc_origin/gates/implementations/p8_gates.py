# -*- coding: utf-8
"""P8-B workflow bridge L4 gate bodies."""

from __future__ import annotations

import tempfile
from pathlib import Path

from data_pc_origin.gates.registry import P8_DEPS, register_gate
from data_pc_origin.o8_fixtures import OPJU_FX, fx_job_op_full
from data_pc_origin.o9_facade import OriginUpdateResult, update_from_dataframe
from data_pc_origin.p0_types import WorkflowMode
from data_pc_origin.workflow_bridge import (
    build_workflow_options,
    run_workflow_bridged,
)

_FIXTURE = (
    Path(__file__).resolve().parents[2]
    / "tests"
    / "fixtures"
    / "catalyst_mock_module.py"
)
_LOG: list[str] = []


def _assert(condition: bool, msg: str = "") -> None:
    if not condition:
        raise AssertionError(msg or "assertion failed")


def _printer(msg: str) -> None:
    _LOG.append(msg)


def _load_fixture():
    from data_pc_origin.p6_catalyst_adapter import load_catalyst_module

    return load_catalyst_module(_FIXTURE)


def _mock_origin(payload) -> OriginUpdateResult:
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


def _temp_xlsx() -> str:
    fd, path = tempfile.mkstemp(suffix=".xlsx")
    import os

    os.close(fd)
    return path


def _gate_p8_b_01_a_1() -> None:
    opts = build_workflow_options(opju_path=OPJU_FX, auto_archive=False)
    _assert(opts.opju_path == OPJU_FX)
    _assert(opts.auto_archive is False)


def _gate_p8_b_02_a_1() -> None:
    mod = _load_fixture()
    xlsx = _temp_xlsx()
    try:
        ok = run_workflow_bridged(
            xlsx,
            auto_archive=False,
            catalyst_module=mod,
            origin_runner=_mock_origin,
            printer=_printer,
        )
        _assert(ok is True)
    finally:
        Path(xlsx).unlink(missing_ok=True)


def _gate_p8_b_03_a_1() -> None:
    mod = _load_fixture()
    ok = run_workflow_bridged(
        r"G:\no_such_file.xlsx",
        catalyst_module=mod,
        printer=_printer,
    )
    _assert(ok is False)


def _gate_p8_b_04_a_1() -> None:
    global _LOG
    _LOG = []
    mod = _load_fixture()
    xlsx = _temp_xlsx()
    fd, opju = tempfile.mkstemp(suffix=".opju")
    import os

    os.close(fd)
    try:
        ok = run_workflow_bridged(
            xlsx,
            opju_path=opju,
            skip_origin=True,
            catalyst_module=mod,
            origin_runner=_mock_origin,
            printer=_printer,
        )
        _assert(ok is True)
        joined = "\n".join(_LOG)
        _assert("Origin" in joined or "건너뜀" in joined)
    finally:
        Path(xlsx).unlink(missing_ok=True)
        Path(opju).unlink(missing_ok=True)


_P8_GATES: list[tuple[str, object]] = [
    ("P8-B-01-a-1", _gate_p8_b_01_a_1),
    ("P8-B-02-a-1", _gate_p8_b_02_a_1),
    ("P8-B-03-a-1", _gate_p8_b_03_a_1),
    ("P8-B-04-a-1", _gate_p8_b_04_a_1),
]


def register_p8_gates() -> None:
    for gate_id, fn in _P8_GATES:
        register_gate(gate_id, fn, depends=P8_DEPS[gate_id], layer="P8")  # type: ignore[arg-type]
