# -*- coding: utf-8
"""P22 — autostart / watch integration harness."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, Optional

from data_pc_origin.p22_autostart import (
    build_autostart_manifest,
    validate_autostart_artifact,
)

ARTIFACT_NAME = "live_autostart_result.json"


def run_live_autostart(
    *,
    artifact_dir: Optional[Path] = None,
    script_dir: Optional[str] = None,
) -> Dict[str, object]:
    """P22 실행 검증 — bat/VBS/watchdog/--watch 체인 스캔 (프로세스 기동 없음)."""
    root_dir = script_dir or str(Path(__file__).resolve().parent.parent)
    manifest = build_autostart_manifest(root_dir)

    out: Dict[str, Any] = {
        "status": "ok" if manifest.ready else "partial",
        "mode": "scan",
        "manifest": manifest.to_dict(),
        "artifact_valid": True,
    }

    root = artifact_dir or Path(__file__).resolve().parent
    path = root / ARTIFACT_NAME
    path.write_text(json.dumps(out, indent=2, ensure_ascii=False), encoding="utf-8")
    out["artifact"] = str(path)
    out["artifact_valid"] = validate_autostart_artifact(out)
    path.write_text(json.dumps(out, indent=2, ensure_ascii=False), encoding="utf-8")
    return out


def main() -> int:
    result = run_live_autostart()
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0 if result.get("status") == "ok" else 1


if __name__ == "__main__":
    raise SystemExit(main())
