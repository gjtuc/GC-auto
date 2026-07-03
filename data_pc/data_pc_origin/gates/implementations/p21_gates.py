# -*- coding: utf-8
"""P21 L4 gate bodies — operational cutover."""

from __future__ import annotations

import os
import tempfile
from pathlib import Path

from data_pc_origin.gates.registry import P21_DEPS, register_gate
from data_pc_origin.live_cutover import ARTIFACT_NAME, run_live_cutover
from data_pc_origin.p17_env_config import SKIP_ORIGIN_ENV
from data_pc_origin.p21_cutover import (
    CUTOVER_APPLY_ENV,
    apply_cutover,
    cutover_apply_enabled,
    plan_cutover,
    validate_cutover_artifact,
)


def _assert(condition: bool, msg: str = "") -> None:
    if not condition:
        raise AssertionError(msg or "assertion failed")


def _script_dir() -> str:
    return str(Path(__file__).resolve().parents[2].parent)


def _gate_p21_c_01_a_1() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        env = Path(tmp) / "gc_automation.env"
        env.write_text(f"{SKIP_ORIGIN_ENV}=1\nDATA_PC_ORIGIN_PIPELINE=1\n", encoding="utf-8")
        plan = plan_cutover(tmp)
        _assert(not plan.already_production)
        _assert(any(c["key"] == SKIP_ORIGIN_ENV for c in plan.changes))


def _gate_p21_c_02_a_1() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        env = Path(tmp) / "gc_automation.env"
        env.write_text(f"{SKIP_ORIGIN_ENV}=1\nDATA_PC_ORIGIN_PIPELINE=1\n", encoding="utf-8")
        plan = apply_cutover(tmp, backup=True)
        text = env.read_text(encoding="utf-8")
        _assert(f"{SKIP_ORIGIN_ENV}=0" in text)
        _assert(Path(plan.backup_path).is_file())


def _gate_p21_c_03_a_1() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        env = Path(tmp) / "gc_automation.env"
        env.write_text(f"{SKIP_ORIGIN_ENV}=0\nDATA_PC_ORIGIN_PIPELINE=1\n", encoding="utf-8")
        plan = plan_cutover(tmp)
        _assert(plan.already_production)


def _gate_p21_c_04_a_1() -> None:
    _assert(cutover_apply_enabled({CUTOVER_APPLY_ENV: "1"}))
    _assert(not cutover_apply_enabled({CUTOVER_APPLY_ENV: "0"}))


def _gate_p21_h_01_a_1() -> None:
    root = Path(__file__).resolve().parents[2]
    out = run_live_cutover(artifact_dir=root, script_dir=_script_dir(), dry=True)
    _assert(out["status"] == "ok")
    _assert(out["mode"] == "dry_plan")


def _gate_p21_h_02_a_1() -> None:
    root = Path(__file__).resolve().parents[2]
    _assert((root / ARTIFACT_NAME).is_file())


def _gate_p21_h_03_a_1() -> None:
    saved = os.environ.pop(CUTOVER_APPLY_ENV, None)
    try:
        out = run_live_cutover(script_dir=_script_dir(), apply=True)
        _assert(out["mode"] == "apply")
        _assert(out["status"] == "skipped")
    finally:
        if saved is not None:
            os.environ[CUTOVER_APPLY_ENV] = saved


def _gate_p21_h_04_a_1() -> None:
    root = Path(__file__).resolve().parents[2]
    out = run_live_cutover(artifact_dir=root, script_dir=_script_dir(), dry=True)
    _assert(validate_cutover_artifact(out))


_P21_GATES: list[tuple[str, object]] = [
    ("P21-C-01-a-1", _gate_p21_c_01_a_1),
    ("P21-C-02-a-1", _gate_p21_c_02_a_1),
    ("P21-C-03-a-1", _gate_p21_c_03_a_1),
    ("P21-C-04-a-1", _gate_p21_c_04_a_1),
    ("P21-H-01-a-1", _gate_p21_h_01_a_1),
    ("P21-H-02-a-1", _gate_p21_h_02_a_1),
    ("P21-H-03-a-1", _gate_p21_h_03_a_1),
    ("P21-H-04-a-1", _gate_p21_h_04_a_1),
]


def register_p21_gates() -> None:
    for gate_id, fn in _P21_GATES:
        register_gate(gate_id, fn, depends=P21_DEPS[gate_id], layer="P21")  # type: ignore[arg-type]
