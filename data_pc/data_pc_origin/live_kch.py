# -*- coding: utf-8
"""P11-K — KCH 원본 process_excel live (companion shortcut 없음)."""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Optional

from data_pc_origin.live_common import (
    LIVE_KCH_XLSX_ENV,
    make_catalyst_stage2_runner,
)
from data_pc_origin.live_run import LIVE_OPJU_ENV, _g_drive_ok, _originpro_import_ok
from data_pc_origin.o1_opju_path import probe_opju_path
from data_pc_origin.o2_env import skip_origin_active
from data_pc_origin.p0_types import WorkflowMode
from data_pc_origin.p2_paths import resolve_stage4_save_path
from data_pc_origin.workflow_bridge import run_workflow_bridged_detailed

ARTIFACT_NAME = "live_kch_result.json"


@dataclass
class LiveKchPrep:
    ready: bool
    reason: str
    kch_path: str
    opju_path: str
    stage2_only: bool
    skip_origin: bool
    g_drive_ok: bool
    originpro_import_ok: bool
    probe_ok: bool

    def to_dict(self) -> Dict[str, object]:
        return {
            "ready": self.ready,
            "reason": self.reason,
            "kch_path": self.kch_path,
            "opju_path": self.opju_path,
            "stage2_only": self.stage2_only,
            "skip_origin": self.skip_origin,
            "g_drive_ok": self.g_drive_ok,
            "originpro_import_ok": self.originpro_import_ok,
            "probe_ok": self.probe_ok,
        }


def prepare_live_kch(
    kch_path: Optional[str] = None,
    *,
    opju_path: Optional[str] = None,
    stage2_only: bool = False,
) -> LiveKchPrep:
    kch = (kch_path or os.getenv(LIVE_KCH_XLSX_ENV) or "").strip()
    opju = (opju_path or os.getenv(LIVE_OPJU_ENV) or "").strip()
    skip = skip_origin_active()
    g_ok = _g_drive_ok()
    imp_ok = _originpro_import_ok()
    probe = probe_opju_path(opju) if opju else None

    if not kch:
        return LiveKchPrep(
            False,
            f"set {LIVE_KCH_XLSX_ENV} or pass kch_path",
            kch,
            opju,
            stage2_only,
            skip,
            g_ok,
            imp_ok,
            False,
        )
    if not os.path.isfile(kch):
        return LiveKchPrep(
            False,
            f"kch xlsx not found: {kch}",
            kch,
            opju,
            stage2_only,
            skip,
            g_ok,
            imp_ok,
            False,
        )
    if stage2_only:
        return LiveKchPrep(True, "ready", kch, opju, True, skip, g_ok, imp_ok, True)

    if skip:
        return LiveKchPrep(
            False, "DATA_PC_SKIP_ORIGIN=1", kch, opju, False, skip, g_ok, imp_ok, False
        )
    if not opju:
        return LiveKchPrep(
            False,
            f"full workflow needs {LIVE_OPJU_ENV} or opju_path",
            kch,
            opju,
            False,
            skip,
            g_ok,
            imp_ok,
            False,
        )
    if not g_ok:
        return LiveKchPrep(
            False, "G: drive not available", kch, opju, False, skip, g_ok, imp_ok, False
        )
    if not imp_ok:
        return LiveKchPrep(
            False,
            "originpro import failed",
            kch,
            opju,
            False,
            skip,
            g_ok,
            imp_ok,
            False,
        )
    if probe is None or not probe.ok:
        return LiveKchPrep(
            False,
            (probe.detail if probe else "opju probe failed"),
            kch,
            opju,
            False,
            skip,
            g_ok,
            imp_ok,
            False,
        )
    return LiveKchPrep(True, "ready", kch, opju, False, skip, g_ok, imp_ok, True)


