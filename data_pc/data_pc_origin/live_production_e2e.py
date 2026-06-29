# -*- coding: utf-8
"""P18 — production full E2E harness (IMAP + Origin COM)."""

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
    run_production_imap_once,
)

ARTIFACT_NAME = "live_production_e2e_result.json"


def run_live_production_e2e(
    *,
    artifact_dir: Optional[Path] = None,
    dry_prep: bool = True,
    prep_live: bool = False,
    live: bool = False,
    printer=print,
) -> Dict[str, object]:
    """
    P18 실행 검증.

    · default `--dry` — prep only (IMAP/Origin 미실행)
    · `--prep-live` — IMAP probe live + prep
    · `--live` — full imap workflow (requires DATA_PC_E2E_LIVE=1)
    """
    script_dir = str(Path(__file__).resolve().parent.parent)
    prep = prepare_production_e2e(script_dir)
    out: Dict[str, Any] = {
        "status": "skipped",
        "mode": "dry_prep",
        "prep": prep.to_dict(),
    }

    if live:
        if not e2e_live_enabled():
            out = {
                "status": "skipped",
                "mode": "live",
                "prep": prep.to_dict(),
                "reason": f"set {E2E_LIVE_ENV}=1 for live full E2E",
            }
        else:
            try:
                apply_production_e2e_env()
                imap = run_production_imap_once(
                    artifact_dir=artifact_dir,
                    printer=printer,
                )
                out = {
                    "status": imap.get("status", "error"),
                    "mode": "live",
                    "prep": prep.to_dict(),
                    "imap": {
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
                    },
                }
            except Exception as exc:  # noqa: BLE001
                out = {
                    "status": "error",
                    "mode": "live",
                    "prep": prep.to_dict(),
                    "error": f"{type(exc).__name__}: {exc}",
                }
    elif prep_live:
        try:
            from data_pc_origin.live_imap import run_imap_probe

            probe = run_imap_probe(
                artifact_dir=artifact_dir,
                dry_run=False,
                printer=printer,
            )
            out = {
                "status": "ok" if probe.get("status") == "ok" else probe.get("status", "error"),
                "mode": "prep_live",
                "prep": prep.to_dict(),
                "imap_probe": {
                    k: probe[k]
                    for k in ("status", "total_pending", "mode")
                    if k in probe
                },
            }
        except Exception as exc:  # noqa: BLE001
            out = {
                "status": "error",
                "mode": "prep_live",
                "prep": prep.to_dict(),
                "error": f"{type(exc).__name__}: {exc}",
            }
    elif dry_prep:
        out = {
            "status": "ok",
            "mode": "dry_prep",
            "prep": prep.to_dict(),
            "would_run": prep.stack,
            "live_gate": E2E_LIVE_ENV,
        }

    root = artifact_dir or Path(__file__).resolve().parent
    path = root / ARTIFACT_NAME
    path.write_text(json.dumps(out, indent=2, ensure_ascii=False), encoding="utf-8")
    out["artifact"] = str(path)
    out["e2e_live_env"] = e2e_live_enabled()
    return out


def main() -> int:
    import sys

    dry = "--live" not in sys.argv and "--prep-live" not in sys.argv
    prep_live = "--prep-live" in sys.argv
    live = "--live" in sys.argv
    result = run_live_production_e2e(
        dry_prep=dry,
        prep_live=prep_live,
        live=live,
    )
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0 if result["status"] in ("ok", "skipped", "dry_run") else 1


if __name__ == "__main__":
    raise SystemExit(main())
