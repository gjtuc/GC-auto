# -*- coding: utf-8 -*-
"""P41 L4 gate bodies — O층 정렬 후 stack manifest."""

from __future__ import annotations

from pathlib import Path

from data_pc_origin.catalyst_identity_bridge import (
    catalyst_comment_matches_identity,
)
from data_pc_origin.gates.registry import (
    O0_IMPLEMENTATION_ORDER,
    O6_G_GATES,
    O6_IMPLEMENTATION_ORDER,
    P40_EXTENDED_ORDER,
    P41_DEPS,
    register_gate,
    rollup_gate_ids,
)
from data_pc_origin.live_p41_manifest import ARTIFACT_NAME, run_live_p41_manifest
from data_pc_origin.p41_manifest import (
    plan_stack_manifest_post40,
    validate_stack_manifest_artifact,
)

_LIVE_IDENTITY = ("20260620", "dre(1.5) 600c ni5_ce5_al2o3")
_LIVE_COMMENT = "20260620 DRE(1.5%)@600°C Ni5/Ce5/Al2O3_OCM 장비"


def _assert(condition: bool, msg: str = "") -> None:
    if not condition:
        raise AssertionError(msg or "assertion failed")


def _script_dir() -> str:
    return str(Path(__file__).resolve().parents[2].parent)


def _gate_p41_m_01_a_1() -> None:
    plan = plan_stack_manifest_post40(_script_dir())
    _assert(plan.stack_gate_count >= len(P40_EXTENDED_ORDER))
    _assert(plan.p40_extended_gate_count >= 302)
    _assert(plan.p41_extended_gate_count == plan.p40_extended_gate_count + 8)


def _gate_p41_m_02_a_1() -> None:
    plan = plan_stack_manifest_post40(_script_dir())
    _assert(plan.o0_gate_count == len(O0_IMPLEMENTATION_ORDER))
    _assert(plan.o6_gate_count == len(O6_IMPLEMENTATION_ORDER))
    _assert(plan.o6_g_gate_count == len(O6_G_GATES))


def _gate_p41_m_03_a_1() -> None:
    root = Path(_script_dir())
    _assert((root / "data_pc_origin" / "catalyst_identity_bridge.py").is_file())
    _assert((root / "data_pc_origin" / "catalyst_o6_bridge.py").is_file())


def _gate_p41_m_04_a_1() -> None:
    """실행 검증 — live GC Comments ↔ KCH identity."""
    _assert(catalyst_comment_matches_identity(_LIVE_COMMENT, _LIVE_IDENTITY))


def _gate_p41_h_01_a_1() -> None:
    root = Path(__file__).resolve().parents[2]
    out = run_live_p41_manifest(artifact_dir=root, script_dir=_script_dir())
    _assert(out["status"] in ("ok", "partial"))
    _assert(out.get("artifact_valid") is True)


def _gate_p41_h_02_a_1() -> None:
    root = Path(__file__).resolve().parents[2]
    _assert((root / ARTIFACT_NAME).is_file())


def _gate_p41_h_03_a_1() -> None:
    stack = len(rollup_gate_ids("P41"))
    _assert(stack == len(rollup_gate_ids("P40")) + 8)


def _gate_p41_h_04_a_1() -> None:
    root = Path(__file__).resolve().parents[2]
    out = run_live_p41_manifest(artifact_dir=root, script_dir=_script_dir())
    _assert(validate_stack_manifest_artifact(out))


_P41_GATES: list[tuple[str, object]] = [
    ("P41-M-01-a-1", _gate_p41_m_01_a_1),
    ("P41-M-02-a-1", _gate_p41_m_02_a_1),
    ("P41-M-03-a-1", _gate_p41_m_03_a_1),
    ("P41-M-04-a-1", _gate_p41_m_04_a_1),
    ("P41-H-01-a-1", _gate_p41_h_01_a_1),
    ("P41-H-02-a-1", _gate_p41_h_02_a_1),
    ("P41-H-03-a-1", _gate_p41_h_03_a_1),
    ("P41-H-04-a-1", _gate_p41_h_04_a_1),
]


def register_p41_gates() -> None:
    for gate_id, fn in _P41_GATES:
        register_gate(gate_id, fn, depends=P41_DEPS[gate_id], layer="P41")  # type: ignore[arg-type]
