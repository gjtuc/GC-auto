# -*- coding: utf-8
"""P28 L4 gate bodies — main merge readiness."""

from __future__ import annotations

import os
from pathlib import Path
from unittest.mock import patch

from data_pc_origin.gates.registry import P28_DEPS, register_gate
from data_pc_origin.live_merge_readiness import ARTIFACT_NAME, run_live_merge_readiness
from data_pc_origin.p23_github_snapshot import SNAPSHOT_BRANCH
from data_pc_origin.p28_merge_readiness import (
    MERGE_PR_ENV,
    build_merge_readiness_manifest,
    merge_pr_enabled,
    validate_merge_readiness_artifact,
)


def _assert(condition: bool, msg: str = "") -> None:
    if not condition:
        raise AssertionError(msg or "assertion failed")


def _script_dir() -> str:
    return str(Path(__file__).resolve().parents[2].parent)


def _gate_p28_m_01_a_1() -> None:
    m = build_merge_readiness_manifest(_script_dir())
    _assert(m.gate_count >= 206)
    _assert(m.branch == SNAPSHOT_BRANCH)
    _assert(m.base == "main")


def _gate_p28_m_02_a_1() -> None:
    m = build_merge_readiness_manifest(_script_dir())
    _assert(m.ops_ready is True)
    _assert("ops_production_ready" in m.checks)


def _gate_p28_m_03_a_1() -> None:
    m = build_merge_readiness_manifest(_script_dir())
    _assert(m.github_sync_ready is True)
    _assert("github_markers_synced" in m.checks)


def _gate_p28_m_04_a_1() -> None:
    _assert(merge_pr_enabled({MERGE_PR_ENV: "1"}))
    _assert(not merge_pr_enabled({MERGE_PR_ENV: "0"}))


def _gate_p28_h_01_a_1() -> None:
    root = Path(__file__).resolve().parents[2]
    out = run_live_merge_readiness(artifact_dir=root, script_dir=_script_dir())
    _assert(out["status"] in ("ok", "partial"))
    _assert(out.get("artifact_valid") is True)


def _gate_p28_h_02_a_1() -> None:
    root = Path(__file__).resolve().parents[2]
    _assert((root / ARTIFACT_NAME).is_file())


def _gate_p28_h_03_a_1() -> None:
    saved = os.environ.pop(MERGE_PR_ENV, None)
    try:
        out = run_live_merge_readiness(script_dir=_script_dir(), create_pr=True)
        _assert(out["mode"] == "pr")
        _assert(out["status"] == "skipped")
    finally:
        if saved is not None:
            os.environ[MERGE_PR_ENV] = saved


def _gate_p28_h_04_a_1() -> None:
    m = build_merge_readiness_manifest(_script_dir())
    _assert(m.ready is True)
    root = Path(__file__).resolve().parents[2]
    out = run_live_merge_readiness(artifact_dir=root, script_dir=_script_dir())
    _assert(validate_merge_readiness_artifact(out))


_P28_GATES: list[tuple[str, object]] = [
    ("P28-M-01-a-1", _gate_p28_m_01_a_1),
    ("P28-M-02-a-1", _gate_p28_m_02_a_1),
    ("P28-M-03-a-1", _gate_p28_m_03_a_1),
    ("P28-M-04-a-1", _gate_p28_m_04_a_1),
    ("P28-H-01-a-1", _gate_p28_h_01_a_1),
    ("P28-H-02-a-1", _gate_p28_h_02_a_1),
    ("P28-H-03-a-1", _gate_p28_h_03_a_1),
    ("P28-H-04-a-1", _gate_p28_h_04_a_1),
]


def register_p28_gates() -> None:
    for gate_id, fn in _P28_GATES:
        register_gate(gate_id, fn, depends=P28_DEPS[gate_id], layer="P28")  # type: ignore[arg-type]
