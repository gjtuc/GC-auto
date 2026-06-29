# -*- coding: utf-8
"""P28 — main merge readiness (feat/data-pc-origin → main PR prep)."""

from __future__ import annotations

import os
import subprocess
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from data_pc_origin.gates.registry import P30_EXTENDED_ORDER, P39_EXTENDED_ORDER
from data_pc_origin.p23_github_snapshot import (
    SNAPSHOT_BRANCH,
    inspect_git_repo,
    repo_root_path,
)
from data_pc_origin.p24_ops_rollup import build_ops_rollup_manifest
from data_pc_origin.p29_github_refresh import plan_github_refresh_post28, verify_dest_markers_post28
from data_pc_origin.p38_github_refresh import plan_github_refresh_post37, verify_dest_markers_post37

MERGE_PR_ENV = "DATA_PC_MERGE_PR"
MAIN_BRANCH = "main"
REMOTE_NAME = "origin"
# feat → main PR diff 허용 경로 — data_pc 파이프라인 + deploy 예제(env·machine template)
ALLOWED_PREFIXES = ("data_pc/", "deploy/")


@dataclass
class MergeReadinessManifest:
    ready: bool
    reason: str
    gate_count: int
    branch: str
    base: str
    ops_ready: bool
    github_sync_ready: bool
    checks: List[str] = field(default_factory=list)
    failures: List[str] = field(default_factory=list)
    diff_stat: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "ready": self.ready,
            "reason": self.reason,
            "gate_count": self.gate_count,
            "branch": self.branch,
            "base": self.base,
            "ops_ready": self.ops_ready,
            "github_sync_ready": self.github_sync_ready,
            "checks": list(self.checks),
            "failures": list(self.failures),
            "diff_stat": list(self.diff_stat[:30]),
        }


STRUCTURAL_CHECKS: frozenset[str] = frozenset(
    {
        "git_repo",
        "on_feat_branch",
        "remote_feat_branch",
        "github_markers_synced",
        "diff_vs_main",
        "data_pc_only_diff",
    }
)


def merge_structural_ready(manifest: MergeReadinessManifest) -> bool:
    return STRUCTURAL_CHECKS.issubset(set(manifest.checks))


def merge_pr_enabled(environ: Optional[Dict[str, str]] = None) -> bool:
    env = environ if environ is not None else os.environ
    return env.get(MERGE_PR_ENV, "").strip().lower() in ("1", "true", "yes", "on")


def _run_git(repo: Path, *args: str) -> Tuple[int, str]:
    try:
        proc = subprocess.run(
            ["git", *args],
            cwd=str(repo),
            capture_output=True,
            text=True,
            check=False,
        )
        return proc.returncode, ((proc.stdout or "") + (proc.stderr or "")).strip()
    except OSError as exc:
        return 127, str(exc)


def _diff_vs_main(repo: Path) -> Tuple[List[str], List[str], bool]:
    """--name-only for path checks; --stat for manifest display (truncated paths ok)."""
    triple = f"{REMOTE_NAME}/{MAIN_BRANCH}...HEAD"
    _run_git(repo, "fetch", REMOTE_NAME, MAIN_BRANCH)
    code_names, names_out = _run_git(repo, "diff", "--name-only", triple)
    code_stat, stat_out = _run_git(repo, "diff", "--stat", triple)
    if code_names != 0 or code_stat != 0:
        return [], [], False
    names = [ln.strip() for ln in names_out.splitlines() if ln.strip()]
    stat_lines = [
        ln
        for ln in stat_out.splitlines()
        if ln.strip() and " files changed" not in ln
    ]
    return names, stat_lines, True


def _normalize_diff_path(name: str) -> str:
    return name.strip().strip('"').strip("'").replace("\\", "/")


def _only_data_pc_paths(names: List[str]) -> bool:
    """diff vs main — ALLOWED_PREFIXES (data_pc/ · deploy/ 예제) 밖 경로 있으면 False."""
    if not names:
        return False
    for name in names:
        norm = _normalize_diff_path(name)
        if not any(norm.startswith(p) for p in ALLOWED_PREFIXES):
            return False
    return True


