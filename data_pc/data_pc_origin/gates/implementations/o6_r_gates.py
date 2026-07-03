# -*- coding: utf-8 -*-
"""O6-R L4 gate bodies."""

from __future__ import annotations

from data_pc_origin.gates.registry import O6_DEPS, register_gate
from data_pc_origin.o6_fixtures import (
    IDENTITY_KEY,
    SAMPLE_EXACT,
    SAMPLE_NEW,
    fx_wks_exact_match,
    fx_wks_identity_match,
    fx_wks_three_dated,
)
from data_pc_origin.o6_resolve import resolve_target_column


def _assert(condition: bool, msg: str = "") -> None:
    if not condition:
        raise AssertionError(msg or "assertion failed")


def _gate_o6_r_01_a_1() -> None:
    calls: list[str] = []

    def _lt(cmd: str) -> None:
        calls.append(cmd)

    wks = fx_wks_exact_match()
    _assert(resolve_target_column(wks, SAMPLE_EXACT, lt_execute=_lt) == 2)
    _assert(calls == [])

    wks2 = fx_wks_identity_match()
    _assert(resolve_target_column(wks2, "new name", IDENTITY_KEY, lt_execute=_lt) == 2)
    _assert(calls == [])

    wks3 = fx_wks_three_dated()
    col = resolve_target_column(wks3, SAMPLE_NEW, lt_execute=_lt)
    _assert(col == 2)
    _assert(len(calls) == 1)


def _gate_o6_r_01_b_1() -> None:
    """O8-J-04 — 동일 wks·sample → 동일 col (exact path)."""
    wks = fx_wks_exact_match()
    a = resolve_target_column(wks, SAMPLE_EXACT, lt_execute=lambda _c: None)
    b = resolve_target_column(wks, SAMPLE_EXACT, lt_execute=lambda _c: None)
    _assert(a == b == 2)


_O6_R_GATES: list[tuple[str, object]] = [
    ("O6-R-01-a-1", _gate_o6_r_01_a_1),
    ("O6-R-01-b-1", _gate_o6_r_01_b_1),
]


def register_o6_r_gates() -> None:
    for gate_id, fn in _O6_R_GATES:
        register_gate(gate_id, fn, depends=O6_DEPS[gate_id], layer="O6")  # type: ignore[arg-type]
