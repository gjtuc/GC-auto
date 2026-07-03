# -*- coding: utf-8
"""P23 L4 gate bodies — GitHub snapshot sync · push."""

from __future__ import annotations

import os
import tempfile
from pathlib import Path

from data_pc_origin.gates.registry import P23_DEPS, register_gate
from data_pc_origin.live_github_snapshot import ARTIFACT_NAME, run_live_github_snapshot
from data_pc_origin.p23_github_snapshot import (
    GITHUB_PUSH_ENV,
    SNAPSHOT_BRANCH,
    github_push_enabled,
    plan_github_snapshot,
    sync_snapshot,
    validate_github_snapshot_artifact,
)


def _assert(condition: bool, msg: str = "") -> None:
    if not condition:
        raise AssertionError(msg or "assertion failed")


def _script_dir() -> str:
    return str(Path(__file__).resolve().parents[2].parent)


def _gate_p23_g_01_a_1() -> None:
    plan = plan_github_snapshot(_script_dir())
    _assert(plan.ready, plan.reason)
    _assert(plan.branch == SNAPSHOT_BRANCH)
    _assert(plan.gate_count >= 158)


def _gate_p23_g_02_a_1() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        src = Path(tmp) / "src"
        repo = src / "GC-auto-push"
        (src / "data_pc_origin").mkdir(parents=True)
        (src / "data_pc_origin" / "verify.py").write_text("# test\n", encoding="utf-8")
        (src / "data_pc_runtime").mkdir()
        (src / "data_pc_runtime" / "verify.py").write_text("# rt\n", encoding="utf-8")
        (src / "data_pc_watch.py").write_text("# watch\n", encoding="utf-8")
        (src / "data_pc_watchdog.py").write_text("# wd\n", encoding="utf-8")
        (src / "촉매 반응 계산.py").write_text("# calc\n", encoding="utf-8")
        for name in (
            "gc_data_pc_watch_loop.bat",
            "gc_data_pc_ensure_watch.bat",
            "gc_data_pc_ensure_watch_hidden.vbs",
            "gc_data_pc_start_watch_hidden.vbs",
        ):
            (src / name).write_text("@echo off\n", encoding="utf-8")
        repo.mkdir()
        (repo / ".git").mkdir()
        out = sync_snapshot(str(src), dry_run=False)
        _assert(out["status"] == "ok")
        _assert((repo / "data_pc" / "data_pc_origin" / "verify.py").is_file())


def _gate_p23_g_03_a_1() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        src = Path(tmp) / "src"
        repo = src / "GC-auto-push"
        pkg = src / "data_pc_origin" / "tests"
        pkg.mkdir(parents=True)
        (pkg / "sample.py").write_text("x=1\n", encoding="utf-8")
        cache = pkg / "__pycache__"
        cache.mkdir()
        (cache / "sample.cpython-313.pyc").write_bytes(b"bad")
        (src / "data_pc_runtime").mkdir()
        (src / "data_pc_runtime" / "verify.py").write_text("# rt\n", encoding="utf-8")
        (src / "data_pc_watch.py").write_text("# w\n", encoding="utf-8")
        (src / "data_pc_watchdog.py").write_text("# d\n", encoding="utf-8")
        (src / "촉매 반응 계산.py").write_text("# c\n", encoding="utf-8")
        for name in (
            "gc_data_pc_watch_loop.bat",
            "gc_data_pc_ensure_watch.bat",
            "gc_data_pc_ensure_watch_hidden.vbs",
            "gc_data_pc_start_watch_hidden.vbs",
        ):
            (src / name).write_text("rem\n", encoding="utf-8")
        repo.mkdir()
        (repo / ".git").mkdir()
        sync_snapshot(str(src), dry_run=False)
        _assert(not (repo / "data_pc" / "data_pc_origin" / "tests" / "__pycache__").exists())


def _gate_p23_g_04_a_1() -> None:
    _assert(github_push_enabled({GITHUB_PUSH_ENV: "1"}))
    _assert(not github_push_enabled({GITHUB_PUSH_ENV: "0"}))


def _gate_p23_h_01_a_1() -> None:
    root = Path(__file__).resolve().parents[2]
    out = run_live_github_snapshot(artifact_dir=root, script_dir=_script_dir())
    _assert(out["status"] in ("ok", "partial"))
    _assert(out.get("artifact_valid") is True)


def _gate_p23_h_02_a_1() -> None:
    root = Path(__file__).resolve().parents[2]
    _assert((root / ARTIFACT_NAME).is_file())


def _gate_p23_h_03_a_1() -> None:
    saved = os.environ.pop(GITHUB_PUSH_ENV, None)
    try:
        out = run_live_github_snapshot(script_dir=_script_dir(), do_push=True)
        _assert(out["mode"] == "push")
        _assert(out["status"] == "skipped")
    finally:
        if saved is not None:
            os.environ[GITHUB_PUSH_ENV] = saved


def _gate_p23_h_04_a_1() -> None:
    root = Path(__file__).resolve().parents[2]
    out = run_live_github_snapshot(artifact_dir=root, script_dir=_script_dir())
    _assert(validate_github_snapshot_artifact(out))
    _assert(len(out["plan"]["entries"]) >= 9)


_P23_GATES: list[tuple[str, object]] = [
    ("P23-G-01-a-1", _gate_p23_g_01_a_1),
    ("P23-G-02-a-1", _gate_p23_g_02_a_1),
    ("P23-G-03-a-1", _gate_p23_g_03_a_1),
    ("P23-G-04-a-1", _gate_p23_g_04_a_1),
    ("P23-H-01-a-1", _gate_p23_h_01_a_1),
    ("P23-H-02-a-1", _gate_p23_h_02_a_1),
    ("P23-H-03-a-1", _gate_p23_h_03_a_1),
    ("P23-H-04-a-1", _gate_p23_h_04_a_1),
]


def register_p23_gates() -> None:
    for gate_id, fn in _P23_GATES:
        register_gate(gate_id, fn, depends=P23_DEPS[gate_id], layer="P23")  # type: ignore[arg-type]
