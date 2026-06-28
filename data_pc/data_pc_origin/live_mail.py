# -*- coding: utf-8
"""P10-M — 메일 첨부 시뮬 live E2E (P7 + P8, IMAP 없음)."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Dict, Optional

from data_pc_origin.live_common import (
    LIVE_MAIL_XLSX_ENV,
    make_companion_stage2_runner,
    prepare_live_harness,
)
from data_pc_origin.live_data import resolve_live_job
from data_pc_origin.p0_types import WorkflowMode
from data_pc_origin.p2_paths import resolve_stage4_save_path
from data_pc_origin.p7_mail_hook import MailJob, parse_mail_attachment
from data_pc_origin.workflow_bridge import run_workflow_bridged_detailed

ARTIFACT_NAME = "live_mail_result.json"


def prepare_live_mail(
    attachment_path: Optional[str] = None,
    *,
    opju_path: Optional[str] = None,
):
    mail_x = (attachment_path or os.getenv(LIVE_MAIL_XLSX_ENV) or "").strip()
    return prepare_live_harness(
        opju_path,
        mail_xlsx=mail_x,
        require_opju=True,
    )


def run_live_mail(
    attachment_path: Optional[str] = None,
    *,
    opju_path: Optional[str] = None,
    artifact_dir: Optional[Path] = None,
    dry_run: bool = False,
    printer=print,
) -> Dict[str, object]:
    """
    메일 1건 시뮬 — `DATA_PC_LIVE_MAIL_XLSX` 또는 companion.

    IMAP 없음; P7 `MailJob` 경로 검증 후 P8 bridge (--opju).
    """
    prep = prepare_live_mail(attachment_path, opju_path=opju_path)
    out: Dict[str, Any] = {
        "status": "skipped",
        "prep": prep.to_dict(),
        "mode": WorkflowMode.OPJU_ONLY.value,
        "entry": "mail",
    }

    if prep.ready:
        job_mail = MailJob(attachment_path=prep.excel_path, subject="live_sim")
        parse_mail_attachment(job_mail)

    if prep.ready and dry_run:
        job = resolve_live_job(prep.opju_path, xlsx_path=prep.excel_path)
        out = {
            "status": "dry_run",
            "prep": prep.to_dict(),
            "mode": WorkflowMode.OPJU_ONLY.value,
            "entry": "mail",
            "attachment": prep.excel_path,
            "sample_name": job.sample_name,
            "row_count": job.row_count,
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
                opju_path=prep.opju_path,
                auto_archive=True,
                skip_origin=False,
                catalyst_module=catalyst,
                environ=live_env,
                printer=_capture,
                stage2_runner=make_companion_stage2_runner(
                    job, label="mail attachment", printer=_capture
                ),
            )
            save_path = resolve_stage4_save_path(prep.opju_path, save_in_place=False)
            sheets = 0
            if wf is not None and wf.stage4 is not None and wf.stage4.origin is not None:
                sheets = wf.stage4.origin.sheets_updated
            if ok:
                out = {
                    "status": "ok",
                    "prep": prep.to_dict(),
                    "mode": WorkflowMode.OPJU_ONLY.value,
                    "entry": "mail",
                    "attachment": prep.excel_path,
                    "workflow_ok": ok,
                    "sheets_updated": sheets,
                    "save_path": save_path,
                    "save_path_exists": os.path.isfile(save_path),
                    "sample_name": job.sample_name,
                }
            else:
                out = {
                    "status": "error",
                    "prep": prep.to_dict(),
                    "entry": "mail",
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
    attach: Optional[str] = None
    opju: Optional[str] = None
    for p in positional:
        low = p.lower()
        if low.endswith(".opju"):
            opju = p
        elif low.endswith((".xlsx", ".xls")):
            attach = p
    result = run_live_mail(attach, opju_path=opju, dry_run=dry)
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0 if result["status"] in ("ok", "skipped", "dry_run") else 1


if __name__ == "__main__":
    raise SystemExit(main())
