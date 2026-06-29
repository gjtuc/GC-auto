# -*- coding: utf-8
"""P23 — GitHub feat/data-pc-origin snapshot sync · push."""

from __future__ import annotations

import os
import shutil
import subprocess
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Tuple

from data_pc_origin.gates.registry import P22_EXTENDED_ORDER

GITHUB_PUSH_ENV = "DATA_PC_GITHUB_PUSH"
SNAPSHOT_BRANCH = "feat/data-pc-origin"
REPO_DIRNAME = "GC-auto-push"
DATA_PC_SUBDIR = "data_pc"
REMOTE_NAME = "origin"

SNAPSHOT_RELPATHS: Tuple[str, ...] = (
    "data_pc_origin",
    "data_pc_runtime",
    "data_pc_watch.py",
    "data_pc_watchdog.py",
    "촉매 반응 계산.py",
    "gc_data_pc_watch_loop.bat",
    "gc_data_pc_ensure_watch.bat",
    "gc_data_pc_ensure_watch_hidden.vbs",
    "gc_data_pc_start_watch_hidden.vbs",
)

SNAPSHOT_EXCLUDE_DIRS = frozenset({"__pycache__", ".pytest_cache", ".git"})
SNAPSHOT_EXCLUDE_SUFFIXES = (".pyc",)
SNAPSHOT_EXCLUDE_GLOBS = ("live_*_result.json",)


@dataclass
class SnapshotEntry:
    relpath: str
    source_exists: bool
    dest_relpath: str
    action: str = "skip"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "relpath": self.relpath,
            "source_exists": self.source_exists,
            "dest_relpath": self.dest_relpath,
            "action": self.action,
        }


@dataclass
class SnapshotPlan:
    script_dir: str
    repo_root: str
    branch: str
    entries: List[SnapshotEntry] = field(default_factory=list)
    gate_count: int = 0
    ready: bool = False
    reason: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "script_dir": self.script_dir,
            "repo_root": self.repo_root,
            "branch": self.branch,
            "entries": [e.to_dict() for e in self.entries],
            "gate_count": self.gate_count,
            "ready": self.ready,
            "reason": self.reason,
        }


@dataclass
class GitRepoStatus:
    repo_root: str
    branch: str
    is_repo: bool
    remote_branch_exists: bool
    porcelain: List[str] = field(default_factory=list)
    ahead: int = 0
    behind: int = 0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "repo_root": self.repo_root,
            "branch": self.branch,
            "is_repo": self.is_repo,
            "remote_branch_exists": self.remote_branch_exists,
            "porcelain_count": len(self.porcelain),
            "porcelain_sample": self.porcelain[:20],
            "ahead": self.ahead,
            "behind": self.behind,
        }


def github_push_enabled(environ: Optional[Dict[str, str]] = None) -> bool:
    env = environ if environ is not None else os.environ
    return env.get(GITHUB_PUSH_ENV, "").strip().lower() in ("1", "true", "yes", "on")


def repo_root_path(script_dir: str) -> Path:
    return Path(script_dir) / REPO_DIRNAME


def data_pc_dest(repo_root: Path) -> Path:
    return repo_root / DATA_PC_SUBDIR


def _should_exclude(name: str) -> bool:
    if name in SNAPSHOT_EXCLUDE_DIRS:
        return True
    return any(name.endswith(s) for s in SNAPSHOT_EXCLUDE_SUFFIXES)


def _dest_relpath(source_relpath: str) -> str:
    return f"{DATA_PC_SUBDIR}/{source_relpath}".replace("\\", "/")


