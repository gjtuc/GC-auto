# -*- coding: utf-8
"""P25 — native env production live harness."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, Optional

from data_pc_origin.p19_live_assert import validate_imap_live_payload, validate_production_run_result
from data_pc_origin.p25_native_live import (
    NATIVE_LIVE_ENV,
    native_live_enabled,
    prep_native_production_live,
    run_native_production_imap_once,
    validate_native_live_artifact,
)

ARTIFACT_NAME = "live_native_production_result.json"


def run_live_native_production(
    *,
    artifact_dir: Optional[Path] = None,
    live: bool = False,
    printer=print,
) -> Dict[str, object]:
    """
    P25 실행 검증.

    · default — native env prep (override 없음)
    · `--live` + `DATA_PC_NATIVE_LIVE=1` — production imap 1회
    """
    script_dir = str(Path(__file__).resolve().parent.parent)
    prep = prep_native_production_live(script_dir)

    out: Dict[str, Any] = {
        "status": "ok" if prep.ready else "partial",
        "mode": "prep",
        "prep": prep.to_dict(),
        "native_env": True,
    }

    if live:
        if not native_live_enabled():
            out = {
                "status": "skipped",
                "mode": "live",
                "reason": f"set {NATIVE_LIVE_ENV}=1",
                "prep": prep.to_dict(),
                "native_env": True,
            }
        elif not prep.ready:
            out = {
                "status": "skipped",
                "mode": "live",
                "reason": prep.reason,
                "prep": prep.to_dict(),
                "native_env": True,
            }
        else:
            try:
                imap = run_native_production_imap_once(artifact_dir=artifact_dir, printer=printer)
                imap_block = {
                    k: imap[k]
                    for k in (
                        "status",
                        "workflow_ok",
                        "row_count",
                        "sheets_updated",
                        "save_path",
                        "save_path_exists",
                        "reason",
                    )
                    if k in imap
                }
                validation = validate_imap_live_payload(imap_block)
                out = {
                    "status": "ok" if validation.ok else "error",
                    "mode": "live",
                    "prep": prep.to_dict(),
                    "native_env": True,
                    "imap": imap_block,
                    "validation": validation.to_dict(),
                }
            except Exception as exc:  # noqa: BLE001
                out = {
                    "status": "error",
                    "mode": "live",
                    "prep": prep.to_dict(),
                    "native_env": True,
                    "error": f"{type(exc).__name__}: {exc}",
                }

    root = artifact_dir or Path(__file__).resolve().parent
    path = root / ARTIFACT_NAME
    path.write_text(json.dumps(out, indent=2, ensure_ascii=False), encoding="utf-8")
    out["artifact"] = str(path)
    out["artifact_valid"] = validate_native_live_artifact(out)
    if live and "validation" in out:
        out["artifact_valid"] = out["artifact_valid"] and validate_production_run_result(out).ok
    path.write_text(json.dumps(out, indent=2, ensure_ascii=False), encoding="utf-8")
    return out


def main() -> int:
    import sys

    do_live = "--live" in sys.argv
    result = run_live_native_production(live=do_live)
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0 if result.get("status") in ("ok", "skipped", "partial") else 1


if __name__ == "__main__":
    raise SystemExit(main())
