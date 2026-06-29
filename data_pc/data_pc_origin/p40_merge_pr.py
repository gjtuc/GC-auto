# -*- coding: utf-8 -*-
"""P40 — merge PR refresh (feat/data-pc-origin → main, post-P41)."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List

from data_pc_origin.gates.registry import P41_EXTENDED_ORDER
from data_pc_origin.p28_merge_readiness import (
    MERGE_PR_ENV,
    STRUCTURAL_CHECKS,
    build_merge_readiness_manifest_post41,
    create_merge_pr_post41 as gh_create_merge_pr_post41,
    merge_pr_enabled,
    merge_structural_ready,
)
from data_pc_origin.p31_merge_pr import gh_available
from data_pc_origin.p39_github_push import plan_github_push_post38
from data_pc_origin.p41_manifest import plan_stack_manifest_post40

# P41-EXT 이후 최소 gate count (P40 merge PR 게이트·artifact 검증)
_MIN_P41_EXT_GATES = 310
_MIN_STACK_GATES = 616


@dataclass
class MergePrPlan:
    pr_ready: bool
    reason: str
    gate_count: int
    stack_gate_count: int
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
            "stack_gate_count": self.stack_gate_count,
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


def plan_merge_pr_post41(script_dir: str) -> MergePrPlan:
    """P39 push + P41 stack manifest — structural merge readiness."""
    push = plan_github_push_post38(script_dir)
    manifest = build_merge_readiness_manifest_post41(script_dir)
    stack = plan_stack_manifest_post40(script_dir)
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

    if stack.ready:
        checks.append("stack_manifest_ready")
    else:
        failures.append(f"stack: {stack.reason}")

    if gh_ok:
        checks.append("gh_auth")

    pr_ready = push.push_ready and remote_synced and structural and stack.ready
    return MergePrPlan(
        pr_ready=pr_ready,
        reason="pr_ready" if pr_ready else "; ".join(failures),
        gate_count=len(P41_EXTENDED_ORDER),
        stack_gate_count=stack.stack_gate_count,
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


# 하위 호환 — 게이트 ID 는 P40-M 이지만 post-P41 manifest 사용
plan_merge_pr_post39 = plan_merge_pr_post41


def create_merge_pr_post41(script_dir: str) -> Dict[str, Any]:
    """`gh pr create` — `DATA_PC_MERGE_PR=1` + gh auth + readiness."""
    plan = plan_merge_pr_post41(script_dir)
    manifest = build_merge_readiness_manifest_post41(script_dir)

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

    result = gh_create_merge_pr_post41(script_dir)
    result["plan"] = plan.to_dict()
    return result


create_merge_pr_post39 = create_merge_pr_post41


def validate_merge_pr_post41_artifact(payload: Dict[str, Any]) -> bool:
    if payload.get("status") not in ("ok", "skipped", "partial"):
        return False
    plan = payload.get("plan")
    if not isinstance(plan, dict):
        return False
    return (
        plan.get("gate_count", 0) >= _MIN_P41_EXT_GATES
        and plan.get("structural_ready") is True
        and plan.get("stack_gate_count", 0) >= _MIN_STACK_GATES
    )


validate_merge_pr_post39_artifact = validate_merge_pr_post41_artifact
