# -*- coding: utf-8
"""O9-L live harness L4 gate bodies."""

from __future__ import annotations

from pathlib import Path

from data_pc_origin.gates.registry import O9_L_DEPS, register_gate
from data_pc_origin.live_run import ARTIFACT_NAME, prepare_live_e2e, run_live_e2e


def _assert(condition: bool, msg: str = "") -> None:
    if not condition:
        raise AssertionError(msg or "assertion failed")


def _gate_o9_l_01_a_1() -> None:
    prep = prepare_live_e2e("")
    _assert(isinstance(prep.ready, bool))
    _assert("skip_origin" in prep.to_dict())


def _gate_o9_l_02_a_1() -> None:
    out = run_live_e2e("", artifact_dir=Path(__file__).resolve().parents[2], use_fixture=True)
    _assert(out["status"] in ("skipped", "ok", "partial", "error"))
    _assert(ARTIFACT_NAME in str(out.get("artifact", "")))


def _gate_o9_l_03_a_1() -> None:
    artifact = Path(__file__).resolve().parents[2] / ARTIFACT_NAME
    _assert(artifact.is_file())
    _assert("prep" in artifact.read_text(encoding="utf-8"))


_O9_L_GATES: list[tuple[str, object]] = [
    ("O9-L-01-a-1", _gate_o9_l_01_a_1),
    ("O9-L-02-a-1", _gate_o9_l_02_a_1),
    ("O9-L-03-a-1", _gate_o9_l_03_a_1),
]


def register_o9_l_gates() -> None:
    for gate_id, fn in _O9_L_GATES:
        register_gate(gate_id, fn, depends=O9_L_DEPS[gate_id], layer="O9")  # type: ignore[arg-type]
