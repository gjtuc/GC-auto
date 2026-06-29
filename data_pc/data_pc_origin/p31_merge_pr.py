# -*- coding: utf-8
"""P31 — merge PR (P30 push → feat/data-pc-origin → main)."""

from __future__ import annotations

import subprocess
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from data_pc_origin.gates.registry import P30_EXTENDED_ORDER
from data_pc_origin.p28_merge_readiness import (
    MERGE_PR_ENV,
    MergeReadinessManifest,
    STRUCTURAL_CHECKS,
    build_merge_readiness_manifest,
    create_merge_pr,
    merge_pr_enabled,
    merge_structural_ready,
)
from data_pc_origin.p30_github_push import plan_github_push_post29


@dataclass
class MergePrPlan:
    pr_ready: bool
    reason: str
    gate_count: int
    branch: str
    base: str
    push_ready: bool
    remote_synced: bool
    structural_ready: bool
    ops_ready: bool
    gh_available: bool
    checks: List[str] = field(default_factory=list)
    failures: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "pr_ready": self.pr_ready,
            "reason": self.reason,
            "gate_count": self.gate_count,
            "branch": self.branch,
            "base": self.base,
            "push_ready": self.push_ready,
            "remote_synced": self.remote_synced,
            "structural_ready": self.structural_ready,
            "ops_ready": self.ops_ready,
            "gh_available": self.gh_available,
            "checks": list(self.checks),
            "failures": list(self.failures),
        }


def gh_available() -> bool:
    try:
        proc = subprocess.run(
            ["gh", "auth", "status"],
            capture_output=True,
            text=True,
            check=False,
        )
        out = ((proc.stdout or "") + (proc.stderr or "")).lower()
        return proc.returncode == 0 and "logged in" in out
    except OSError:
        return False


def plan_merge_pr_post30(script_dir: str) -> MergePrPlan:
    """P30 push state + P28 manifest (structural merge readiness)."""
    push = plan_github_push_post29(script_dir)
    manifest = build_merge_readiness_manifest(script_dir)
    structural = merge_structural_ready(manifest)
    remote_synced = push.ahead == 0 and push.behind == 0
    gh_ok = gh_available()

    checks: List[str] = []
    failures: List[str] = []

    if push.push_ready:
        checks.append("push_ready")
    else:
        failures.append(f"push: {push.reason}")

    if remote_synced:
        checks.append("remote_synced")
    else:
        failures.append(f"ahead={push.ahead} behind={push.behind}")

    if structural:
        checks.append("structural_ready")
    else:
        missing = sorted(STRUCTURAL_CHECKS - set(manifest.checks))
        failures.append(f"structural:{','.join(missing)}")

    if manifest.ops_ready:
        checks.append("ops_ready")
    else:
        failures.append(f"ops: {manifest.reason}")

    if gh_ok:
        checks.append("gh_auth")

    pr_ready = push.push_ready and remote_synced and structural
    return MergePrPlan(
        pr_ready=pr_ready,
        reason="pr_ready" if pr_ready else "; ".join(failures),
        gate_count=len(P30_EXTENDED_ORDER),
        branch=manifest.branch,
        base=manifest.base,
        push_ready=push.push_ready,
        remote_synced=remote_synced,
        structural_ready=structural,
        ops_ready=manifest.ops_ready,
        gh_available=gh_ok,
        checks=checks,
        failures=failures,
    )


def create_merge_pr_post30(script_dir: str) -> Dict[str, Any]:
    """`gh pr create` — `DATA_PC_MERGE_PR=1` + gh auth + structural readiness."""
    plan = plan_merge_pr_post30(script_dir)
    manifest = build_merge_readiness_manifest(script_dir)

    if not plan.pr_ready:
        return {"status": "error", "stage": "plan", "plan": plan.to_dict(), "manifest": manifest.to_dict()}

    if not merge_pr_enabled():
        return {
            "status": "skipped",
            "stage": "pr_gate",
            "reason": f"set {MERGE_PR_ENV}=1",
            "plan": plan.to_dict(),
            "manifest": manifest.to_dict(),
        }

    if not plan.gh_available:
        return {
            "status": "error",
            "stage": "gh_auth",
            "detail": "run: gh auth login",
            "plan": plan.to_dict(),
            "manifest": manifest.to_dict(),
        }

    result = create_merge_pr(script_dir)
    result["plan"] = plan.to_dict()
    return result


def validate_merge_pr_artifact(payload: Dict[str, Any]) -> bool:
    if payload.get("status") not in ("ok", "skipped", "partial"):
        return False
    plan = payload.get("plan")
    if not isinstance(plan, dict):
        return False
    return plan.get("gate_count", 0) >= 222 and plan.get("structural_ready") is True
