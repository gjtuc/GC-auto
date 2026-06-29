# -*- coding: utf-8
"""P9-L — Live workflow E2E (workflow_bridge + G: opju, DATA_PC_SKIP_ORIGIN=0)."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Dict, Optional

from data_pc_origin.live_common import (
    LIVE_XLSX_ENV,
    LiveHarnessPrep as LiveWorkflowPrep,
    make_companion_stage2_runner,
    prepare_live_harness,
    resolve_live_excel_path,
)
from data_pc_origin.live_data import resolve_live_job
from data_pc_origin.p0_types import WorkflowMode
from data_pc_origin.p2_paths import resolve_stage4_save_path
from data_pc_origin.workflow_bridge import run_workflow_bridged_detailed

ARTIFACT_NAME = "live_workflow_result.json"


def prepare_live_workflow(
    opju_path: Optional[str] = None,
    *,
    xlsx_path: Optional[str] = None,
):
    return prepare_live_harness(opju_path, xlsx_path=xlsx_path, require_opju=True)


def run_live_workflow(
    opju_path: Optional[str] = None,
    *,
    xlsx_path: Optional[str] = None,
    artifact_dir: Optional[Path] = None,
    dry_run: bool = False,
    printer=print,
) -> Dict[str, object]:
    """Live 1회 — P8 `run_workflow_bridged` (--opju 모드)."""
    prep = prepare_live_workflow(opju_path, xlsx_path=xlsx_path)
    out: Dict[str, Any] = {
        "status": "skipped",
        "prep": prep.to_dict(),
        "mode": WorkflowMode.OPJU_ONLY.value,
    }

    if prep.ready and not dry_run:
        try:
            from data_pc_origin.live_data import _load_catalyst_module

            catalyst = _load_catalyst_module()
            job = resolve_live_job(prep.opju_path, xlsx_path=prep.excel_path)
            log: list[str] = []

            def _capture(msg: str) -> None:
                log.append(msg)
                printer(msg)

            live_env = {**os.environ, "DATA_PC_SKIP_ORIGIN": "0"}
            ok, wf = run_workflow_bridged_detailed(
                prep.excel_path,
                opju_path=prep.opju_path,
                auto_archive=True,
                skip_origin=False,
                catalyst_module=catalyst,
                environ=live_env,
                printer=_capture,
                stage2_runner=make_companion_stage2_runner(job, printer=_capture),
            )
            save_path = resolve_stage4_save_path(prep.opju_path, save_in_place=False)
            sheets = 0
            stage4_skipped = False
            if wf is not None and wf.stage4 is not None:
                stage4_skipped = wf.stage4.skipped
                if wf.stage4.origin is not None:
                    sheets = wf.stage4.origin.sheets_updated
            if ok:
                out = {
                    "status": "ok",
                    "prep": prep.to_dict(),
                    "mode": WorkflowMode.OPJU_ONLY.value,
                    "workflow_ok": ok,
                    "log_lines": len(log),
                    "sheets_updated": sheets,
                    "stage4_skipped": stage4_skipped,
                    "save_path": save_path,
                    "save_path_exists": os.path.isfile(save_path),
                    "data_source": "companion_xlsx",
                    "sample_name": job.sample_name,
                }
            else:
                out = {
                    "status": "error",
                    "prep": prep.to_dict(),
                    "mode": WorkflowMode.OPJU_ONLY.value,
                    "workflow_ok": False,
                    "log_tail": log[-5:] if log else [],
                }
        except Exception as exc:  # noqa: BLE001
            out = {
                "status": "error",
                "prep": prep.to_dict(),
                "error": f"{type(exc).__name__}: {exc}",
            }
    elif prep.ready and dry_run:
        job = resolve_live_job(prep.opju_path, xlsx_path=prep.excel_path)
        out = {
            "status": "dry_run",
            "prep": prep.to_dict(),
            "mode": WorkflowMode.OPJU_ONLY.value,
            "sample_name": job.sample_name,
            "row_count": job.row_count,
            "df_columns": len(job.columns),
        }

    root = artifact_dir or Path(__file__).resolve().parent
    artifact = root / ARTIFACT_NAME
    artifact.write_text(json.dumps(out, indent=2, ensure_ascii=False), encoding="utf-8")
    out["artifact"] = str(artifact)
    return out


def main() -> int:
    import sys

    dry = "--dry" in sys.argv
    positional = [a for a in sys.argv[1:] if not a.startswith("--")]
    opju = positional[0] if positional else None
    result = run_live_workflow(opju, dry_run=dry)
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0 if result["status"] in ("ok", "skipped", "dry_run") else 1


if __name__ == "__main__":
    raise SystemExit(main())
