# -*- coding: utf-8
"""P40 L4 gate bodies — merge PR (post-P41)."""

from __future__ import annotations

import os
from pathlib import Path

from data_pc_origin.gates.registry import P40_DEPS, register_gate
from data_pc_origin.live_p40_merge_pr import ARTIFACT_NAME, run_live_p40_merge_pr
from data_pc_origin.p23_github_snapshot import SNAPSHOT_BRANCH
from data_pc_origin.p28_merge_readiness import MERGE_PR_ENV, merge_pr_enabled
from data_pc_origin.p40_merge_pr import (
    plan_merge_pr_post41,
    validate_merge_pr_post41_artifact,
)


def _assert(condition: bool, msg: str = "") -> None:
    if not condition:
        raise AssertionError(msg or "assertion failed")


def _script_dir() -> str:
    return str(Path(__file__).resolve().parents[2].parent)


def _gate_p40_m_01_a_1() -> None:
    plan = plan_merge_pr_post41(_script_dir())
    _assert(plan.gate_count >= 310)
    _assert(plan.stack_gate_count >= 616)
    _assert(plan.branch == SNAPSHOT_BRANCH)
    _assert(plan.base == "main")


def _gate_p40_m_02_a_1() -> None:
    plan = plan_merge_pr_post41(_script_dir())
    _assert(plan.structural_ready)
    _assert("structural_ready" in plan.checks)
    _assert("stack_manifest_ready" in plan.checks)


def _gate_p40_m_03_a_1() -> None:
    plan = plan_merge_pr_post41(_script_dir())
    _assert(plan.remote_synced)
    _assert(plan.push_ready)


def _gate_p40_m_04_a_1() -> None:
    _assert(merge_pr_enabled({MERGE_PR_ENV: "1"}))
    _assert(not merge_pr_enabled({MERGE_PR_ENV: "0"}))


def _gate_p40_h_01_a_1() -> None:
    root = Path(__file__).resolve().parents[2]
    out = run_live_p40_merge_pr(artifact_dir=root, script_dir=_script_dir())
    _assert(out["status"] in ("ok", "partial"))
    _assert(out.get("artifact_valid") is True)


def _gate_p40_h_02_a_1() -> None:
    root = Path(__file__).resolve().parents[2]
    _assert((root / ARTIFACT_NAME).is_file())


def _gate_p40_h_03_a_1() -> None:
    saved = os.environ.pop(MERGE_PR_ENV, None)
    try:
        out = run_live_p40_merge_pr(script_dir=_script_dir(), create_pr=True)
        _assert(out["mode"] == "pr")
        _assert(out["status"] == "skipped")
    finally:
        if saved is not None:
            os.environ[MERGE_PR_ENV] = saved


def _gate_p40_h_04_a_1() -> None:
    plan = plan_merge_pr_post41(_script_dir())
    _assert(plan.structural_ready)
    root = Path(__file__).resolve().parents[2]
    out = run_live_p40_merge_pr(artifact_dir=root, script_dir=_script_dir())
    _assert(validate_merge_pr_post41_artifact(out))


_P40_GATES: list[tuple[str, object]] = [
    ("P40-M-01-a-1", _gate_p40_m_01_a_1),
    ("P40-M-02-a-1", _gate_p40_m_02_a_1),
    ("P40-M-03-a-1", _gate_p40_m_03_a_1),
    ("P40-M-04-a-1", _gate_p40_m_04_a_1),
    ("P40-H-01-a-1", _gate_p40_h_01_a_1),
    ("P40-H-02-a-1", _gate_p40_h_02_a_1),
    ("P40-H-03-a-1", _gate_p40_h_03_a_1),
    ("P40-H-04-a-1", _gate_p40_h_04_a_1),
]


def register_p40_gates() -> None:
    for gate_id, fn in _P40_GATES:
        register_gate(gate_id, fn, depends=P40_DEPS[gate_id], layer="P40")  # type: ignore[arg-type]
