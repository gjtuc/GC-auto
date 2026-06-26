# -*- coding: utf-8 -*-
"""O6-P L4 gate bodies."""

from __future__ import annotations

from data_pc_origin.gates.registry import O6_DEPS, register_gate
from data_pc_origin.o6_fixtures import SAMPLE_NEW, fx_wks_insert_plan, fx_wks_mixed_dated
from data_pc_origin.o6_plan import (
    column_comment_nonempty,
    needs_column_insert,
    plan_insert_index,
    sample_sort_date,
)
from data_pc_origin.o6_scan import dated_columns


def _assert(condition: bool, msg: str = "") -> None:
    if not condition:
        raise AssertionError(msg or "assertion failed")


def _gate_o6_p_01_a_1() -> None:
    _assert(sample_sort_date(SAMPLE_NEW) == "20250610")
    _assert(sample_sort_date("no date") is None)


def _gate_o6_p_02_a_1() -> None:
    dated = dated_columns(fx_wks_insert_plan())
    _assert(plan_insert_index(dated, "20250610") == 2)


def _gate_o6_p_03_a_1() -> None:
    dated = dated_columns(fx_wks_insert_plan())
    _assert(plan_insert_index(dated, None) == 4)
    _assert(plan_insert_index([], None) == 1)


def _gate_o6_p_04_a_1() -> None:
    wks = fx_wks_mixed_dated()
    _assert(column_comment_nonempty(wks, 1) is True)
    _assert(column_comment_nonempty(wks, 2) is False)
    _assert(needs_column_insert(wks, 2) is False)
    _assert(needs_column_insert(wks, 3) is True)


_O6_P_GATES: list[tuple[str, object]] = [
    ("O6-P-01-a-1", _gate_o6_p_01_a_1),
    ("O6-P-02-a-1", _gate_o6_p_02_a_1),
    ("O6-P-03-a-1", _gate_o6_p_03_a_1),
    ("O6-P-04-a-1", _gate_o6_p_04_a_1),
]


def register_o6_p_gates() -> None:
    for gate_id, fn in _O6_P_GATES:
        register_gate(gate_id, fn, depends=O6_DEPS[gate_id], layer="O6")  # type: ignore[arg-type]
