# -*- coding: utf-8
"""P20 L4 gate bodies — production readiness manifest."""

from __future__ import annotations

from pathlib import Path

from data_pc_origin.gates.registry import P20_DEPS, register_gate
from data_pc_origin.live_readiness import ARTIFACT_NAME, run_live_readiness
from data_pc_origin.p20_readiness import build_readiness_manifest, validate_readiness_artifact


def _assert(condition: bool, msg: str = "") -> None:
    if not condition:
        raise AssertionError(msg or "assertion failed")


def _script_dir() -> str:
    return str(Path(__file__).resolve().parents[2].parent)


def _gate_p20_m_01_a_1() -> None:
    m = build_readiness_manifest(
        _script_dir(),
        environ={"DATA_PC_ORIGIN_PIPELINE": "1", "DATA_PC_LEGACY_WATCH": "0"},
    )
    _assert(m.stack == "imap_full_native_origin")
    _assert("env" in m.layers)


def _gate_p20_m_02_a_1() -> None:
    m = build_readiness_manifest(
        _script_dir(),
        environ={"DATA_PC_ORIGIN_PIPELINE": "1", "DATA_PC_SKIP_ORIGIN": "0"},
    )
    _assert("origin_pipeline" in m.checks)
    _assert(m.layers["watch"]["runtime_watch"] is True)


def _gate_p20_m_03_a_1() -> None:
    m = build_readiness_manifest(_script_dir())
    _assert("production_e2e" in m.layers)
    _assert("runtime_bridge" in m.layers)


def _gate_p20_m_04_a_1() -> None:
    m = build_readiness_manifest(_script_dir(), dry_tick=True)
    _assert("supervisor_dry_tick" in m.checks)


def _gate_p20_h_01_a_1() -> None:
    root = Path(__file__).resolve().parents[2]
    out = run_live_readiness(artifact_dir=root, dry_tick=False)
    _assert(out["status"] in ("ok", "partial"))
    _assert(out.get("artifact_valid") is True)


def _gate_p20_h_02_a_1() -> None:
    root = Path(__file__).resolve().parents[2]
    _assert((root / ARTIFACT_NAME).is_file())


def _gate_p20_h_03_a_1() -> None:
    root = Path(__file__).resolve().parents[2]
    out = run_live_readiness(artifact_dir=root, dry_tick=True)
    tick = out["manifest"]["layers"].get("supervisor_tick", {})
    _assert(tick.get("ok") is True)


def _gate_p20_h_04_a_1() -> None:
    root = Path(__file__).resolve().parents[2]
    out = run_live_readiness(artifact_dir=root)
    _assert(validate_readiness_artifact(out))


_P20_GATES: list[tuple[str, object]] = [
    ("P20-M-01-a-1", _gate_p20_m_01_a_1),
    ("P20-M-02-a-1", _gate_p20_m_02_a_1),
    ("P20-M-03-a-1", _gate_p20_m_03_a_1),
    ("P20-M-04-a-1", _gate_p20_m_04_a_1),
    ("P20-H-01-a-1", _gate_p20_h_01_a_1),
    ("P20-H-02-a-1", _gate_p20_h_02_a_1),
    ("P20-H-03-a-1", _gate_p20_h_03_a_1),
    ("P20-H-04-a-1", _gate_p20_h_04_a_1),
]


def register_p20_gates() -> None:
    for gate_id, fn in _P20_GATES:
        register_gate(gate_id, fn, depends=P20_DEPS[gate_id], layer="P20")  # type: ignore[arg-type]
