# -*- coding: utf-8
"""P20 — production readiness harness."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, Optional

from data_pc_origin.p20_readiness import build_readiness_manifest, validate_readiness_artifact

ARTIFACT_NAME = "live_readiness_result.json"


def run_live_readiness(
    *,
    artifact_dir: Optional[Path] = None,
    script_dir: Optional[str] = None,
    dry_tick: bool = False,
) -> Dict[str, object]:
    """P20 실행 검증 — stack manifest (optional supervisor dry tick)."""
    root_dir = script_dir or str(Path(__file__).resolve().parent.parent)
    manifest = build_readiness_manifest(root_dir, dry_tick=dry_tick)

    out: Dict[str, Any] = {
        "status": "ok" if manifest.ready else "partial",
        "mode": "dry_tick" if dry_tick else "manifest",
        "manifest": manifest.to_dict(),
    }

    root = artifact_dir or Path(__file__).resolve().parent
    path = root / ARTIFACT_NAME
    path.write_text(json.dumps(out, indent=2, ensure_ascii=False), encoding="utf-8")
    out["artifact"] = str(path)
    out["artifact_valid"] = validate_readiness_artifact(out)
    return out


def main() -> int:
    import sys

    dry_tick = "--tick" in sys.argv
    result = run_live_readiness(dry_tick=dry_tick)
    print(json.dumps(result, indent=2, ensure_ascii=False))
    ok = result.get("status") in ("ok", "partial") and result.get("artifact_valid")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
