# -*- coding: utf-8 -*-
"""P41 — stack manifest harness (post-O-alignment)."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, Optional

from data_pc_origin.p41_manifest import (
    plan_stack_manifest_post40,
    validate_stack_manifest_artifact,
)

ARTIFACT_NAME = "live_p41_manifest_result.json"


def run_live_p41_manifest(
    *,
    artifact_dir: Optional[Path] = None,
    script_dir: Optional[str] = None,
) -> Dict[str, object]:
    """P41 실행 검증 — manifest plan + artifact JSON."""
    root_dir = script_dir or str(Path(__file__).resolve().parent.parent)
    plan = plan_stack_manifest_post40(root_dir)

    out: Dict[str, Any] = {
        "status": "ok" if plan.ready else "partial",
        "mode": "stack_manifest",
        "plan": plan.to_dict(),
    }
    out["artifact_valid"] = validate_stack_manifest_artifact(out)
    root = artifact_dir or Path(__file__).resolve().parent
    path = root / ARTIFACT_NAME
    path.write_text(json.dumps(out, indent=2, ensure_ascii=False), encoding="utf-8")
    out["artifact"] = str(path)
    return out


def main() -> int:
    result = run_live_p41_manifest()
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0 if result.get("status") in ("ok", "partial") else 1


if __name__ == "__main__":
    raise SystemExit(main())
