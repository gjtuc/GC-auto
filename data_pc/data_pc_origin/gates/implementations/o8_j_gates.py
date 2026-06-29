# -*- coding: utf-8 -*-
"""O8-J L4 gate bodies."""

from __future__ import annotations

from types import ModuleType

from data_pc_origin.gates.registry import O8_DEPS, register_gate
from data_pc_origin.o0_types import ProbeResult
from data_pc_origin.o2_gate_chain import GateVerdict
from data_pc_origin.o3_session import OriginSession
from data_pc_origin.o8_context import build_context
from data_pc_origin.o8_fixtures import (
    OPJU_FX,
    SAMPLE_JOB,
    fx_job_df_full,
    fx_job_df_partial,
    fx_job_op_full,
    fx_job_op_partial,
)
from data_pc_origin.o8_job import require_origin_ready, run_sample_job


def _assert(condition: bool, msg: str = "") -> None:
    if not condition:
        raise AssertionError(msg or "assertion failed")


def _ready_gate(**kwargs) -> GateVerdict:
    return GateVerdict(code="ready", detail="mock")


def _skip_gate(**kwargs) -> GateVerdict:
    return GateVerdict(code="skip_origin", detail="skip")


def _gate_o8_j_01_a_1() -> None:
    v = require_origin_ready(
        opju_probe=ProbeResult(ok=True),
        skip_origin=False,
        gate_fn=_ready_gate,
    )
    _assert(v.code == "ready")
    v2 = require_origin_ready(
        opju_probe=ProbeResult(ok=True),
        skip_origin=False,
        gate_fn=_skip_gate,
    )
    _assert(v2.code == "skip_origin")


def _gate_o8_j_02_a_1() -> None:
    op, _ = fx_job_op_full()
    exited: list[str] = []

    class _Wrap:
        def set_show(self, v: bool) -> None:
            pass

        def oext(self, v: bool) -> None:
            pass

        def exit(self) -> None:
            exited.append("exit")

    def _import() -> ModuleType:
        return _Wrap()  # type: ignore[return-value]

    with OriginSession(importer=_import) as _op:
        pass
    _assert(exited == ["exit"])


def _gate_o8_j_03_a_1() -> None:
    op, _ = fx_job_op_full()
    ctx = build_context(OPJU_FX, fx_job_df_partial(), SAMPLE_JOB)
    run_sample_job(ctx, op=op, skip_gate=True)
    _assert(op.open_calls == [OPJU_FX])


def _gate_o8_j_04_a_1() -> None:
    op, sheets = fx_job_op_partial()
    ctx = build_context(OPJU_FX, fx_job_df_partial(), SAMPLE_JOB)
    run_sample_job(ctx, op=op, skip_gate=True)
    cols = {w[0] for s in sheets for w in s.writes}
    _assert(len(cols) == 1)


def _gate_o8_j_05_a_1() -> None:
    op, _ = fx_job_op_full()
    ctx = build_context(OPJU_FX, fx_job_df_full(), SAMPLE_JOB)
    res = run_sample_job(ctx, op=op, skip_gate=True)
    _assert(res.updated_count == 8)


def _gate_o8_j_06_a_1() -> None:
    op, _ = fx_job_op_full()
    ctx = build_context(OPJU_FX, fx_job_df_full(), SAMPLE_JOB, save_in_place=True)
    run_sample_job(ctx, op=op, skip_gate=True)
    _assert(op.save_calls == [OPJU_FX])


def _gate_o8_j_07_a_1() -> None:
    op, _ = fx_job_op_partial()
    ctx = build_context(OPJU_FX, fx_job_df_partial(), SAMPLE_JOB)
    res = run_sample_job(ctx, op=op, skip_gate=True)
    _assert(res.updated_count == 2)
    _assert(len(res.warnings) >= 1)
    _assert(res.warnings[0].code == "WKS_MISS")
    _assert(res.ok is True)


def _gate_o8_j_08_a_1() -> None:
    op, _ = fx_job_op_full()
    ctx = build_context(OPJU_FX, fx_job_df_full(), SAMPLE_JOB)
    res = run_sample_job(ctx, op=op, skip_gate=True)
    _assert(res.updated_count == 8)
    _assert(res.row_count == 107)
    _assert(res.col_idx is not None)


def _gate_o8_j_09_a_1() -> None:
    op, _ = fx_job_op_full()
    ctx = build_context(OPJU_FX, fx_job_df_partial(), SAMPLE_JOB)
    empty_df = fx_job_df_partial()
    empty_df.columns = []
    empty_df._data = {}  # type: ignore[attr-defined]
    ctx_empty = build_context(OPJU_FX, empty_df, SAMPLE_JOB)
    run_sample_job(ctx_empty, op=op, skip_gate=True)
    _assert(op.exit_calls == ["exit"])


_O8_J_GATES: list[tuple[str, object]] = [
    ("O8-J-01-a-1", _gate_o8_j_01_a_1),
    ("O8-J-02-a-1", _gate_o8_j_02_a_1),
    ("O8-J-03-a-1", _gate_o8_j_03_a_1),
    ("O8-J-04-a-1", _gate_o8_j_04_a_1),
    ("O8-J-05-a-1", _gate_o8_j_05_a_1),
    ("O8-J-06-a-1", _gate_o8_j_06_a_1),
    ("O8-J-07-a-1", _gate_o8_j_07_a_1),
    ("O8-J-08-a-1", _gate_o8_j_08_a_1),
    ("O8-J-09-a-1", _gate_o8_j_09_a_1),
]


def register_o8_j_gates() -> None:
    for gate_id, fn in _O8_J_GATES:
        register_gate(gate_id, fn, depends=O8_DEPS[gate_id], layer="O8")  # type: ignore[arg-type]