def plan_github_snapshot(script_dir: str) -> SnapshotPlan:
    """운영 .cursor → GC-auto-push/data_pc 동기화 계획."""
    root = Path(script_dir)
    repo = repo_root_path(script_dir)
    entries: List[SnapshotEntry] = []
    missing = 0

    for rel in SNAPSHOT_RELPATHS:
        src = root / rel
        exists = src.is_file() or src.is_dir()
        if not exists:
            missing += 1
        entries.append(
            SnapshotEntry(
                relpath=rel,
                source_exists=exists,
                dest_relpath=_dest_relpath(rel),
                action="copy" if exists else "missing",
            )
        )

    gate_count = len(P22_EXTENDED_ORDER)
    ready = missing == 0 and repo.is_dir() and (repo / ".git").is_dir()
    reason = "ready"
    if not repo.is_dir():
        reason = "repo_missing"
    elif not (repo / ".git").is_dir():
        reason = "not_git_repo"
    elif missing:
        reason = f"missing_sources:{missing}"

    return SnapshotPlan(
        script_dir=str(root),
        repo_root=str(repo),
        branch=SNAPSHOT_BRANCH,
        entries=entries,
        gate_count=gate_count,
        ready=ready,
        reason=reason,
    )


def _copy_tree(src: Path, dst: Path) -> int:
    copied = 0
    if dst.exists():
        shutil.rmtree(dst)
    dst.mkdir(parents=True, exist_ok=True)
    for item in src.rglob("*"):
        if any(p.name in SNAPSHOT_EXCLUDE_DIRS for p in item.parents):
            continue
        if _should_exclude(item.name):
            continue
        if any(item.match(g) for g in SNAPSHOT_EXCLUDE_GLOBS):
            continue
        rel = item.relative_to(src)
        target = dst / rel
        if item.is_dir():
            target.mkdir(parents=True, exist_ok=True)
        else:
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(item, target)
            copied += 1
    return copied


def _copy_file(src: Path, dst: Path) -> int:
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dst)
    return 1


def sync_snapshot(script_dir: str, *, dry_run: bool = False) -> Dict[str, Any]:
    """snapshot 경로를 repo data_pc/ 로 복사."""
    plan = plan_github_snapshot(script_dir)
    if not plan.ready:
        return {"status": "error", "reason": plan.reason, "plan": plan.to_dict(), "copied": 0}

    repo = Path(plan.repo_root)
    dest_root = data_pc_dest(repo)
    copied = 0
    actions: List[Dict[str, Any]] = []

    for entry in plan.entries:
        if not entry.source_exists:
            continue
        src = Path(plan.script_dir) / entry.relpath
        dst = dest_root / entry.relpath
        if dry_run:
            actions.append({"relpath": entry.relpath, "action": "would_copy"})
            continue
        if src.is_dir():
            n = _copy_tree(src, dst)
        else:
            n = _copy_file(src, dst)
        copied += n
        actions.append({"relpath": entry.relpath, "action": "copied", "files": n})

    if not dry_run:
        _write_snapshot_readme(dest_root / "data_pc_origin" / "ORIGIN_SNAPSHOT.md", plan.gate_count)

    return {
        "status": "ok",
        "dry_run": dry_run,
        "copied": copied,
        "actions": actions,
        "plan": plan.to_dict(),
    }


def _write_snapshot_readme(path: Path, gate_count: int) -> None:
    stamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    text = f"""# Origin 자동화 스냅샷 — `{SNAPSHOT_BRANCH}`

> **main에 병합하지 않은 백업 브랜치**. 문제 시 이 브랜치에서 복구.

## 포함 (P23 sync {stamp})

- `data_pc/data_pc_origin/` — O0..O9 + P층 ({gate_count} gates)
- `data_pc/data_pc_runtime/` — L0..L4 supervisor
- `data_pc/data_pc_watch.py` · `data_pc_watchdog.py` · autostart bat/VBS
- `data_pc/촉매 반응 계산.py` — origin pipeline 위임

## 검증 (repo `data_pc` 기준)

```bash
cd data_pc
python -m data_pc_origin.verify --p26
python -m data_pc_origin.live_ops_rollup
```

## 운영 PC

차헌 PC 실사용: `Desktop\\.cursor\\` — P23 harness가 GC-auto-push로 sync.
"""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _run_git(repo_root: Path, *args: str) -> Tuple[int, str]:
    try:
        proc = subprocess.run(
            ["git", *args],
            cwd=str(repo_root),
            capture_output=True,
            text=True,
            check=False,
        )
        out = (proc.stdout or "") + (proc.stderr or "")
        return proc.returncode, out.strip()
    except OSError as exc:
        return 127, str(exc)


