# -*- coding: utf-8 -*-
"""O5 meta gates — E2E mock chain + L1 rollup smoke."""

from __future__ import annotations

from data_pc_origin.gates.registry import (
    O5_E2E_DEPS,
    O5_I_GATES,
    O5_M_GATES,
    O5_R_DEPS,
    O5_T_GATES,
    _O0_O1_O2_O3_O4_PREFIX,
    register_gate,
)
from data_pc_origin.gates.runner import run_gates_in_order
from data_pc_origin.o0_mapping import DEFAULT_ORIGIN_MAPPING
from data_pc_origin.o0_types import OriginWarning
from data_pc_origin.o5_fixtures import fx_default_mapping_op, fx_opju_two_books, make_mock_op
from data_pc_origin.o5_match import report_missing, resolve_worksheets


def _assert(condition: bool, msg: str = "") -> None:
    if not condition:
        raise AssertionError(msg or "assertion failed")


class _FakeDf:
    def __init__(self, columns: list[str]) -> None:
        self.columns = columns


def _rollup_ok(prefix: list[str], gates: list[str], label: str) -> None:
    code, log, _ = run_gates_in_order(prefix + gates)
    _assert(code == 0, f"{label} rollup failed: {log[-1:] if log else log}")


# --- O5-E2E (3) ---


def _gate_o5_e2e_01_a_1() -> None:
    op, _ = fx_default_mapping_op()
    df = _FakeDf(list(DEFAULT_ORIGIN_MAPPING.keys()))
    hits, misses = resolve_worksheets(op, DEFAULT_ORIGIN_MAPPING, df)
    warns = report_missing(misses)
    _assert(len(hits) == 8)
    _assert(len(misses) == 0)
    _assert(warns == [])
    _assert(hits["H2 yield"].name == "H2yield")
    _assert(hits["CO2 conversion"].name == "CO2conversion")


def _gate_o5_e2e_02_a_1() -> None:
    op = make_mock_op([])
    df = _FakeDf(list(DEFAULT_ORIGIN_MAPPING.keys()))
    hits, misses = resolve_worksheets(op, DEFAULT_ORIGIN_MAPPING, df)
    warns = report_missing(misses)
    _assert(len(hits) == 0)
    _assert(len(misses) == 8)
    _assert(len(warns) == 1)
    _assert(warns[0].code == "WKS_MISS")
    _assert(isinstance(warns[0], OriginWarning))


def _gate_o5_e2e_03_a_1() -> None:
    op, _ = fx_opju_two_books()
    df = _FakeDf(["H2 Yield (%)", "C2H6 Conversion (%)"])
    hits, misses = resolve_worksheets(op, DEFAULT_ORIGIN_MAPPING, df)
    warns = report_missing(misses)
    _assert(len(hits) == 1 and "H2 yield" in hits)
    _assert(misses == ["C2H6 conversion"])
    _assert(len(warns) == 1 and warns[0].code == "WKS_MISS")


# --- O5-R rollup smoke (4) ---


def _gate_o5_r_01_a_1() -> None:
    _rollup_ok(_O0_O1_O2_O3_O4_PREFIX, list(O5_I_GATES), "O5-L1-I")


def _gate_o5_r_02_a_1() -> None:
    _rollup_ok(
        _O0_O1_O2_O3_O4_PREFIX,
        list(O5_I_GATES) + list(O5_T_GATES),
        "O5-L1-T",
    )


def _gate_o5_r_03_a_1() -> None:
    _rollup_ok(
        _O0_O1_O2_O3_O4_PREFIX,
        list(O5_I_GATES) + list(O5_T_GATES) + list(O5_M_GATES),
        "O5-L1-M",
    )


def _gate_o5_r_04_a_1() -> None:
    _rollup_ok(
        _O0_O1_O2_O3_O4_PREFIX,
        list(O5_I_GATES) + list(O5_T_GATES) + list(O5_M_GATES),
        "O5 core",
    )
    _assert(len(O5_I_GATES) + len(O5_T_GATES) + len(O5_M_GATES) == 105)


_O5_E2E_GATES: list[tuple[str, object]] = [
    ("O5-E2E-01-a-1", _gate_o5_e2e_01_a_1),
    ("O5-E2E-02-a-1", _gate_o5_e2e_02_a_1),
    ("O5-E2E-03-a-1", _gate_o5_e2e_03_a_1),
]

_O5_R_GATES: list[tuple[str, object]] = [
    ("O5-R-01-a-1", _gate_o5_r_01_a_1),
    ("O5-R-02-a-1", _gate_o5_r_02_a_1),
    ("O5-R-03-a-1", _gate_o5_r_03_a_1),
    ("O5-R-04-a-1", _gate_o5_r_04_a_1),
]


def register_o5_meta_gates() -> None:
    for gate_id, fn in _O5_E2E_GATES:
        register_gate(gate_id, fn, depends=O5_E2E_DEPS[gate_id], layer="O5")  # type: ignore[arg-type]
    for gate_id, fn in _O5_R_GATES:
        register_gate(gate_id, fn, depends=O5_R_DEPS[gate_id], layer="O5")  # type: ignore[arg-type]
