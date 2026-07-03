# -*- coding: utf-8
"""P19 — production live run + artifact validation."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Dict, Optional

from data_pc_origin.p18_production_e2e import (
    E2E_LIVE_ENV,
    apply_production_e2e_env,
    e2e_live_enabled,
    prepare_production_e2e,
)
from data_pc_origin.p19_live_assert import (
    fixture_ok_imap_payload,
    validate_imap_live_payload,
    validate_production_run_result,
)

ARTIFACT_NAME = "live_production_run_result.json"


def run_validate_fixture(*, artifact_dir: Optional[Path] = None) -> Dict[str, object]:
    """실행 검증 — synthetic ok payload against P19 rules."""
    imap = fixture_ok_imap_payload()
    validation = validate_imap_live_payload(imap)
    out: Dict[str, Any] = {
        "status": "ok" if validation.ok else "error",
        "mode": "validate_fixture",
        "imap": imap,
        "validation": validation.to_dict(),
    }
    root = artifact_dir or Path(__file__).resolve().parent
    path = root / ARTIFACT_NAME
    path.write_text(json.dumps(out, indent=2, ensure_ascii=False), encoding="utf-8")
    out["artifact"] = str(path)
    return out


def run_production_live_validated(
    *,
    artifact_dir: Optional[Path] = None,
    printer=print,
    force_live: bool = False,
) -> Dict[str, object]:
    """
    P19 production live — prep → live imap → artifact validate.

    Requires `DATA_PC_E2E_LIVE=1` unless `force_live=True` (harness only).
    """
    script_dir = str(Path(__file__).resolve().parent.parent)
    apply_production_e2e_env()
    os.environ[E2E_LIVE_ENV] = "1"
    prep = prepare_production_e2e(script_dir)

    out: Dict[str, Any] = {
        "status": "skipped",
        "mode": "live",
        "prep": prep.to_dict(),
    }

    if not prep.ready:
        out["reason"] = prep.reason
    elif not e2e_live_enabled() and not force_live:
        out["reason"] = f"set {E2E_LIVE_ENV}=1"
    else:
        try:
            from data_pc_origin.p18_production_e2e import run_production_imap_once

            imap = run_production_imap_once(artifact_dir=artifact_dir, printer=printer)
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
                    "mode",
                )
                if k in imap
            }
            validation = validate_imap_live_payload(
                imap if imap.get("status") == "ok" else imap_block
            )
            out = {
                "status": imap.get("status", "error"),
                "mode": "live",
                "prep": prep.to_dict(),
                "imap": imap_block,
                "validation": validation.to_dict(),
            }
            if validation.ok and out["status"] == "ok":
                out["status"] = "ok"
            elif out["status"] == "ok" and not validation.ok:
                out["status"] = "partial"
        except Exception as exc:  # noqa: BLE001
            out = {
                "status": "error",
                "mode": "live",
                "prep": prep.to_dict(),
                "error": f"{type(exc).__name__}: {exc}",
            }

    root = artifact_dir or Path(__file__).resolve().parent
    path = root / ARTIFACT_NAME
    path.write_text(json.dumps(out, indent=2, ensure_ascii=False), encoding="utf-8")
    out["artifact"] = str(path)
    run_validation = validate_production_run_result(out)
    out["run_validation"] = run_validation.to_dict()
    return out


def main() -> int:
    import sys

    if "--validate-fixture" in sys.argv:
        result = run_validate_fixture()
    else:
        result = run_production_live_validated(force_live="--force" in sys.argv)
    print(json.dumps(result, indent=2, ensure_ascii=False))
    ok_status = result.get("status") in ("ok", "skipped", "partial")
    validation = result.get("validation") or result.get("run_validation") or {}
    if isinstance(validation, dict) and validation.get("ok") is False and result.get("status") == "ok":
        return 1
    return 0 if ok_status else 1


if __name__ == "__main__":
    raise SystemExit(main())
