# -*- coding: utf-8
"""P24 — operational closure harness."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, Optional

from data_pc_origin.p24_ops_rollup import (
    build_ops_rollup_manifest,
    validate_ops_rollup_artifact,
)

ARTIFACT_NAME = "live_ops_rollup_result.json"


def run_live_ops_rollup(
    *,
    artifact_dir: Optional[Path] = None,
    script_dir: Optional[str] = None,
    dry_tick: bool = False,
) -> Dict[str, object]:
    """P24 실행 검증 — P20–P23 rollup (optional supervisor dry tick)."""
    root_dir = script_dir or str(Path(__file__).resolve().parent.parent)
    manifest = build_ops_rollup_manifest(root_dir, dry_tick=dry_tick)

    out: Dict[str, Any] = {
        "status": "ok" if manifest.production_ready else "partial",
        "mode": "dry_tick" if dry_tick else "rollup",
        "manifest": manifest.to_dict(),
    }

    root = artifact_dir or Path(__file__).resolve().parent
    path = root / ARTIFACT_NAME
    path.write_text(json.dumps(out, indent=2, ensure_ascii=False), encoding="utf-8")
    out["artifact"] = str(path)
    out["artifact_valid"] = validate_ops_rollup_artifact(out)
    path.write_text(json.dumps(out, indent=2, ensure_ascii=False), encoding="utf-8")
    return out


def main() -> int:
    import sys

    dry_tick = "--tick" in sys.argv
    result = run_live_ops_rollup(dry_tick=dry_tick)
    print(json.dumps(result, indent=2, ensure_ascii=False))
    ok = result.get("status") in ("ok", "partial") and result.get("artifact_valid")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