def build_merge_readiness_manifest(script_dir: str) -> MergeReadinessManifest:
    """P24 ops + P27 sync + git diff vs main."""
    repo = repo_root_path(script_dir)
    git = inspect_git_repo(script_dir)
    refresh = plan_github_refresh_post28(script_dir)
    dest = verify_dest_markers_post28(script_dir)
    ops = build_ops_rollup_manifest(script_dir)

    checks: List[str] = []
    failures: List[str] = []

    if git.is_repo:
        checks.append("git_repo")
    else:
        failures.append("not a git repo")

    if git.branch == SNAPSHOT_BRANCH:
        checks.append("on_feat_branch")
    else:
        failures.append(f"branch={git.branch!r}")

    if git.remote_branch_exists:
        checks.append("remote_feat_branch")
    else:
        failures.append("remote feat branch missing")

    if ops.production_ready:
        checks.append("ops_production_ready")
    else:
        failures.append(f"ops: {ops.reason}")

    if refresh.markers_ready and dest.get("ok"):
        checks.append("github_markers_synced")
    else:
        failures.append("github markers not synced")

    diff_names, diff_stat, diff_ok = _diff_vs_main(repo)
    if diff_ok and diff_names:
        checks.append("diff_vs_main")
        if _only_data_pc_paths(diff_names):
            checks.append("data_pc_only_diff")
        else:
            failures.append("diff outside data_pc/")
    elif diff_ok:
        failures.append("empty diff vs main")
    else:
        failures.append("diff stat failed")

    ready = not failures
    return MergeReadinessManifest(
        ready=ready,
        reason="merge_ready" if ready else "; ".join(failures),
        gate_count=len(P30_EXTENDED_ORDER),
        branch=SNAPSHOT_BRANCH,
        base=MAIN_BRANCH,
        ops_ready=ops.production_ready,
        github_sync_ready=bool(refresh.markers_ready and dest.get("ok")),
        checks=checks,
        failures=failures,
        diff_stat=diff_stat,
    )


def build_merge_readiness_manifest_post39(script_dir: str) -> MergeReadinessManifest:
    """P24 ops + P38 sync markers + git diff vs main (post-P39)."""
    repo = repo_root_path(script_dir)
    git = inspect_git_repo(script_dir)
    refresh = plan_github_refresh_post37(script_dir)
    dest = verify_dest_markers_post37(script_dir)
    ops = build_ops_rollup_manifest(script_dir)

    checks: List[str] = []
    failures: List[str] = []

    if git.is_repo:
        checks.append("git_repo")
    else:
        failures.append("not a git repo")

    if git.branch == SNAPSHOT_BRANCH:
        checks.append("on_feat_branch")
    else:
        failures.append(f"branch={git.branch!r}")

    if git.remote_branch_exists:
        checks.append("remote_feat_branch")
    else:
        failures.append("remote feat branch missing")

    if ops.production_ready:
        checks.append("ops_production_ready")
    else:
        failures.append(f"ops: {ops.reason}")

    if refresh.markers_ready and dest.get("ok"):
        checks.append("github_markers_synced")
    else:
        failures.append("github markers not synced")

    diff_names, diff_stat, diff_ok = _diff_vs_main(repo)
    if diff_ok and diff_names:
        checks.append("diff_vs_main")
        if _only_data_pc_paths(diff_names):
            checks.append("data_pc_only_diff")
        else:
            failures.append("diff outside data_pc/")
    elif diff_ok:
        failures.append("empty diff vs main")
    else:
        failures.append("diff stat failed")

    ready = not failures
    return MergeReadinessManifest(
        ready=ready,
        reason="merge_ready" if ready else "; ".join(failures),
        gate_count=len(P39_EXTENDED_ORDER),
        branch=SNAPSHOT_BRANCH,
        base=MAIN_BRANCH,
        ops_ready=ops.production_ready,
        github_sync_ready=bool(refresh.markers_ready and dest.get("ok")),
        checks=checks,
        failures=failures,
        diff_stat=diff_stat,
    )


def draft_pr_body(manifest: MergeReadinessManifest) -> str:
    return f"""## Summary
- Origin pipeline P층 P0–P30 ({manifest.gate_count} gates) on `{manifest.branch}`
- **Does not auto-merge** — review before merging to `{manifest.base}`

## Readiness
- ops_production_ready: {manifest.ops_ready}
- github_sync_ready: {manifest.github_sync_ready}
- checks: {', '.join(manifest.checks)}

## Test plan
- [ ] `python -m data_pc_origin.verify --p27` on data PC
- [ ] `python -m data_pc_origin.live_ops_rollup --tick`
- [ ] `DATA_PC_NATIVE_LIVE=1 python -m data_pc_origin.live_native_production --live`
"""