def inspect_git_repo(script_dir: str) -> GitRepoStatus:
    repo = repo_root_path(script_dir)
    if not (repo / ".git").is_dir():
        return GitRepoStatus(
            repo_root=str(repo),
            branch="",
            is_repo=False,
            remote_branch_exists=False,
        )

    _, branch_out = _run_git(repo, "branch", "--show-current")
    branch = branch_out.splitlines()[0].strip() if branch_out else ""

    _, remote_out = _run_git(repo, "branch", "-r", "--list", f"{REMOTE_NAME}/{SNAPSHOT_BRANCH}")
    remote_exists = SNAPSHOT_BRANCH in remote_out

    _, porcelain_out = _run_git(repo, "status", "--porcelain")
    lines = [ln for ln in porcelain_out.splitlines() if ln.strip()]

    ahead, behind = 0, 0
    if remote_exists:
        code, ab = _run_git(repo, "rev-list", "--left-right", "--count", f"{REMOTE_NAME}/{SNAPSHOT_BRANCH}...HEAD")
        if code == 0 and ab:
            parts = ab.split()
            if len(parts) == 2:
                behind, ahead = int(parts[0]), int(parts[1])

    return GitRepoStatus(
        repo_root=str(repo),
        branch=branch,
        is_repo=True,
        remote_branch_exists=remote_exists,
        porcelain=lines,
        ahead=ahead,
        behind=behind,
    )


def push_snapshot(
    script_dir: str,
    *,
    message: Optional[str] = None,
) -> Dict[str, Any]:
    """checkout → sync → commit → push (호출 전 github_push_enabled 확인)."""
    repo = repo_root_path(script_dir)
    code, checkout_out = _run_git(repo, "checkout", SNAPSHOT_BRANCH)
    if code != 0:
        _run_git(repo, "fetch", REMOTE_NAME, SNAPSHOT_BRANCH)
        code2, _ = _run_git(repo, "checkout", "-B", SNAPSHOT_BRANCH, f"{REMOTE_NAME}/{SNAPSHOT_BRANCH}")
        if code2 != 0:
            _run_git(repo, "checkout", "-b", SNAPSHOT_BRANCH)
            checkout_out = f"created local {SNAPSHOT_BRANCH}"

    sync = sync_snapshot(script_dir, dry_run=False)
    if sync["status"] != "ok":
        return {"status": "error", "stage": "sync", "checkout": checkout_out, "sync": sync}

    rel_paths = [_dest_relpath(e.relpath) for e in plan_github_snapshot(script_dir).entries if e.source_exists]
    _run_git(repo, "add", *rel_paths)
    _run_git(repo, "add", _dest_relpath("data_pc_origin/ORIGIN_SNAPSHOT.md"))

    commit_msg = message or f"chore(data-pc): P23 origin snapshot ({len(P22_EXTENDED_ORDER)} gates)"
    code, out = _run_git(repo, "commit", "-m", commit_msg)
    committed = code == 0
    if code != 0 and "nothing to commit" not in out.lower():
        return {"status": "error", "stage": "commit", "detail": out, "sync": sync}

    code, push_out = _run_git(repo, "push", "-u", REMOTE_NAME, SNAPSHOT_BRANCH)
    git_after = inspect_git_repo(script_dir)
    return {
        "status": "ok" if code == 0 else "error",
        "stage": "push" if code == 0 else "push_failed",
        "committed": committed,
        "push_detail": push_out,
        "checkout": checkout_out,
        "sync": sync,
        "git": git_after.to_dict(),
    }


def validate_github_snapshot_artifact(payload: Dict[str, Any]) -> bool:
    if payload.get("status") not in ("ok", "skipped", "partial"):
        return False
    if "plan" not in payload:
        return False
    plan = payload["plan"]
    if not isinstance(plan, dict):
        return False
    return "repo_root" in plan and "entries" in plan
