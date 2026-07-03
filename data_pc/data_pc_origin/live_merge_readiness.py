# -*- coding: utf-8
"""P28 — main merge readiness harness."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, Optional

from data_pc_origin.p28_merge_readiness import (
    MERGE_PR_ENV,
    build_merge_readiness_manifest,
    create_merge_pr,
    draft_pr_body,
    merge_pr_enabled,
    validate_merge_readiness_artifact,
)

ARTIFACT_NAME = "live_merge_readiness_result.json"


def run_live_merge_readiness(
    *,
    artifact_dir: Optional[Path] = None,
    script_dir: Optional[str] = None,
    create_pr: bool = False,
) -> Dict[str, object]:
    """P28 실행 검증 — merge manifest (+ optional gated PR)."""
    root_dir = script_dir or str(Path(__file__).resolve().parent.parent)
    manifest = build_merge_readiness_manifest(root_dir)

    out: Dict[str, Any] = {
        "status": "ok" if manifest.ready else "partial",
        "mode": "manifest",
        "manifest": manifest.to_dict(),
        "pr_body_preview": draft_pr_body(manifest),
    }

    if create_pr:
        if not merge_pr_enabled():
            out = {
                "status": "skipped",
                "mode": "pr",
                "reason": f"set {MERGE_PR_ENV}=1",
                "manifest": manifest.to_dict(),
            }
        else:
            result = create_merge_pr(root_dir)
            out = {
                "status": result.get("status", "error"),
                "mode": "pr",
                "manifest": manifest.to_dict(),
                "pr": result,
            }

    root = artifact_dir or Path(__file__).resolve().parent
    path = root / ARTIFACT_NAME
    path.write_text(json.dumps(out, indent=2, ensure_ascii=False), encoding="utf-8")
    out["artifact"] = str(path)
    out["artifact_valid"] = validate_merge_readiness_artifact(out)
    path.write_text(json.dumps(out, indent=2, ensure_ascii=False), encoding="utf-8")
    return out


def main() -> int:
    import sys

    do_pr = "--pr" in sys.argv
    result = run_live_merge_readiness(create_pr=do_pr)
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0 if result.get("status") in ("ok", "partial", "skipped") else 1


if __name__ == "__main__":
    raise SystemExit(main())
