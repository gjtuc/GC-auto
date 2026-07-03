# -*- coding: utf-8
"""P10-F — FULL_ARCHIVE live (companion + in-place opju, stage3 주입)."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Dict, Optional

from data_pc_origin.live_common import (
    LIVE_XLSX_ENV,
    make_companion_stage2_runner,
    make_injected_stage3_runner,
    prepare_live_harness,
)
from data_pc_origin.live_data import resolve_live_job
from data_pc_origin.p0_types import WorkflowMode
from data_pc_origin.p2_paths import resolve_stage4_save_path
from data_pc_origin.workflow_bridge import run_workflow_bridged_detailed

ARTIFACT_NAME = "live_full_archive_result.json"


def prepare_live_full_archive(
    opju_path: Optional[str] = None,
    *,
    xlsx_path: Optional[str] = None,
):
    return prepare_live_harness(opju_path, xlsx_path=xlsx_path, require_opju=True)


def run_live_full_archive(
    opju_path: Optional[str] = None,
    *,
    xlsx_path: Optional[str] = None,
    artifact_dir: Optional[Path] = None,
    dry_run: bool = False,
    printer=print,
) -> Dict[str, object]:
    """
    FULL_ARCHIVE live — companion stage2 · stage3=기존 폴더 · stage4 save_in_place.

    새 G: 폴더 생성 없음 (`setup_experiment_folder` 생략).
    """
    prep = prepare_live_full_archive(opju_path, xlsx_path=xlsx_path)
    out: Dict[str, Any] = {
        "status": "skipped",
        "prep": prep.to_dict(),
        "mode": WorkflowMode.FULL_ARCHIVE.value,
    }

    if prep.ready and dry_run:
        job = resolve_live_job(prep.opju_path, xlsx_path=prep.excel_path)
        out = {
            "status": "dry_run",
            "prep": prep.to_dict(),
            "mode": WorkflowMode.FULL_ARCHIVE.value,
            "sample_name": job.sample_name,
            "row_count": job.row_count,
            "save_in_place_path": prep.opju_path,
        }
    elif prep.ready and not dry_run:
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
                opju_path=None,
                auto_archive=True,
                skip_origin=False,
                catalyst_module=catalyst,
                environ=live_env,
                printer=_capture,
                stage2_runner=make_companion_stage2_runner(
                    job, label="companion xlsx", printer=_capture
                ),
                stage3_runner=make_injected_stage3_runner(
                    prep.opju_path, prep.excel_path
                ),
            )
            save_path = resolve_stage4_save_path(prep.opju_path, save_in_place=True)
            sheets = 0
            if wf is not None and wf.stage4 is not None and wf.stage4.origin is not None:
                sheets = wf.stage4.origin.sheets_updated
            if ok:
                out = {
                    "status": "ok",
                    "prep": prep.to_dict(),
                    "mode": WorkflowMode.FULL_ARCHIVE.value,
                    "workflow_ok": ok,
                    "sheets_updated": sheets,
                    "save_path": save_path,
                    "save_path_exists": os.path.isfile(save_path),
                    "save_in_place": True,
                    "data_source": "companion_xlsx",
                    "sample_name": job.sample_name,
                }
            else:
                out = {
                    "status": "error",
                    "prep": prep.to_dict(),
                    "mode": WorkflowMode.FULL_ARCHIVE.value,
                    "log_tail": log[-5:] if log else [],
                }
        except Exception as exc:  # noqa: BLE001
            out = {
                "status": "error",
                "prep": prep.to_dict(),
                "error": f"{type(exc).__name__}: {exc}",
            }

    root = artifact_dir or Path(__file__).resolve().parent
    path = root / ARTIFACT_NAME
    path.write_text(json.dumps(out, indent=2, ensure_ascii=False), encoding="utf-8")
    out["artifact"] = str(path)
    return out


def main() -> int:
    import sys

    dry = "--dry" in sys.argv
    positional = [a for a in sys.argv[1:] if not a.startswith("--")]
    opju = positional[0] if positional else None
    result = run_live_full_archive(opju, dry_run=dry)
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0 if result["status"] in ("ok", "skipped", "dry_run") else 1


if __name__ == "__main__":
    raise SystemExit(main())
