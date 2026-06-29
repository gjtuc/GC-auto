# -*- coding: utf-8
"""P37 — GitHub push harness."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, Optional

from data_pc_origin.p23_github_snapshot import GITHUB_PUSH_ENV, github_push_enabled, inspect_git_repo
from data_pc_origin.p37_github_push import (
    plan_github_push_post36,
    push_github_post36,
    validate_github_push_post36_artifact,
)

ARTIFACT_NAME = "live_p37_github_push_result.json"


def run_live_p37_github_push(
    *,
    artifact_dir: Optional[Path] = None,
    script_dir: Optional[str] = None,
    do_push: bool = False,
) -> Dict[str, object]:
    """P37 실행 검증 — push plan (+ optional gated push)."""
    root_dir = script_dir or str(Path(__file__).resolve().parent.parent)
    plan = plan_github_push_post36(root_dir)
    git = inspect_git_repo(root_dir)

    out: Dict[str, Any] = {
        "status": "ok" if plan.push_ready else "partial",
        "mode": "dry_plan",
        "plan": plan.to_dict(),
        "git": git.to_dict(),
    }

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
            result = push_github_post36(root_dir)
            out = {
                "status": result.get("status", "error"),
                "mode": "push",
                "plan": plan.to_dict(),
                "git_before": git.to_dict(),
                "push_result": result,
            }

    out["artifact_valid"] = validate_github_push_post36_artifact(out)
    root = artifact_dir or Path(__file__).resolve().parent
    path = root / ARTIFACT_NAME
    path.write_text(json.dumps(out, indent=2, ensure_ascii=False), encoding="utf-8")
    out["artifact"] = str(path)
    return out


def main() -> int:
    import sys

    do_push = "--push" in sys.argv
    result = run_live_p37_github_push(do_push=do_push)
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0 if result.get("status") in ("ok", "skipped", "partial") else 1


if __name__ == "__main__":
    raise SystemExit(main())
