# -*- coding: utf-8
"""P13 — IMAP probe · fetch · mail→P7→P8 live E2E."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Dict, Optional

from data_pc_origin.live_common import make_catalyst_stage2_runner
from data_pc_origin.o2_env import skip_origin_active
from data_pc_origin.p0_types import WorkflowMode
from data_pc_origin.p13_imap_adapter import (
    FetchedMail,
    gather_pending_counts,
    fetch_oldest_pending,
    mark_fetched_mail_seen,
    prepare_imap,
    reconcile_processed_unseen_mails,
)
from data_pc_origin.p6_catalyst_adapter import make_stage3_runner
from data_pc_origin.p7_mail_hook import MailJob, parse_mail_attachment
from data_pc_origin.p2_paths import resolve_stage4_save_path
from data_pc_origin.live_run import _g_drive_ok, _originpro_import_ok
from data_pc_origin.workflow_bridge import run_workflow_bridged_detailed

ARTIFACT_NAME = "live_imap_result.json"


def run_imap_probe(
    *,
    artifact_dir: Optional[Path] = None,
    dry_run: bool = False,
    printer=print,
) -> Dict[str, object]:
    """IMAP prep · (--dry) prep only · live 시 pending counts."""
    prep = prepare_imap()
    out: Dict[str, Any] = {
        "status": "skipped",
        "prep": prep.to_dict(),
        "mode": "imap_probe",
    }

    if not prep.ready:
        pass
    elif dry_run:
        out = {
            "status": "dry_run",
            "prep": prep.to_dict(),
            "mode": "imap_probe",
        }
    else:
        try:
            counts = gather_pending_counts(printer=printer)
            if counts.get("ok"):
                out = {
                    "status": "ok",
                    "prep": prep.to_dict(),
                    "mode": "imap_probe",
                    **{k: counts[k] for k in counts if k not in ("ok", "prep")},
                }
            else:
                out = {
                    "status": "error",
                    "prep": prep.to_dict(),
                    "mode": "imap_probe",
                    "reason": counts.get("reason", "probe failed"),
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


def run_live_imap(
    *,
    artifact_dir: Optional[Path] = None,
    dry_run: bool = False,
    fetch_only: bool = False,
    mark_seen: bool = False,
    opju_path: Optional[str] = None,
    printer=print,
) -> Dict[str, object]:
    """
    P13 live harness.

    · `--dry` — IMAP prep only
    · `--probe` — pending counts (run_imap_probe live)
    · `--fetch-only` — oldest pending → inbox (workflow 없음)
    · default — fetch + FULL_ARCHIVE native s2+s3 (production mail path)
    """
    prep = prepare_imap()
    skip = skip_origin_active()
    g_ok = _g_drive_ok()
    imp_ok = _originpro_import_ok()

    out: Dict[str, Any] = {
        "status": "skipped",
        "prep": prep.to_dict(),
        "entry": "imap",
    }

    if not prep.ready:
        pass
    elif dry_run:
        out = {
            "status": "dry_run",
            "prep": prep.to_dict(),
            "entry": "imap",
            "mode": "fetch_only" if fetch_only else "full_archive",
        }
    elif fetch_only:
        try:
            reconcile_processed_unseen_mails(printer=printer)
            fetched = fetch_oldest_pending(mark_seen=mark_seen, printer=printer)
            if fetched is None:
                counts = gather_pending_counts(printer=printer)
                out = {
                    "status": "skipped",
                    "prep": prep.to_dict(),
                    "entry": "imap",
                    "mode": "fetch_only",
                    "reason": "no pending gc mail",
                    "total_pending": counts.get("total_pending", 0),
                }
            else:
                job = MailJob(
                    attachment_path=fetched.attachment_path, subject=fetched.subject
                )
                parse_mail_attachment(job)
                out = {
                    "status": "ok",
                    "prep": prep.to_dict(),
                    "entry": "imap",
                    "mode": "fetch_only",
                    "fetched": fetched.to_dict(),
                    "attachment_exists": os.path.isfile(fetched.attachment_path),
                }
        except Exception as exc:  # noqa: BLE001
            out = {
                "status": "error",
                "prep": prep.to_dict(),
                "error": f"{type(exc).__name__}: {exc}",
            }
    else:
        if skip:
            out = {
                "status": "skipped",
                "prep": prep.to_dict(),
                "reason": "DATA_PC_SKIP_ORIGIN=1",
            }
        elif not g_ok:
            out = {
                "status": "skipped",
                "prep": prep.to_dict(),
                "reason": "G: drive not available",
            }
        elif not imp_ok:
            out = {
                "status": "skipped",
                "prep": prep.to_dict(),
                "reason": "originpro import failed",
            }
        else:
            try:
                reconcile_processed_unseen_mails(printer=printer)
                fetched = fetch_oldest_pending(mark_seen=False, printer=printer)
                if fetched is None:
                    out = {
                        "status": "skipped",
                        "prep": prep.to_dict(),
                        "entry": "imap",
                        "reason": "no pending gc mail",
                    }
                else:
                    job = MailJob(
                        attachment_path=fetched.attachment_path,
                        subject=fetched.subject,
                    )
                    parse_mail_attachment(job)
                    from data_pc_origin.live_data import _load_catalyst_module

                    catalyst = _load_catalyst_module()
                    log: list[str] = []

                    def _capture(msg: str) -> None:
                        log.append(msg)
                        printer(msg)

                    live_env = {**os.environ, "DATA_PC_SKIP_ORIGIN": "0"}
                    mode = (
                        WorkflowMode.OPJU_ONLY
                        if (opju_path or "").strip()
                        else WorkflowMode.FULL_ARCHIVE
                    )
                    ok, wf = run_workflow_bridged_detailed(
                        fetched.attachment_path,
                        opju_path=(opju_path or "").strip() or None,
                        auto_archive=not bool((opju_path or "").strip()),
                        skip_origin=False,
                        catalyst_module=catalyst,
                        environ=live_env,
                        printer=_capture,
                        stage2_runner=make_catalyst_stage2_runner(
                            catalyst, printer=_capture
                        ),
                        stage3_runner=(
                            None
                            if mode == WorkflowMode.OPJU_ONLY
                            else make_stage3_runner(catalyst)
                        ),
                        mail_received_at=fetched.received_at,
                    )
                    save_path = ""
                    sheets = 0
                    row_count = 0
                    if wf is not None and wf.stage2 is not None:
                        row_count = len(wf.stage2.artifacts.df)
                    if wf is not None and wf.stage3 is not None:
                        save_path = resolve_stage4_save_path(
                            wf.stage3.target_opju,
                            save_in_place=(mode != WorkflowMode.OPJU_ONLY),
                        )
                    elif wf is not None and wf.stage4 is not None:
                        save_path = resolve_stage4_save_path(
                            (opju_path or "").strip(),
                            save_in_place=False,
                        )
                    if wf is not None and wf.stage4 is not None and wf.stage4.origin:
                        sheets = wf.stage4.origin.sheets_updated
                    if ok:
                        mark_fetched_mail_seen(fetched, printer=printer)
                        out = {
                            "status": "ok",
                            "prep": prep.to_dict(),
                            "entry": "imap",
                            "mode": mode.value,
                            "data_source": "imap_fetch",
                            "fetched": fetched.to_dict(),
                            "workflow_ok": ok,
                            "row_count": row_count,
                            "sheets_updated": sheets,
                            "save_path": save_path,
                            "save_path_exists": bool(
                                save_path and os.path.isfile(save_path)
                            ),
                        }
                    else:
                        out = {
                            "status": "error",
                            "prep": prep.to_dict(),
                            "entry": "imap",
                            "fetched": fetched.to_dict(),
                            "log_tail": log[-8:] if log else [],
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
    fetch_only = "--fetch-only" in sys.argv
    probe = "--probe" in sys.argv
    mark_seen = "--mark-seen" in sys.argv
    positional = [a for a in sys.argv[1:] if not a.startswith("--")]
    opju = positional[0] if positional and positional[0].lower().endswith(".opju") else None

    if probe:
        result = run_imap_probe(dry_run=dry)
    elif "--reconcile-seen" in sys.argv:
        count = reconcile_processed_unseen_mails()
        result = {"status": "ok", "reconciled": count}
        print(json.dumps(result, indent=2, ensure_ascii=False))
        return 0
    else:
        result = run_live_imap(
            dry_run=dry,
            fetch_only=fetch_only,
            mark_seen=mark_seen,
            opju_path=opju,
        )
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0 if result["status"] in ("ok", "skipped", "dry_run") else 1


if __name__ == "__main__":
    raise SystemExit(main())
