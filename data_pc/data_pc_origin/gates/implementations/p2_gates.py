# -*- coding: utf-8
"""P2 L4 gate bodies."""

from __future__ import annotations

from data_pc_origin.gates.registry import P2_DEPS, register_gate
from data_pc_origin.p2_paths import (
    build_stage4_paths,
    is_g_drive_path,
    normalize_opju_path,
    probe_stage4_suffix,
    resolve_stage4_save_path,
)


def _assert(condition: bool, msg: str = "") -> None:
    if not condition:
        raise AssertionError(msg or "assertion failed")


FX_OPJU = r"g:\lab\Ni5.opju"


def _gate_p2_v_01_a_1() -> None:
    _assert(normalize_opju_path(FX_OPJU) == r"G:\lab\Ni5.opju")


def _gate_p2_v_02_a_1() -> None:
    _assert(is_g_drive_path(FX_OPJU) is True)
    _assert(is_g_drive_path(r"C:\x.opju") is False)


def _gate_p2_p_01_a_1() -> None:
    ok = probe_stage4_suffix(FX_OPJU)
    _assert(ok.ok is True)
    bad = probe_stage4_suffix(r"G:\x.xlsx")
    _assert(bad.ok is False)


def _gate_p2_s_01_a_1() -> None:
    p = r"G:\t\run.opju"
    _assert(resolve_stage4_save_path(p, True) == normalize_opju_path(p))


def _gate_p2_s_02_a_1() -> None:
    p = r"G:\t\run.opju"
    _assert(resolve_stage4_save_path(p, False).endswith("_Updated.opju"))


def _gate_p2_r_01_a_1() -> None:
    bundle = build_stage4_paths(FX_OPJU, save_in_place=False)
    _assert(bundle.source_opju.startswith("G:"))
    _assert(bundle.save_path.endswith("_Updated.opju"))
    _assert(bundle.save_in_place is False)


_P2_GATES: list[tuple[str, object]] = [
    ("P2-V-01-a-1", _gate_p2_v_01_a_1),
    ("P2-V-02-a-1", _gate_p2_v_02_a_1),
    ("P2-P-01-a-1", _gate_p2_p_01_a_1),
    ("P2-S-01-a-1", _gate_p2_s_01_a_1),
    ("P2-S-02-a-1", _gate_p2_s_02_a_1),
    ("P2-R-01-a-1", _gate_p2_r_01_a_1),
]


def register_p2_gates() -> None:
    for gate_id, fn in _P2_GATES:
        register_gate(gate_id, fn, depends=P2_DEPS[gate_id], layer="P2")  # type: ignore[arg-type]
