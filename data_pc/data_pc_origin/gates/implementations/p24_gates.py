# -*- coding: utf-8
"""P24 L4 gate bodies — operational closure rollup."""

from __future__ import annotations

from pathlib import Path

from data_pc_origin.gates.registry import P24_DEPS, register_gate
from data_pc_origin.live_ops_rollup import ARTIFACT_NAME, run_live_ops_rollup
from data_pc_origin.p24_ops_rollup import (
    build_ops_rollup_manifest,
    validate_ops_rollup_artifact,
)


def _assert(condition: bool, msg: str = "") -> None:
    if not condition:
        raise AssertionError(msg or "assertion failed")


def _script_dir() -> str:
    return str(Path(__file__).resolve().parents[2].parent)


def _gate_p24_o_01_a_1() -> None:
    m = build_ops_rollup_manifest(_script_dir())
    _assert("readiness" in m.layers)
    _assert("autostart" in m.layers)
    _assert("github" in m.layers)


def _gate_p24_o_02_a_1() -> None:
    m = build_ops_rollup_manifest(_script_dir())
    _assert(m.gate_count >= 166)
    _assert("full_e2e_ready" in m.layers["readiness"])


def _gate_p24_o_03_a_1() -> None:
    m = build_ops_rollup_manifest(_script_dir())
    _assert(m.layers["cutover"]["already_production"] is True)
    _assert(m.layers["autostart"]["ready"] is True)


def _gate_p24_o_04_a_1() -> None:
    m = build_ops_rollup_manifest(_script_dir(), dry_tick=True)
    _assert("supervisor_dry_tick" in m.checks or "supervisor_dry_tick" in m.layers["readiness"].get("checks", []))


def _gate_p24_h_01_a_1() -> None:
    root = Path(__file__).resolve().parents[2]
    out = run_live_ops_rollup(artifact_dir=root, script_dir=_script_dir())
    _assert(out["status"] in ("ok", "partial"))
    _assert(out.get("artifact_valid") is True)


def _gate_p24_h_02_a_1() -> None:
    root = Path(__file__).resolve().parents[2]
    _assert((root / ARTIFACT_NAME).is_file())


def _gate_p24_h_03_a_1() -> None:
    m = build_ops_rollup_manifest(_script_dir())
    _assert(m.production_ready)


def _gate_p24_h_04_a_1() -> None:
    root = Path(__file__).resolve().parents[2]
    out = run_live_ops_rollup(artifact_dir=root, script_dir=_script_dir())
    _assert(validate_ops_rollup_artifact(out))
    _assert(out["manifest"]["production_ready"] is True)


_P24_GATES: list[tuple[str, object]] = [
    ("P24-O-01-a-1", _gate_p24_o_01_a_1),
    ("P24-O-02-a-1", _gate_p24_o_02_a_1),
    ("P24-O-03-a-1", _gate_p24_o_03_a_1),
    ("P24-O-04-a-1", _gate_p24_o_04_a_1),
    ("P24-H-01-a-1", _gate_p24_h_01_a_1),
    ("P24-H-02-a-1", _gate_p24_h_02_a_1),
    ("P24-H-03-a-1", _gate_p24_h_03_a_1),
    ("P24-H-04-a-1", _gate_p24_h_04_a_1),
]


def register_p24_gates() -> None:
    for gate_id, fn in _P24_GATES:
        register_gate(gate_id, fn, depends=P24_DEPS[gate_id], layer="P24")  # type: ignore[arg-type]
