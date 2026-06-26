# -*- coding: utf-8 -*-
"""O7-W L4 gate bodies."""

from __future__ import annotations

from data_pc_origin.gates.registry import O7_DEPS, register_gate
from data_pc_origin.o0_mapping import DEFAULT_ORIGIN_MAPPING
from data_pc_origin.o0_series import GapPolicy
from data_pc_origin.o7_fixtures import SAMPLE_WRITE, MockWriteWks, fx_df_two_cols, gc3_gap_series
from data_pc_origin.o7_write import write_column, write_h2_column, write_mapping_columns


def _assert(condition: bool, msg: str = "") -> None:
    if not condition:
        raise AssertionError(msg or "assertion failed")


def _gate_o7_w_01_a_1() -> None:
    wks = MockWriteWks()
    col, vals, _ = write_column(wks, 2, [1.0, 2.0], SAMPLE_WRITE)
    _assert(col == 2)
    _assert(len(wks.writes) == 1)
    _assert(wks.writes[0][0] == 2)
    _assert(wks.writes[0][1] == vals)


def _gate_o7_w_01_b_1() -> None:
    wks = MockWriteWks()
    write_column(wks, 3, [1.0], SAMPLE_WRITE)
    _assert(wks.writes[0][2] == SAMPLE_WRITE)


def _gate_o7_w_02_a_1() -> None:
    wks = MockWriteWks()
    col, vals, _ = write_h2_column(wks, 2, gc3_gap_series(), SAMPLE_WRITE)
    _assert(col == 2)
    _assert(len(vals) == 107)


def _gate_o7_w_03_a_1() -> None:
    wks = MockWriteWks()
    df = fx_df_two_cols()
    recs = write_mapping_columns(wks, 2, df, DEFAULT_ORIGIN_MAPPING, SAMPLE_WRITE)
    _assert(len(recs) == 2)
    _assert(len(wks.writes) == 2)


_O7_W_GATES: list[tuple[str, object]] = [
    ("O7-W-01-a-1", _gate_o7_w_01_a_1),
    ("O7-W-01-b-1", _gate_o7_w_01_b_1),
    ("O7-W-02-a-1", _gate_o7_w_02_a_1),
    ("O7-W-03-a-1", _gate_o7_w_03_a_1),
]


def register_o7_w_gates() -> None:
    for gate_id, fn in _O7_W_GATES:
        register_gate(gate_id, fn, depends=O7_DEPS[gate_id], layer="O7")  # type: ignore[arg-type]
