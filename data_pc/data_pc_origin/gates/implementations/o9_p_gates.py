# -*- coding: utf-8 -*-
"""O9-P pipeline L4 gate bodies."""

from __future__ import annotations

import sys
from unittest import mock

from data_pc_origin.gates.registry import O9_DEPS, register_gate
from data_pc_origin.o9_facade import OriginUpdateResult
from data_pc_origin.o8_fixtures import OPJU_FX, SAMPLE_JOB, fx_job_df_full, fx_job_op_full
from data_pc_origin.o8_save import resolve_save_path
from data_pc_origin.pipeline_bridge import ensure_import_path, run_origin_update


def _assert(condition: bool, msg: str = "") -> None:
    if not condition:
        raise AssertionError(msg or "assertion failed")


def _gate_o9_p_01_a_1() -> None:
    root = ensure_import_path()
    _assert((root / "data_pc_origin").is_dir())
    import data_pc_origin  # noqa: F401

    _assert("data_pc_origin" in sys.modules)


def _gate_o9_p_02_a_1() -> None:
    with mock.patch("data_pc_origin.pipeline_bridge.update_from_dataframe") as spy:
        spy.return_value = OriginUpdateResult(
            ok=True,
            sheets_updated=8,
            row_count=107,
            warnings=(),
            opju_path=OPJU_FX,
            sample_name=SAMPLE_JOB,
        )
        res = run_origin_update(
            OPJU_FX,
            fx_job_df_full(),
            SAMPLE_JOB,
        )
        _assert(spy.call_count == 1)
        _assert(res.sheets_updated == 8)


def _gate_o9_p_03_a_1() -> None:
    updated = OPJU_FX.replace(".opju", "_Updated.opju")
    _assert(resolve_save_path(OPJU_FX, False) == updated)
    op, _ = fx_job_op_full()
    from data_pc_origin.o8_context import build_context
    from data_pc_origin.o8_job import run_sample_job

    ctx = build_context(OPJU_FX, fx_job_df_full(), SAMPLE_JOB, save_in_place=False)
    job = run_sample_job(ctx, op=op, skip_gate=True)
    _assert(job.saved_path == updated)
    _assert(op.save_calls == [updated])


_O9_P_GATES: list[tuple[str, object]] = [
    ("O9-P-01-a-1", _gate_o9_p_01_a_1),
    ("O9-P-02-a-1", _gate_o9_p_02_a_1),
    ("O9-P-03-a-1", _gate_o9_p_03_a_1),
]


def register_o9_p_gates() -> None:
    for gate_id, fn in _O9_P_GATES:
        register_gate(gate_id, fn, depends=O9_DEPS[gate_id], layer="O9")  # type: ignore[arg-type]
