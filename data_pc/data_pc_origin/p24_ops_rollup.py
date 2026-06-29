# -*- coding: utf-8
"""P24 — operational closure rollup (P20–P23 single manifest)."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from data_pc_origin.gates.registry import P23_EXTENDED_ORDER
from data_pc_origin.p19_live_assert import assert_no_secrets
from data_pc_origin.p20_readiness import build_readiness_manifest
from data_pc_origin.p21_cutover import plan_cutover
from data_pc_origin.p22_autostart import build_autostart_manifest
from data_pc_origin.p23_github_snapshot import inspect_git_repo, plan_github_snapshot


@dataclass
class OpsRollupManifest:
    production_ready: bool
    reason: str
    gate_count: int
    layers: Dict[str, Any] = field(default_factory=dict)
    checks: List[str] = field(default_factory=list)
    failures: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "production_ready": self.production_ready,
            "reason": self.reason,
            "gate_count": self.gate_count,
            "layers": dict(self.layers),
            "checks": list(self.checks),
            "failures": list(self.failures),
        }


def build_ops_rollup_manifest(
    script_dir: str,
    *,
    dry_tick: bool = False,
) -> OpsRollupManifest:
    """P20 readiness + P21 cutover + P22 autostart + P23 github → 단일 ops manifest."""
    readiness = build_readiness_manifest(script_dir, dry_tick=dry_tick)
    autostart = build_autostart_manifest(script_dir)
    cutover = plan_cutover(script_dir)
    github = plan_github_snapshot(script_dir)
    git = inspect_git_repo(script_dir)

    checks: List[str] = []
    failures: List[str] = []
    layers: Dict[str, Any] = {
        "readiness": readiness.to_dict(),
        "cutover": cutover.to_dict(),
        "autostart": autostart.to_dict(),
        "github": github.to_dict(),
        "git": git.to_dict(),
    }

    if readiness.ready:
        checks.append("readiness")
    else:
        failures.append(f"readiness: {readiness.reason}")

    if readiness.full_e2e_ready:
        checks.append("full_e2e_ready")
    else:
        failures.append("full_e2e_ready false")

    if cutover.already_production:
        checks.append("cutover_production")
    else:
        failures.append("cutover pending")

    if autostart.ready:
        checks.append("autostart")
    else:
        failures.append(f"autostart: {autostart.reason}")

    if github.ready:
        checks.append("github_repo")
    else:
        failures.append(f"github: {github.reason}")

    if git.is_repo and git.remote_branch_exists:
        checks.append("github_remote_branch")
    else:
        failures.append("github remote branch missing")

    if dry_tick and "supervisor_dry_tick" in readiness.checks:
        checks.append("supervisor_dry_tick")

    production_ready = not failures
    return OpsRollupManifest(
        production_ready=production_ready,
        reason="production_ready" if production_ready else "; ".join(failures),
        gate_count=len(P23_EXTENDED_ORDER),
        layers=layers,
        checks=checks,
        failures=failures,
    )


def validate_ops_rollup_artifact(payload: Dict[str, Any]) -> bool:
    import json

    if not assert_no_secrets(json.dumps(payload, ensure_ascii=False)):
        return False
    manifest = payload.get("manifest")
    if not isinstance(manifest, dict):
        return False
    required = ("production_ready", "gate_count", "layers", "checks")
    return all(k in manifest for k in required)
