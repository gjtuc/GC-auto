# -*- coding: utf-8 -*-
"""O6-S L4 gate bodies."""

from __future__ import annotations

from data_pc_origin.gates.registry import O6_DEPS, register_gate
from data_pc_origin.o6_fixtures import fx_wks_empty, fx_wks_mixed_dated, fx_wks_three_dated
from data_pc_origin.o6_scan import dated_columns, iter_col_comments


def _assert(condition: bool, msg: str = "") -> None:
    if not condition:
        raise AssertionError(msg or "assertion failed")


def _gate_o6_s_01_a_1() -> None:
    wks = fx_wks_three_dated()
    pairs = list(iter_col_comments(wks))
    _assert(len(pairs) == 3)
    _assert(pairs[0] == (1, "202506010900 10Ni5Ce5 700C"))
    _assert(all(isinstance(i, int) and isinstance(c, str) for i, c in pairs))


def _gate_o6_s_01_b_1() -> None:
    wks = fx_wks_empty()
    _assert(list(iter_col_comments(wks)) == [])


def _gate_o6_s_02_a_1() -> None:
    wks = fx_wks_three_dated()
    dated = dated_columns(wks)
    _assert(dated == [(1, "20250601"), (2, "20250615"), (3, "20250620")])


def _gate_o6_s_02_b_1() -> None:
    wks = fx_wks_mixed_dated()
    dated = dated_columns(wks)
    _assert(dated == [(1, "20250601"), (3, "20250620")])


_O6_S_GATES: list[tuple[str, object]] = [
    ("O6-S-01-a-1", _gate_o6_s_01_a_1),
    ("O6-S-01-b-1", _gate_o6_s_01_b_1),
    ("O6-S-02-a-1", _gate_o6_s_02_a_1),
    ("O6-S-02-b-1", _gate_o6_s_02_b_1),
]


def register_o6_gates() -> None:
    for gate_id, fn in _O6_S_GATES:
        register_gate(gate_id, fn, depends=O6_DEPS[gate_id], layer="O6")  # type: ignore[arg-type]
