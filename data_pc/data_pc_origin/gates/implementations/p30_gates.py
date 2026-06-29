# -*- coding: utf-8
"""P30 L4 gate bodies — GitHub push."""

from __future__ import annotations

import os
import subprocess
import tempfile
from pathlib import Path

from data_pc_origin.gates.registry import P30_DEPS, register_gate
from data_pc_origin.live_p30_github_push import ARTIFACT_NAME, run_live_p30_github_push
from data_pc_origin.p23_github_snapshot import GITHUB_PUSH_ENV, SNAPSHOT_BRANCH, github_push_enabled
from data_pc_origin.p30_github_push import (
    plan_github_push_post29,
    validate_github_push_post29_artifact,
)
from data_pc_origin.p29_github_refresh import sync_github_refresh_post28, verify_dest_markers_post28


def _assert(condition: bool, msg: str = "") -> None:
    if not condition:
        raise AssertionError(msg or "assertion failed")


def _script_dir() -> str:
    return str(Path(__file__).resolve().parents[2].parent)


def _seed_min_repo(src: Path, repo: Path) -> None:
    (src / "data_pc_origin").mkdir(parents=True)
    for name in (
        "verify.py",
        "p27_github_refresh.py",
        "live_github_refresh.py",
        "p28_merge_readiness.py",
        "live_merge_readiness.py",
    ):
        (src / "data_pc_origin" / name).write_text("# x\n", encoding="utf-8")
    for doc in ("P27.md", "P28.md"):
        (src / "data_pc_origin" / "design" / "catalog").mkdir(parents=True, exist_ok=True)
        (src / "data_pc_origin" / "design" / "catalog" / doc).write_text("# d\n", encoding="utf-8")
    (src / "data_pc_runtime").mkdir()
    (src / "data_pc_runtime" / "verify.py").write_text("# r\n", encoding="utf-8")
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
    subprocess.run(
        ["git", "init", "-b", SNAPSHOT_BRANCH],
        cwd=str(repo),
        check=True,
        capture_output=True,
    )


def _gate_p30_g_01_a_1() -> None:
    plan = plan_github_push_post29(_script_dir())
    _assert(plan.push_ready, plan.reason)
    _assert(plan.gate_count >= 214)
    _assert(plan.branch == SNAPSHOT_BRANCH)
    _assert(plan.dest_markers_ok)


def _gate_p30_g_02_a_1() -> None:
    _assert(github_push_enabled({GITHUB_PUSH_ENV: "1"}))
    _assert(not github_push_enabled({GITHUB_PUSH_ENV: "0"}))


def _gate_p30_g_03_a_1() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        src = Path(tmp) / "src"
        repo = src / "GC-auto-push"
        _seed_min_repo(src, repo)
        sync = sync_github_refresh_post28(str(src), dry_run=False)
        _assert(sync["status"] == "ok")
        markers = verify_dest_markers_post28(str(src))
        _assert(markers["ok"])
        plan = plan_github_push_post29(str(src))
        _assert(plan.push_ready)
        _assert(plan.dest_markers_ok)


def _gate_p30_g_04_a_1() -> None:
    plan = plan_github_push_post29(_script_dir())
    _assert(plan.snapshot_ready)


def _gate_p30_h_01_a_1() -> None:
    root = Path(__file__).resolve().parents[2]
    out = run_live_p30_github_push(artifact_dir=root, script_dir=_script_dir())
    _assert(out["status"] in ("ok", "partial"))
    _assert(out.get("artifact_valid") is True)


def _gate_p30_h_02_a_1() -> None:
    root = Path(__file__).resolve().parents[2]
    _assert((root / ARTIFACT_NAME).is_file())


def _gate_p30_h_03_a_1() -> None:
    saved = os.environ.pop(GITHUB_PUSH_ENV, None)
    try:
        out = run_live_p30_github_push(script_dir=_script_dir(), do_push=True)
        _assert(out["mode"] == "push")
        _assert(out["status"] == "skipped")
    finally:
        if saved is not None:
            os.environ[GITHUB_PUSH_ENV] = saved


def _gate_p30_h_04_a_1() -> None:
    root = Path(__file__).resolve().parents[2]
    out = run_live_p30_github_push(artifact_dir=root, script_dir=_script_dir())
    _assert(validate_github_push_post29_artifact(out))
    _assert(out["plan"]["dest_markers_ok"] is True)


_P30_GATES: list[tuple[str, object]] = [
    ("P30-G-01-a-1", _gate_p30_g_01_a_1),
    ("P30-G-02-a-1", _gate_p30_g_02_a_1),
    ("P30-G-03-a-1", _gate_p30_g_03_a_1),
    ("P30-G-04-a-1", _gate_p30_g_04_a_1),
    ("P30-H-01-a-1", _gate_p30_h_01_a_1),
    ("P30-H-02-a-1", _gate_p30_h_02_a_1),
    ("P30-H-03-a-1", _gate_p30_h_03_a_1),
    ("P30-H-04-a-1", _gate_p30_h_04_a_1),
]


def register_p30_gates() -> None:
    for gate_id, fn in _P30_GATES:
        register_gate(gate_id, fn, depends=P30_DEPS[gate_id], layer="P30")  # type: ignore[arg-type]
