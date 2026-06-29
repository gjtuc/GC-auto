# -*- coding: utf-8
"""O9-F L4 gate bodies."""

from __future__ import annotations

import inspect
from unittest import mock

from data_pc_origin.gates.registry import O9_DEPS, register_gate
from data_pc_origin.o9_facade import (
    LOG_PREFIX,
    OriginUpdateResult,
    facade_signature_param_names,
    origin_log,
    update_from_dataframe,
)
from data_pc_origin.o8_fixtures import OPJU_FX, SAMPLE_JOB, fx_job_df_full, fx_job_op_full


def _assert(condition: bool, msg: str = "") -> None:
    if not condition:
        raise AssertionError(msg or "assertion failed")


def _gate_o9_f_01_a_1() -> None:
    names = facade_signature_param_names()
    _assert(names[:4] == ("opju_path", "df_data", "sample_name", "save_in_place"))
    _assert("identity_key" in names)
    sig = inspect.signature(update_from_dataframe)
    _assert(sig.parameters["save_in_place"].default is True)
    _assert(sig.parameters["identity_key"].default is None)


def _gate_o9_f_02_a_1() -> None:
    op, _ = fx_job_op_full()
    with mock.patch(
        "data_pc_origin.o9_facade.run_sample_job",
        wraps=__import__("data_pc_origin.o8_job", fromlist=["run_sample_job"]).run_sample_job,
    ) as spy:
        update_from_dataframe(
            OPJU_FX,
            fx_job_df_full(),
            SAMPLE_JOB,
            op=op,
            skip_gate=True,
            printer=lambda _m: None,
            log_fn=lambda _m: None,
        )
        _assert(spy.call_count == 1)


def _gate_o9_f_03_a_1() -> None:
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
    _assert(isinstance(res, OriginUpdateResult))
    _assert(res.sheets_updated == 8)
    _assert(res.row_count == 107)
    _assert(res.ok is True)
    _assert(res.opju_path == OPJU_FX)


def _gate_o9_f_04_a_1() -> None:
    lines: list[str] = []
    origin_log("test message", log_fn=lines.append)
    _assert(len(lines) == 1)
    _assert(lines[0].startswith(LOG_PREFIX))


def _gate_o9_f_05_a_1() -> None:
    printed: list[str] = []
    op, _ = fx_job_op_full()
    update_from_dataframe(
        OPJU_FX,
        fx_job_df_full(),
        SAMPLE_JOB,
        op=op,
        skip_gate=True,
        printer=printed.append,
        log_fn=lambda _m: None,
    )
    text = "\n".join(printed)
    _assert("[4단계]" in text)
    _assert("Origin 워크시트" in text)
    _assert(SAMPLE_JOB in text)


_O9_F_GATES: list[tuple[str, object]] = [
    ("O9-F-01-a-1", _gate_o9_f_01_a_1),
    ("O9-F-02-a-1", _gate_o9_f_02_a_1),
    ("O9-F-03-a-1", _gate_o9_f_03_a_1),
    ("O9-F-04-a-1", _gate_o9_f_04_a_1),
    ("O9-F-05-a-1", _gate_o9_f_05_a_1),
]


def register_o9_f_gates() -> None:
    for gate_id, fn in _O9_F_GATES:
        register_gate(gate_id, fn, depends=O9_DEPS[gate_id], layer="O9")  # type: ignore[arg-type]
