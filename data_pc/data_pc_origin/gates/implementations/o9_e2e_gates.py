# -*- coding: utf-8
"""O9-E2E mock L4 gate bodies."""

from __future__ import annotations

from data_pc_origin.gates.registry import O9_DEPS, register_gate
from data_pc_origin.o7_fixtures import gc3_gap_series
from data_pc_origin.o8_fixtures import OPJU_FX, SAMPLE_JOB, fx_job_df_full, fx_job_op_full
from data_pc_origin.o9_facade import update_from_dataframe


def _assert(condition: bool, msg: str = "") -> None:
    if not condition:
        raise AssertionError(msg or "assertion failed")


def _gate_o9_e2e_01_a_1() -> None:
    """Mock Ni5 full job — 8 sheets via facade."""
    op, _ = fx_job_op_full()
    res = update_from_dataframe(
        OPJU_FX,
        fx_job_df_full(),
        SAMPLE_JOB,
        op=op,
        skip_gate=True,
        printer=lambda _m: None,
        log_fn=lambda _m: None,
    )
    _assert(res.ok and res.sheets_updated == 8)
    _assert("Ni5" in OPJU_FX or "Ni5" in res.opju_path)


def _gate_o9_e2e_02_a_1() -> None:
    """Gap NaN → '' in written column (O7-G via full stack)."""
    op, sheets = fx_job_op_full()
    df = fx_job_df_full()
    update_from_dataframe(
        OPJU_FX,
        df,
        SAMPLE_JOB,
        op=op,
        skip_gate=True,
        printer=lambda _m: None,
        log_fn=lambda _m: None,
    )
    h2 = next(s for s in sheets if s.name == "H2yield")
    _assert(len(h2.writes) >= 1)
    vals = h2.writes[0][1]
    _assert(len(vals) == 107)
    _assert(vals[99] == "")
    _assert(vals[100] == "")
    _assert(vals[99] != 0.0)
    _assert(vals == __import__("data_pc_origin.o7_policy", fromlist=["prepare_column_list"]).prepare_column_list(
        gc3_gap_series()
    ))


_O9_E2E_GATES: list[tuple[str, object]] = [
    ("O9-E2E-01-a-1", _gate_o9_e2e_01_a_1),
    ("O9-E2E-02-a-1", _gate_o9_e2e_02_a_1),
]


def register_o9_e2e_gates() -> None:
    for gate_id, fn in _O9_E2E_GATES:
        register_gate(gate_id, fn, depends=O9_DEPS[gate_id], layer="O9")  # type: ignore[arg-type]
