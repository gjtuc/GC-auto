# -*- coding: utf-8
"""P17 — origin env effective config harness."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Dict, Optional

from data_pc_origin.p17_env_config import (
    ORIGIN_PIPELINE_ENV,
    effective_origin_config,
    env_file_documents_origin_stack,
    missing_origin_defaults,
)

ARTIFACT_NAME = "live_env_result.json"

_SECRET_PATTERN = re.compile(
    r"(password|psk|secret|token)\s*=\s*\S+",
    re.IGNORECASE,
)


def run_live_env(
    *,
    artifact_dir: Optional[Path] = None,
    script_dir: Optional[str] = None,
) -> Dict[str, object]:
    """P17 실행 검증 — effective env report (비밀값 미포함)."""
    root_dir = script_dir or str(Path(__file__).resolve().parent.parent)
    env_path = str(Path(root_dir) / "gc_automation.env")
    report = effective_origin_config(root_dir)
    missing = missing_origin_defaults(env_path)
    documented = env_file_documents_origin_stack(env_path)

    out: Dict[str, Any] = {
        "status": "ok",
        "mode": "effective_config",
        "origin_pipeline": report["origin_pipeline"],
        "watch_mode": report["watch_mode"],
        "skip_origin": report["skip_origin"],
        "full_e2e_ready": report["full_e2e_ready"],
        "env_file_exists": report["env_file_exists"],
        "origin_stack_documented": documented,
        "missing_origin_keys": missing,
        "keys": report["keys"],
        "defaults": report["defaults"],
    }

    artifact_text = json.dumps(out, ensure_ascii=False)
    if _SECRET_PATTERN.search(artifact_text):
        out = {
            "status": "error",
            "error": "artifact contains secret-like pattern",
        }

    dest = artifact_dir or Path(__file__).resolve().parent
    path = dest / ARTIFACT_NAME
    path.write_text(json.dumps(out, indent=2, ensure_ascii=False), encoding="utf-8")
    out["artifact"] = str(path)
    out["env_path"] = env_path
    return out


def main() -> int:
    result = run_live_env()
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0 if result.get("status") == "ok" else 1


if __name__ == "__main__":
    raise SystemExit(main())