def run_live_kch(
    kch_path: Optional[str] = None,
    *,
    opju_path: Optional[str] = None,
    stage2_only: bool = False,
    artifact_dir: Optional[Path] = None,
    dry_run: bool = False,
    printer=print,
) -> Dict[str, object]:
    """
    KCH inbox 원본 → P6 process_excel live.

    `--stage2-only`: Origin/G: opju 없이 2단계만.
    기본: OPJU_ONLY + native stage2 (--opju).
    """
    prep = prepare_live_kch(
        kch_path, opju_path=opju_path, stage2_only=stage2_only
    )
    mode = "stage2_only" if stage2_only else WorkflowMode.OPJU_ONLY.value
    out: Dict[str, Any] = {
        "status": "skipped",
        "prep": prep.to_dict(),
        "mode": mode,
        "data_source": "kch_raw",
    }

    if prep.ready and dry_run:
        out = {
            "status": "dry_run",
            "prep": prep.to_dict(),
            "mode": mode,
            "data_source": "kch_raw",
            "kch_basename": os.path.basename(prep.kch_path),
        }
    elif prep.ready and stage2_only and not dry_run:
        try:
            from data_pc_origin.live_data import _load_catalyst_module

            log: list[str] = []

            def _capture(msg: str) -> None:
                log.append(msg)
                printer(msg)

            catalyst = _load_catalyst_module()
            stage2 = make_catalyst_stage2_runner(catalyst, printer=_capture)(
                prep.kch_path
            )
            if stage2 is None:
                out = {
                    "status": "error",
                    "prep": prep.to_dict(),
                    "mode": mode,
                    "error": "process_excel returned None",
                    "log_tail": log[-5:] if log else [],
                }
            else:
                out = {
                    "status": "ok",
                    "prep": prep.to_dict(),
                    "mode": mode,
                    "data_source": "kch_raw",
                    "sample_name": stage2.metadata.sample_name,
                    "saved_excel": stage2.metadata.saved_excel,
                    "row_count": len(stage2.artifacts.df),
                    "warnings": list(stage2.artifacts.warnings),
                    "feed_source": stage2.artifacts.feed_source_desc,
                }
        except Exception as exc:  # noqa: BLE001
            out = {
                "status": "error",
                "prep": prep.to_dict(),
                "error": f"{type(exc).__name__}: {exc}",
            }
    elif prep.ready and not stage2_only and not dry_run:
        try:
            from data_pc_origin.live_data import _load_catalyst_module

            catalyst = _load_catalyst_module()
            log: list[str] = []

            def _capture(msg: str) -> None:
                log.append(msg)
                printer(msg)

            live_env = {**os.environ, "DATA_PC_SKIP_ORIGIN": "0"}
            ok, wf = run_workflow_bridged_detailed(
                prep.kch_path,
                opju_path=prep.opju_path,
                auto_archive=True,
                skip_origin=False,
                catalyst_module=catalyst,
                environ=live_env,
                printer=_capture,
                stage2_runner=make_catalyst_stage2_runner(
                    catalyst, printer=_capture
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
                    "mode": mode,
                    "data_source": "kch_raw",
                    "workflow_ok": ok,
                    "sheets_updated": sheets,
                    "save_path": save_path,
                    "save_path_exists": os.path.isfile(save_path),
                    "sample_name": (
                        wf.stage2.metadata.sample_name
                        if wf is not None and wf.stage2 is not None
                        else ""
                    ),
                }
            else:
                out = {
                    "status": "error",
                    "prep": prep.to_dict(),
                    "mode": mode,
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
    stage2_only = "--stage2-only" in sys.argv
    positional = [a for a in sys.argv[1:] if not a.startswith("--")]
    kch: Optional[str] = None
    opju: Optional[str] = None
    for p in positional:
        low = p.lower()
        if low.endswith(".opju"):
            opju = p
        elif low.endswith((".xlsx", ".xls")):
            kch = p
    result = run_live_kch(
        kch, opju_path=opju, stage2_only=stage2_only, dry_run=dry
    )
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0 if result["status"] in ("ok", "skipped", "dry_run") else 1


if __name__ == "__main__":
    raise SystemExit(main())
