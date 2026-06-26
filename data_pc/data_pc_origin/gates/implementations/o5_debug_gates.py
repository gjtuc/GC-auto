# -*- coding: utf-8
"""O5-DEBUG L4 gate bodies."""

from __future__ import annotations

from data_pc_origin.gates.registry import O5_DEBUG_DEPS, register_gate
from data_pc_origin.o0_keys import normalize_origin_key
from data_pc_origin.o5_debug import find_worksheet_for_keyword_debug
from data_pc_origin.o5_fixtures import fx_opju_two_books


def _assert(condition: bool, msg: str = "") -> None:
    if not condition:
        raise AssertionError(msg or "assertion failed")


def _gate_o5_debug_01_a_1() -> None:
    op, _ = fx_opju_two_books()
    _, dbg = find_worksheet_for_keyword_debug(op, "H2 yield")
    _assert(len(dbg.candidates) >= 1)
    _assert("raw_search" in dbg.candidates[0])
    _assert("Book1" in dbg.candidates[0]["raw_search"])


def _gate_o5_debug_02_a_1() -> None:
    op, _ = fx_opju_two_books()
    _, dbg = find_worksheet_for_keyword_debug(op, "CO2 conversion")
    row = dbg.candidates[0]
    _assert(row["norm_kw"] == normalize_origin_key("CO2 conversion"))
    _assert("norm_search" in row)


def _gate_o5_debug_03_a_1() -> None:
    op, _ = fx_opju_two_books()
    wks, dbg = find_worksheet_for_keyword_debug(op, "H2 yield")
    _assert(wks is not None)
    _assert(dbg.hit is not None)
    _assert(dbg.hit["wks"] == "H2yield")


def _gate_o5_debug_04_a_1() -> None:
    op, _ = fx_opju_two_books()
    _, dbg = find_worksheet_for_keyword_debug(op, "H2 yield")
    _assert(dbg.scanned == len(dbg.candidates))
    _assert(dbg.scanned >= 1)


def _gate_o5_debug_05_a_1() -> None:
    op, _ = fx_opju_two_books()
    _, dbg = find_worksheet_for_keyword_debug(op, "CO2 conversion")
    _assert(dbg.first_miss_fx == "C4")


_O5_DEBUG_GATES: list[tuple[str, object]] = [
    ("O5-DEBUG-01-a-1", _gate_o5_debug_01_a_1),
    ("O5-DEBUG-02-a-1", _gate_o5_debug_02_a_1),
    ("O5-DEBUG-03-a-1", _gate_o5_debug_03_a_1),
    ("O5-DEBUG-04-a-1", _gate_o5_debug_04_a_1),
    ("O5-DEBUG-05-a-1", _gate_o5_debug_05_a_1),
]


def register_o5_debug_gates() -> None:
    for gate_id, fn in _O5_DEBUG_GATES:
        register_gate(gate_id, fn, depends=O5_DEBUG_DEPS[gate_id], layer="O5")  # type: ignore[arg-type]
