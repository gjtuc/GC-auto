# -*- coding: utf-8 -*-
"""O6-G — 장비·날짜 열 삽입 가드."""

from __future__ import annotations

from data_pc_origin.gates.registry import O6_DEPS, register_gate
from data_pc_origin.o0_equipment_day import evaluate_equipment_day_guard
from data_pc_origin.o6_fixtures import MockWks
from data_pc_origin.o6_guard import OriginColumnGuardError
from data_pc_origin.o6_resolve import resolve_target_column

_LEFT = "20260620 DRE(1.5%)@600°C Ni5/Ce5/Al2O3_OCM 장비"
_NEW_SAME = "20260620 DRE(3%)@650°C Ni10/Al2O3_OCM 장비"
_NEW_OK = "20260621 DRE(1.5%)@600°C Ni5/Ce5/Al2O3_OCM 장비"


def _assert(condition: bool, msg: str = "") -> None:
    if not condition:
        raise AssertionError(msg or "assertion failed")


def _wks() -> MockWks:
    return MockWks({1: {"C": _LEFT}, 2: {"C": ""}}, cols=3)


def _gate_o6_g_01_a_1() -> None:
    r = evaluate_equipment_day_guard(_LEFT, _NEW_SAME)
    _assert(r.needs_user_confirm and r.reason_code == "same_date")


def _gate_o6_g_02_a_1() -> None:
    left = "20260625 DRE(1.5%)@600°C Ni5/Ce5/Al2O3_OCM 장비"
    r = evaluate_equipment_day_guard(
        left, "20260620 DRE(1.5%)@600°C Ni5/Ce5/Al2O3_OCM 장비"
    )
    _assert(r.needs_user_confirm and r.reason_code == "left_date_ahead")


def _gate_o6_g_03_a_1() -> None:
    r = evaluate_equipment_day_guard(_LEFT, _NEW_OK)
    _assert(not r.needs_user_confirm)


def _gate_o6_g_04_a_1() -> None:
    try:
        resolve_target_column(_wks(), _NEW_SAME, lt_execute=lambda _c: None)
        _assert(False, "expected OriginColumnGuardError")
    except OriginColumnGuardError:
        pass


_O6_G_GATES: list[tuple[str, object]] = [
    ("O6-G-01-a-1", _gate_o6_g_01_a_1),
    ("O6-G-02-a-1", _gate_o6_g_02_a_1),
    ("O6-G-03-a-1", _gate_o6_g_03_a_1),
    ("O6-G-04-a-1", _gate_o6_g_04_a_1),
]


def register_o6_g_gates() -> None:
    for gate_id, fn in _O6_G_GATES:
        register_gate(gate_id, fn, depends=O6_DEPS[gate_id], layer="O6")  # type: ignore[arg-type]
