# -*- coding: utf-8 -*-
"""O7-G L4 gate bodies — gap row invariants."""

from __future__ import annotations

from data_pc_origin.gates.registry import O7_DEPS, register_gate
from data_pc_origin.o0_series import GapPolicy
from data_pc_origin.o7_fixtures import SAMPLE_WRITE, MockWriteWks, gc3_gap_series
from data_pc_origin.o7_write import write_h2_column


def _assert(condition: bool, msg: str = "") -> None:
    if not condition:
        raise AssertionError(msg or "assertion failed")


def _gate_o7_g_01_a_1() -> None:
    wks = MockWriteWks()
    _, vals, _ = write_h2_column(
        wks,
        2,
        gc3_gap_series(),
        SAMPLE_WRITE,
        gap_policy=GapPolicy.AS_EMPTY,
    )
    _assert(vals[99] == "")
    _assert(vals[100] == "")


def _gate_o7_g_02_a_1() -> None:
    wks = MockWriteWks()
    _, vals, _ = write_h2_column(
        wks,
        2,
        gc3_gap_series(),
        SAMPLE_WRITE,
        gap_policy=GapPolicy.AS_EMPTY,
    )
    _assert(vals[99] != 0.0)
    _assert(vals[100] != 0.0)


_O7_G_GATES: list[tuple[str, object]] = [
    ("O7-G-01-a-1", _gate_o7_g_01_a_1),
    ("O7-G-02-a-1", _gate_o7_g_02_a_1),
]


def register_o7_g_gates() -> None:
    for gate_id, fn in _O7_G_GATES:
        register_gate(gate_id, fn, depends=O7_DEPS[gate_id], layer="O7")  # type: ignore[arg-type]
