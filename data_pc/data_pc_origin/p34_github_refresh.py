# -*- coding: utf-8
"""P34 — GitHub refresh sync (P32–P33 → feat/data-pc-origin)."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

from data_pc_origin.gates.registry import P33_EXTENDED_ORDER
from data_pc_origin.p23_github_snapshot import (
    SNAPSHOT_BRANCH,
    _write_snapshot_readme,
    data_pc_dest,
    plan_github_snapshot,
    push_snapshot,
    repo_root_path,
    sync_snapshot,
)

REFRESH_MARKER_FILES: tuple[str, ...] = (
    "p32_github_refresh.py",
    "live_p32_github_refresh.py",
    "p33_github_push.py",
    "live_p33_github_push.py",
)

REFRESH_MARKER_DOCS: tuple[str, ...] = (
    "design/catalog/P32.md",
    "design/catalog/P33.md",
)


@dataclass
class RefreshMarkerCheck:
    relpath: str
    source_ok: bool
    dest_ok: bool

    def to_dict(self) -> Dict[str, Any]:
        return {"relpath": self.relpath, "source_ok": self.source_ok, "dest_ok": self.dest_ok}


@dataclass
class GithubRefreshPlan:
    snapshot_ready: bool
    reason: str
    gate_count: int
    branch: str
    markers: List[RefreshMarkerCheck] = field(default_factory=list)
    markers_ready: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return {
            "snapshot_ready": self.snapshot_ready,
            "reason": self.reason,
            "gate_count": self.gate_count,
            "branch": self.branch,
            "markers": [m.to_dict() for m in self.markers],
            "markers_ready": self.markers_ready,
        }


def _collect_markers(script_dir: str) -> List[RefreshMarkerCheck]:
    root = Path(script_dir)
    dest_root = data_pc_dest(repo_root_path(script_dir)) / "data_pc_origin"
    checks: List[RefreshMarkerCheck] = []

    for name in REFRESH_MARKER_FILES:
        src = root / "data_pc_origin" / name
        dst = dest_root / name
        checks.append(
            RefreshMarkerCheck(
                relpath=f"data_pc_origin/{name}",
                source_ok=src.is_file(),
                dest_ok=dst.is_file(),
            )
        )
    for doc in REFRESH_MARKER_DOCS:
        src = root / "data_pc_origin" / doc
        dst = dest_root / doc
        checks.append(
            RefreshMarkerCheck(
                relpath=f"data_pc_origin/{doc}",
                source_ok=src.is_file(),
                dest_ok=dst.is_file(),
            )
        )
    return checks


def plan_github_refresh_post33(script_dir: str) -> GithubRefreshPlan:
    """P23 snapshot + P32–P33 marker readiness."""
    snap = plan_github_snapshot(script_dir)
    markers = _collect_markers(script_dir)
    source_ok = all(m.source_ok for m in markers)

    failures: List[str] = []
    if not snap.ready:
        failures.append(snap.reason)
    if not source_ok:
        missing = [m.relpath for m in markers if not m.source_ok]
        failures.append(f"missing_markers:{','.join(missing)}")

    ready = not failures
    return GithubRefreshPlan(
        snapshot_ready=snap.ready,
        reason="ready" if ready else "; ".join(failures),
        gate_count=len(P33_EXTENDED_ORDER),
        branch=SNAPSHOT_BRANCH,
        markers=markers,
        markers_ready=source_ok,
    )


def verify_dest_markers_post33(script_dir: str) -> Dict[str, Any]:
    markers = _collect_markers(script_dir)
    return {
        "ok": all(m.dest_ok for m in markers),
        "markers": [m.to_dict() for m in markers],
    }


def sync_github_refresh_post33(script_dir: str, *, dry_run: bool = False) -> Dict[str, Any]:
    plan = plan_github_refresh_post33(script_dir)
    if not plan.snapshot_ready or not plan.markers_ready:
        return {"status": "error", "reason": plan.reason, "plan": plan.to_dict()}

    sync = sync_snapshot(script_dir, dry_run=dry_run)
    if sync["status"] != "ok":
        return {"status": "error", "stage": "sync", "sync": sync, "plan": plan.to_dict()}

    if not dry_run:
        readme = data_pc_dest(repo_root_path(script_dir)) / "data_pc_origin" / "ORIGIN_SNAPSHOT.md"
        _write_snapshot_readme(readme, plan.gate_count)

    dest_markers = verify_dest_markers_post33(script_dir) if not dry_run else {"ok": True, "markers": []}
    return {
        "status": "ok",
        "dry_run": dry_run,
        "sync": sync,
        "plan": plan.to_dict(),
        "dest_markers": dest_markers,
    }


def push_github_refresh_post33(
    script_dir: str,
    *,
    message: Optional[str] = None,
) -> Dict[str, Any]:
    sync = sync_github_refresh_post33(script_dir, dry_run=False)
    if sync["status"] != "ok":
        return {"status": "error", "stage": "sync", "sync": sync}

    msg = message or f"chore(data-pc): P34 github refresh ({len(P33_EXTENDED_ORDER)} gates)"
    push = push_snapshot(script_dir, message=msg)
    push["refresh"] = sync
    push["dest_markers"] = verify_dest_markers_post33(script_dir)
    return push


def validate_github_refresh_post33_artifact(payload: Dict[str, Any]) -> bool:
    if payload.get("status") not in ("ok", "skipped", "partial"):
        return False
    plan = payload.get("plan")
    if not isinstance(plan, dict):
        return False
    return plan.get("gate_count", 0) >= 246 and "markers" in plan
