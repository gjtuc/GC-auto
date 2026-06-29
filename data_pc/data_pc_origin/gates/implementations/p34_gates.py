# -*- coding: utf-8
"""P34 L4 gate bodies — GitHub refresh (P32–P33)."""

from __future__ import annotations

import os
import subprocess
import tempfile
from pathlib import Path

from data_pc_origin.gates.registry import P34_DEPS, register_gate
from data_pc_origin.live_p34_github_refresh import ARTIFACT_NAME, run_live_p34_github_refresh
from data_pc_origin.p23_github_snapshot import GITHUB_PUSH_ENV, SNAPSHOT_BRANCH, github_push_enabled
from data_pc_origin.p34_github_refresh import (
    plan_github_refresh_post33,
    sync_github_refresh_post33,
    validate_github_refresh_post33_artifact,
    verify_dest_markers_post33,
)


def _assert(condition: bool, msg: str = "") -> None:
    if not condition:
        raise AssertionError(msg or "assertion failed")


def _script_dir() -> str:
    return str(Path(__file__).resolve().parents[2].parent)


def _seed_min_repo(src: Path, repo: Path) -> None:
    (src / "data_pc_origin").mkdir(parents=True)
    for name in (
        "verify.py",
        "p32_github_refresh.py",
        "live_p32_github_refresh.py",
        "p33_github_push.py",
        "live_p33_github_push.py",
    ):
        (src / "data_pc_origin" / name).write_text("# x\n", encoding="utf-8")
    for doc in ("P32.md", "P33.md"):
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


def _gate_p34_g_01_a_1() -> None:
    plan = plan_github_refresh_post33(_script_dir())
    _assert(plan.snapshot_ready, plan.reason)
    _assert(plan.gate_count >= 246)
    _assert(plan.branch == SNAPSHOT_BRANCH)


def _gate_p34_g_02_a_1() -> None:
    plan = plan_github_refresh_post33(_script_dir())
    _assert(plan.markers_ready)
    _assert(all(m.source_ok for m in plan.markers))


def _gate_p34_g_03_a_1() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        src = Path(tmp) / "src"
        repo = src / "GC-auto-push"
        _seed_min_repo(src, repo)
        out = sync_github_refresh_post33(str(src), dry_run=False)
        _assert(out["status"] == "ok")
        markers = verify_dest_markers_post33(str(src))
        _assert(markers["ok"])


def _gate_p34_g_04_a_1() -> None:
    _assert(github_push_enabled({GITHUB_PUSH_ENV: "1"}))
    _assert(not github_push_enabled({GITHUB_PUSH_ENV: "0"}))


def _gate_p34_h_01_a_1() -> None:
    root = Path(__file__).resolve().parents[2]
    out = run_live_p34_github_refresh(artifact_dir=root, script_dir=_script_dir())
    _assert(out["status"] in ("ok", "partial"))
    _assert(out.get("artifact_valid") is True)


def _gate_p34_h_02_a_1() -> None:
    root = Path(__file__).resolve().parents[2]
    _assert((root / ARTIFACT_NAME).is_file())


def _gate_p34_h_03_a_1() -> None:
    saved = os.environ.pop(GITHUB_PUSH_ENV, None)
    try:
        out = run_live_p34_github_refresh(script_dir=_script_dir(), do_push=True)
        _assert(out["mode"] == "push")
        _assert(out["status"] == "skipped")
    finally:
        if saved is not None:
            os.environ[GITHUB_PUSH_ENV] = saved


def _gate_p34_h_04_a_1() -> None:
    root = Path(__file__).resolve().parents[2]
    out = run_live_p34_github_refresh(artifact_dir=root, script_dir=_script_dir())
    _assert(validate_github_refresh_post33_artifact(out))
    _assert(out["plan"]["markers_ready"] is True)


_P34_GATES: list[tuple[str, object]] = [
    ("P34-G-01-a-1", _gate_p34_g_01_a_1),
    ("P34-G-02-a-1", _gate_p34_g_02_a_1),
    ("P34-G-03-a-1", _gate_p34_g_03_a_1),
    ("P34-G-04-a-1", _gate_p34_g_04_a_1),
    ("P34-H-01-a-1", _gate_p34_h_01_a_1),
    ("P34-H-02-a-1", _gate_p34_h_02_a_1),
    ("P34-H-03-a-1", _gate_p34_h_03_a_1),
    ("P34-H-04-a-1", _gate_p34_h_04_a_1),
]


def register_p34_gates() -> None:
    for gate_id, fn in _P34_GATES:
        register_gate(gate_id, fn, depends=P34_DEPS[gate_id], layer="P34")  # type: ignore[arg-type]
