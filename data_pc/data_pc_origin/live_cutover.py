# -*- coding: utf-8
"""P21 — operational cutover harness."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, Optional

from data_pc_origin.p17_env_config import load_script_env
from data_pc_origin.p20_readiness import build_readiness_manifest
from data_pc_origin.p21_cutover import (
    CUTOVER_APPLY_ENV,
    apply_cutover,
    assess_cutover_readiness,
    cutover_apply_enabled,
    plan_cutover,
)

ARTIFACT_NAME = "live_cutover_result.json"


def run_live_cutover(
    *,
    artifact_dir: Optional[Path] = None,
    script_dir: Optional[str] = None,
    dry: bool = True,
    apply: bool = False,
) -> Dict[str, object]:
    """
    P21 실행 검증.

    · default — cutover plan + readiness (파일 변경 없음)
    · `--apply` + `DATA_PC_CUTOVER_APPLY=1` — backup 후 production env 적용
    """
    root_dir = script_dir or str(Path(__file__).resolve().parent.parent)
    before = assess_cutover_readiness(root_dir)

    out: Dict[str, Any] = {
        "status": "ok",
        "mode": "dry_plan",
        "before": before,
    }

    if apply:
        if not cutover_apply_enabled():
            out = {
                "status": "skipped",
                "mode": "apply",
                "reason": f"set {CUTOVER_APPLY_ENV}=1",
                "before": before,
            }
        else:
            try:
                plan = apply_cutover(root_dir, backup=True)
                load_script_env(root_dir)
                after_manifest = build_readiness_manifest(root_dir)
                out = {
                    "status": "ok",
                    "mode": "apply",
                    "before": before,
                    "applied": plan.to_dict(),
                    "after": {
                        "manifest": after_manifest.to_dict(),
                        "full_e2e_ready": after_manifest.full_e2e_ready,
                    },
                }
            except Exception as exc:  # noqa: BLE001
                out = {
                    "status": "error",
                    "mode": "apply",
                    "before": before,
                    "error": f"{type(exc).__name__}: {exc}",
                }
    elif not dry:
        out["mode"] = "assess_only"

    root = artifact_dir or Path(__file__).resolve().parent
    path = root / ARTIFACT_NAME
    path.write_text(json.dumps(out, indent=2, ensure_ascii=False), encoding="utf-8")
    out["artifact"] = str(path)
    return out


def main() -> int:
    import sys

    do_apply = "--apply" in sys.argv
    result = run_live_cutover(dry=not do_apply, apply=do_apply)
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0 if result.get("status") in ("ok", "skipped") else 1


if __name__ == "__main__":
    raise SystemExit(main())
