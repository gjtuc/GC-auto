# -*- coding: utf-8
"""P9-L live workflow L4 gate bodies."""

from __future__ import annotations

from pathlib import Path

from data_pc_origin.gates.registry import P9_L_DEPS, register_gate
from data_pc_origin.live_workflow import (
    ARTIFACT_NAME,
    prepare_live_workflow,
    resolve_live_excel_path,
    run_live_workflow,
)


def _assert(condition: bool, msg: str = "") -> None:
    if not condition:
        raise AssertionError(msg or "assertion failed")


def _gate_p9_l_01_a_1() -> None:
    prep = prepare_live_workflow("")
    _assert(isinstance(prep.ready, bool))
    _assert("excel_path" in prep.to_dict())


def _gate_p9_l_02_a_1() -> None:
    root = Path(__file__).resolve().parents[2]
    out = run_live_workflow("", artifact_dir=root, dry_run=False)
    _assert(out["status"] in ("skipped", "ok", "error", "dry_run"))
    _assert(ARTIFACT_NAME in str(out.get("artifact", "")))


def _gate_p9_l_03_a_1() -> None:
    artifact = Path(__file__).resolve().parents[2] / ARTIFACT_NAME
    _assert(artifact.is_file())
    text = artifact.read_text(encoding="utf-8")
    _assert("prep" in text)
    _assert("mode" in text)


def _gate_p9_l_04_a_1() -> None:
    """resolve_live_excel_path — 빈 opju → 빈 문자열."""
    _assert(resolve_live_excel_path("") == "")


_P9_L_GATES: list[tuple[str, object]] = [
    ("P9-L-01-a-1", _gate_p9_l_01_a_1),
    ("P9-L-02-a-1", _gate_p9_l_02_a_1),
    ("P9-L-03-a-1", _gate_p9_l_03_a_1),
    ("P9-L-04-a-1", _gate_p9_l_04_a_1),
]


def register_p9_l_gates() -> None:
    for gate_id, fn in _P9_L_GATES:
        register_gate(gate_id, fn, depends=P9_L_DEPS[gate_id], layer="P9")  # type: ignore[arg-type]
