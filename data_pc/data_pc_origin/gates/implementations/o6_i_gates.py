# -*- coding: utf-8 -*-
"""O6-I L4 gate bodies."""

from __future__ import annotations

from data_pc_origin.gates.registry import O6_DEPS, register_gate
from data_pc_origin.o6_fixtures import fx_wks_mixed_dated, fx_wks_three_dated
from data_pc_origin.o6_insert import (
    build_insert_lt_command,
    insert_column_before,
    insert_column_if_needed,
)


def _assert(condition: bool, msg: str = "") -> None:
    if not condition:
        raise AssertionError(msg or "assertion failed")


def _gate_o6_i_01_a_1() -> None:
    wks = fx_wks_three_dated()
    calls: list[str] = []

    def _lt(cmd: str) -> None:
        calls.append(cmd)

    cmd = insert_column_before(wks, 2, lt_execute=_lt)
    _assert("GCData" in cmd)
    _assert(".insert(GCData)" in cmd)
    _assert(cmd == build_insert_lt_command(wks, 2))
    _assert(len(calls) == 1)


def _gate_o6_i_01_b_1() -> None:
    wks = fx_wks_three_dated()
    cmd = build_insert_lt_command(wks, 2)
    _assert("[Book1]Sheet1!.col=3" in cmd.replace(" ", ""))
    _assert("page.xlcolname=0" in cmd)


def _gate_o6_i_02_a_1() -> None:
    wks = fx_wks_mixed_dated()
    calls: list[str] = []

    def _lt(cmd: str) -> None:
        calls.append(cmd)

    _assert(insert_column_if_needed(wks, 2, lt_execute=_lt) is None)
    _assert(len(calls) == 0)
    out = insert_column_if_needed(wks, 3, lt_execute=_lt)
    _assert(out is not None and "GCData" in out)
    _assert(len(calls) == 1)


def _gate_o6_i_02_b_1() -> None:
    wks = fx_wks_three_dated()
    calls: list[str] = []
    insert_column_if_needed(wks, 4, lt_execute=calls.append)
    _assert(calls == [])


_O6_I_GATES: list[tuple[str, object]] = [
    ("O6-I-01-a-1", _gate_o6_i_01_a_1),
    ("O6-I-01-b-1", _gate_o6_i_01_b_1),
    ("O6-I-02-a-1", _gate_o6_i_02_a_1),
    ("O6-I-02-b-1", _gate_o6_i_02_b_1),
]


def register_o6_i_gates() -> None:
    for gate_id, fn in _O6_I_GATES:
        register_gate(gate_id, fn, depends=O6_DEPS[gate_id], layer="O6")  # type: ignore[arg-type]