def draft_pr_body_post39(manifest: MergeReadinessManifest) -> str:
    return f"""## Summary
- Origin pipeline P층 P0–P39 ({manifest.gate_count} gates) on `{manifest.branch}`
- **Does not auto-merge** — review before merging to `{manifest.base}`

## Readiness
- ops_production_ready: {manifest.ops_ready}
- github_sync_ready: {manifest.github_sync_ready}
- checks: {', '.join(manifest.checks)}

## Test plan
- [ ] `python -m data_pc_origin.verify --p39` on data PC
- [ ] `python -m data_pc_origin.live_ops_rollup --tick`
- [ ] `DATA_PC_NATIVE_LIVE=1 python -m data_pc_origin.live_native_production --live`
"""


def create_merge_pr(script_dir: str) -> Dict[str, Any]:
    """`gh pr create` — `DATA_PC_MERGE_PR=1` + gh auth 필요."""
    manifest = build_merge_readiness_manifest(script_dir)
    if not manifest.ready:
        return {"status": "error", "stage": "readiness", "manifest": manifest.to_dict()}

    repo = repo_root_path(script_dir)
    body = draft_pr_body(manifest)
    title = f"feat(data-pc): origin pipeline P0–P30 ({manifest.gate_count} gates)"
    code, out = _run_git(
        repo,
        "push",
        "-u",
        REMOTE_NAME,
        SNAPSHOT_BRANCH,
    )
    if code != 0:
        return {"status": "error", "stage": "push", "detail": out, "manifest": manifest.to_dict()}

    try:
        proc = subprocess.run(
            [
                "gh",
                "pr",
                "create",
                "--base",
                MAIN_BRANCH,
                "--head",
                SNAPSHOT_BRANCH,
                "--title",
                title,
                "--body",
                body,
            ],
            cwd=str(repo),
            capture_output=True,
            text=True,
            check=False,
        )
        detail = ((proc.stdout or "") + (proc.stderr or "")).strip()
        ok = proc.returncode == 0
        return {
            "status": "ok" if ok else "error",
            "stage": "pr_create",
            "detail": detail,
            "manifest": manifest.to_dict(),
        }
    except OSError as exc:
        return {
            "status": "error",
            "stage": "pr_create",
            "detail": str(exc),
            "manifest": manifest.to_dict(),
        }


def create_merge_pr_post39(script_dir: str) -> Dict[str, Any]:
    """`gh pr create` — post-P39 manifest (structural; ops optional for plan)."""
    manifest = build_merge_readiness_manifest_post39(script_dir)
    if not merge_structural_ready(manifest):
        return {"status": "error", "stage": "readiness", "manifest": manifest.to_dict()}

    repo = repo_root_path(script_dir)
    body = draft_pr_body_post39(manifest)
    title = f"feat(data-pc): origin pipeline P0–P39 ({manifest.gate_count} gates)"
    code, out = _run_git(
        repo,
        "push",
        "-u",
        REMOTE_NAME,
        SNAPSHOT_BRANCH,
    )
    if code != 0:
        return {"status": "error", "stage": "push", "detail": out, "manifest": manifest.to_dict()}

    try:
        proc = subprocess.run(
            [
                "gh",
                "pr",
                "create",
                "--base",
                MAIN_BRANCH,
                "--head",
                SNAPSHOT_BRANCH,
                "--title",
                title,
                "--body",
                body,
            ],
            cwd=str(repo),
            capture_output=True,
            text=True,
            check=False,
        )
        detail = ((proc.stdout or "") + (proc.stderr or "")).strip()
        ok = proc.returncode == 0
        return {
            "status": "ok" if ok else "error",
            "stage": "pr_create",
            "detail": detail,
            "manifest": manifest.to_dict(),
        }
    except OSError as exc:
        return {
            "status": "error",
            "stage": "pr_create",
            "detail": str(exc),
            "manifest": manifest.to_dict(),
        }


def validate_merge_readiness_artifact(payload: Dict[str, Any]) -> bool:
    if payload.get("status") not in ("ok", "partial", "skipped"):
        return False
    manifest = payload.get("manifest")
    if not isinstance(manifest, dict):
        return False
    return "ready" in manifest and "checks" in manifest
