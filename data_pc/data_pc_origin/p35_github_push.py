# -*- coding: utf-8
"""P35 — GitHub push (P34 sync → feat/data-pc-origin remote)."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from data_pc_origin.gates.registry import P34_EXTENDED_ORDER
from data_pc_origin.p23_github_snapshot import (
    GITHUB_PUSH_ENV,
    SNAPSHOT_BRANCH,
    github_push_enabled,
    inspect_git_repo,
)
from data_pc_origin.p34_github_refresh import (
    plan_github_refresh_post33,
    push_github_refresh_post33,
    verify_dest_markers_post33,
)


@dataclass
class GithubPushPlan:
    push_ready: bool
    reason: str
    gate_count: int
    branch: str
    dest_markers_ok: bool
    snapshot_ready: bool
    ahead: int
    behind: int
    porcelain_count: int
    porcelain_sample: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "push_ready": self.push_ready,
            "reason": self.reason,
            "gate_count": self.gate_count,
            "branch": self.branch,
            "dest_markers_ok": self.dest_markers_ok,
            "snapshot_ready": self.snapshot_ready,
            "ahead": self.ahead,
            "behind": self.behind,
            "porcelain_count": self.porcelain_count,
            "porcelain_sample": list(self.porcelain_sample[:20]),
        }


def plan_github_push_post34(script_dir: str) -> GithubPushPlan:
    """P34 dest markers + git branch state."""
    refresh = plan_github_refresh_post33(script_dir)
    dest = verify_dest_markers_post33(script_dir)
    git = inspect_git_repo(script_dir)

    failures: List[str] = []
    if not refresh.snapshot_ready:
        failures.append(refresh.reason)
    if not dest.get("ok"):
        failures.append("dest_markers")
    if not git.is_repo:
        failures.append("not_git_repo")
    elif git.branch != SNAPSHOT_BRANCH:
        failures.append(f"branch={git.branch!r}")

    ready = not failures
    return GithubPushPlan(
        push_ready=ready,
        reason="push_ready" if ready else "; ".join(failures),
        gate_count=len(P34_EXTENDED_ORDER),
        branch=SNAPSHOT_BRANCH,
        dest_markers_ok=bool(dest.get("ok")),
        snapshot_ready=refresh.snapshot_ready,
        ahead=git.ahead,
        behind=git.behind,
        porcelain_count=len(git.porcelain),
        porcelain_sample=list(git.porcelain),
    )


def push_github_post34(
    script_dir: str,
    *,
    message: Optional[str] = None,
) -> Dict[str, Any]:
    """`DATA_PC_GITHUB_PUSH=1` — sync+commit+push via P34."""
    plan = plan_github_push_post34(script_dir)
    if not plan.push_ready:
        return {"status": "error", "stage": "plan", "plan": plan.to_dict()}

    if not github_push_enabled():
        return {
            "status": "skipped",
            "stage": "push_gate",
            "reason": f"set {GITHUB_PUSH_ENV}=1",
            "plan": plan.to_dict(),
        }

    msg = message or f"chore(data-pc): P35 github push ({plan.gate_count} gates)"
    push = push_github_refresh_post33(script_dir, message=msg)
    git_after = inspect_git_repo(script_dir)
    remote_synced = git_after.ahead == 0 and git_after.behind == 0
    return {
        "status": push.get("status", "error"),
        "stage": "push",
        "plan": plan.to_dict(),
        "push": push,
        "git_after": git_after.to_dict(),
        "remote_synced": remote_synced,
    }


def validate_github_push_post34_artifact(payload: Dict[str, Any]) -> bool:
    if payload.get("status") not in ("ok", "skipped", "partial"):
        return False
    plan = payload.get("plan")
    if not isinstance(plan, dict):
        return False
    return plan.get("gate_count", 0) >= 254 and "dest_markers_ok" in plan
