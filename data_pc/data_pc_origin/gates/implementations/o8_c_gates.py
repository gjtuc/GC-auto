# -*- coding: utf-8 -*-
"""O8-C L4 gate bodies."""

from __future__ import annotations

import dataclasses

from data_pc_origin.gates.registry import O8_DEPS, register_gate
from data_pc_origin.o0_mapping import DEFAULT_ORIGIN_MAPPING
from data_pc_origin.o8_context import SampleContext, build_context
from data_pc_origin.o8_fixtures import OPJU_FX, SAMPLE_JOB, fx_job_df_partial


def _assert(condition: bool, msg: str = "") -> None:
    if not condition:
        raise AssertionError(msg or "assertion failed")


def _gate_o8_c_01_a_1() -> None:
    ctx = SampleContext(
        opju_path=OPJU_FX,
        df=fx_job_df_partial(),
        sample_name=SAMPLE_JOB,
        identity_key=None,
        mapping=dict(DEFAULT_ORIGIN_MAPPING),
        save_in_place=True,
    )
    _assert(dataclasses.is_dataclass(ctx))
    _assert(ctx.opju_path == OPJU_FX)
    _assert(ctx.sample_name == SAMPLE_JOB)
    _assert(ctx.save_in_place is True)


def _gate_o8_c_02_a_1() -> None:
    df = fx_job_df_partial()
    ctx = build_context(OPJU_FX, df, SAMPLE_JOB)
    _assert(len(ctx.mapping) == 3)
    _assert("H2 Yield (%)" in ctx.mapping)
    _assert("C2H6 Conversion (%)" in ctx.mapping)


_O8_C_GATES: list[tuple[str, object]] = [
    ("O8-C-01-a-1", _gate_o8_c_01_a_1),
    ("O8-C-02-a-1", _gate_o8_c_02_a_1),
]


def register_o8_c_gates() -> None:
    for gate_id, fn in _O8_C_GATES:
        register_gate(gate_id, fn, depends=O8_DEPS[gate_id], layer="O8")  # type: ignore[arg-type]
