# -*- coding: utf-8 -*-
"""O6-F L4 gate bodies."""

from __future__ import annotations

from data_pc_origin.gates.registry import O6_DEPS, register_gate
from data_pc_origin.o6_find import find_column_by_identity, find_column_exact_comment
from data_pc_origin.o6_fixtures import (
    IDENTITY_KEY,
    SAMPLE_EXACT,
    fx_wks_exact_match,
    fx_wks_identity_match,
    fx_wks_three_dated,
)


def _assert(condition: bool, msg: str = "") -> None:
    if not condition:
        raise AssertionError(msg or "assertion failed")


def _gate_o6_f_01_a_1() -> None:
    wks = fx_wks_exact_match()
    _assert(find_column_exact_comment(wks, SAMPLE_EXACT) == 2)


def _gate_o6_f_01_b_1() -> None:
    wks = fx_wks_exact_match()
    _assert(find_column_exact_comment(wks, "nonexistent sample") is None)


def _gate_o6_f_02_a_1() -> None:
    wks = fx_wks_identity_match()
    _assert(find_column_by_identity(wks, IDENTITY_KEY) == 2)


def _gate_o6_f_02_b_1() -> None:
    wks = fx_wks_three_dated()
    _assert(find_column_by_identity(wks, IDENTITY_KEY) is None)
    _assert(find_column_by_identity(wks, None) is None)


_O6_F_GATES: list[tuple[str, object]] = [
    ("O6-F-01-a-1", _gate_o6_f_01_a_1),
    ("O6-F-01-b-1", _gate_o6_f_01_b_1),
    ("O6-F-02-a-1", _gate_o6_f_02_a_1),
    ("O6-F-02-b-1", _gate_o6_f_02_b_1),
]


def register_o6_f_gates() -> None:
    for gate_id, fn in _O6_F_GATES:
        register_gate(gate_id, fn, depends=O6_DEPS[gate_id], layer="O6")  # type: ignore[arg-type]
