# -*- coding: utf-8
"""P31 — merge PR harness."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, Optional

from data_pc_origin.p28_merge_readiness import MERGE_PR_ENV, draft_pr_body, merge_pr_enabled
from data_pc_origin.p28_merge_readiness import build_merge_readiness_manifest
from data_pc_origin.p31_merge_pr import (
    create_merge_pr_post30,
    plan_merge_pr_post30,
    validate_merge_pr_artifact,
)

ARTIFACT_NAME = "live_p31_merge_pr_result.json"


def run_live_p31_merge_pr(
    *,
    artifact_dir: Optional[Path] = None,
    script_dir: Optional[str] = None,
    create_pr: bool = False,
) -> Dict[str, object]:
    """P31 실행 검증 — merge PR plan (+ optional gated create)."""
    root_dir = script_dir or str(Path(__file__).resolve().parent.parent)
    plan = plan_merge_pr_post30(root_dir)
    manifest = build_merge_readiness_manifest(root_dir)

    out: Dict[str, Any] = {
        "status": "ok" if plan.pr_ready else "partial",
        "mode": "dry_plan",
        "plan": plan.to_dict(),
        "manifest": manifest.to_dict(),
        "pr_body_preview": draft_pr_body(manifest),
    }

    if create_pr:
        if not merge_pr_enabled():
            out = {
                "status": "skipped",
                "mode": "pr",
                "reason": f"set {MERGE_PR_ENV}=1",
                "plan": plan.to_dict(),
                "manifest": manifest.to_dict(),
            }
        else:
            result = create_merge_pr_post30(root_dir)
            out = {
                "status": result.get("status", "error"),
                "mode": "pr",
                "plan": plan.to_dict(),
                "manifest": manifest.to_dict(),
                "pr": result,
            }

    out["artifact_valid"] = validate_merge_pr_artifact(out)
    root = artifact_dir or Path(__file__).resolve().parent
    path = root / ARTIFACT_NAME
    path.write_text(json.dumps(out, indent=2, ensure_ascii=False), encoding="utf-8")
    out["artifact"] = str(path)
    return out


def main() -> int:
    import sys

    do_pr = "--pr" in sys.argv
    result = run_live_p31_merge_pr(create_pr=do_pr)
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0 if result.get("status") in ("ok", "skipped", "partial") else 1


if __name__ == "__main__":
    raise SystemExit(main())
