# -*- coding: utf-8 -*-
"""O7-P L4 gate bodies."""

from __future__ import annotations

from data_pc_origin.gates.registry import O7_DEPS, register_gate
from data_pc_origin.o0_series import GapPolicy
from data_pc_origin.o7_fixtures import gc3_gap_series
from data_pc_origin.o7_policy import GAP_POLICY_ENV, prepare_column_list, select_gap_policy


def _assert(condition: bool, msg: str = "") -> None:
    if not condition:
        raise AssertionError(msg or "assertion failed")


def _gate_o7_p_01_a_1() -> None:
    _assert(select_gap_policy(environ={}) == GapPolicy.AS_EMPTY)


def _gate_o7_p_01_b_1() -> None:
    _assert(select_gap_policy(environ={GAP_POLICY_ENV: "nan"}) == GapPolicy.AS_NAN)
    _assert(select_gap_policy(environ={GAP_POLICY_ENV: "skip"}) == GapPolicy.SKIP_ROWS)
    _assert(select_gap_policy(environ={GAP_POLICY_ENV: "bogus"}) == GapPolicy.AS_EMPTY)


def _gate_o7_p_02_a_1() -> None:
    out = prepare_column_list(gc3_gap_series(), gap_policy=GapPolicy.AS_EMPTY)
    _assert(len(out) == 107)
    _assert(out[99] == "" and out[100] == "")


_O7_P_GATES: list[tuple[str, object]] = [
    ("O7-P-01-a-1", _gate_o7_p_01_a_1),
    ("O7-P-01-b-1", _gate_o7_p_01_b_1),
    ("O7-P-02-a-1", _gate_o7_p_02_a_1),
]


def register_o7_p_gates() -> None:
    for gate_id, fn in _O7_P_GATES:
        register_gate(gate_id, fn, depends=O7_DEPS[gate_id], layer="O7")  # type: ignore[arg-type]
