# -*- coding: utf-8
"""P32 — GitHub refresh harness (P30–P31 markers)."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, Optional

from data_pc_origin.p23_github_snapshot import GITHUB_PUSH_ENV, github_push_enabled, inspect_git_repo
from data_pc_origin.p32_github_refresh import (
    plan_github_refresh_post31,
    push_github_refresh_post31,
    sync_github_refresh_post31,
    validate_github_refresh_post31_artifact,
)

ARTIFACT_NAME = "live_p32_github_refresh_result.json"


def run_live_p32_github_refresh(
    *,
    artifact_dir: Optional[Path] = None,
    script_dir: Optional[str] = None,
    do_sync: bool = False,
    do_push: bool = False,
) -> Dict[str, object]:
    """P32 실행 검증 — plan / sync / push (P30–P31 markers)."""
    root_dir = script_dir or str(Path(__file__).resolve().parent.parent)
    plan = plan_github_refresh_post31(root_dir)
    git = inspect_git_repo(root_dir)

    out: Dict[str, Any] = {
        "status": "ok" if plan.snapshot_ready and plan.markers_ready else "partial",
        "mode": "dry_plan",
        "plan": plan.to_dict(),
        "git": git.to_dict(),
    }

    if do_sync:
        sync = sync_github_refresh_post31(root_dir, dry_run=False)
        out["sync"] = sync
        out["mode"] = "sync"
        out["status"] = sync.get("status", "error")
        out["git_after"] = inspect_git_repo(root_dir).to_dict()

    if do_push:
        if not github_push_enabled():
            out = {
                "status": "skipped",
                "mode": "push",
                "reason": f"set {GITHUB_PUSH_ENV}=1",
                "plan": plan.to_dict(),
                "git": git.to_dict(),
            }
        else:
            result = push_github_refresh_post31(root_dir)
            out = {
                "status": result.get("status", "error"),
                "mode": "push",
                "plan": plan.to_dict(),
                "git_before": git.to_dict(),
                "push": result,
            }

    out["artifact_valid"] = validate_github_refresh_post31_artifact(out)
    root = artifact_dir or Path(__file__).resolve().parent
    path = root / ARTIFACT_NAME
    path.write_text(json.dumps(out, indent=2, ensure_ascii=False), encoding="utf-8")
    out["artifact"] = str(path)
    return out


def main() -> int:
    import sys

    do_sync = "--sync" in sys.argv
    do_push = "--push" in sys.argv
    result = run_live_p32_github_refresh(do_sync=do_sync, do_push=do_push)
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0 if result.get("status") in ("ok", "skipped", "partial") else 1


if __name__ == "__main__":
    raise SystemExit(main())
