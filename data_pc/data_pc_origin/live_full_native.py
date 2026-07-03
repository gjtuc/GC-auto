# -*- coding: utf-8
"""P12-F — FULL_ARCHIVE live (KCH native stage2 + setup_experiment_folder stage3)."""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Optional

from data_pc_origin.live_common import LIVE_KCH_XLSX_ENV, make_catalyst_stage2_runner
from data_pc_origin.live_run import _g_drive_ok, _originpro_import_ok
from data_pc_origin.o2_env import skip_origin_active
from data_pc_origin.p0_types import WorkflowMode
from data_pc_origin.p2_paths import resolve_stage4_save_path
from data_pc_origin.p6_catalyst_adapter import make_stage3_runner
from data_pc_origin.workflow_bridge import run_workflow_bridged_detailed

ARTIFACT_NAME = "live_full_native_result.json"


@dataclass
class LiveFullNativePrep:
    ready: bool
    reason: str
    kch_path: str
    skip_origin: bool
    g_drive_ok: bool
    originpro_import_ok: bool

    def to_dict(self) -> Dict[str, object]:
        return {
            "ready": self.ready,
            "reason": self.reason,
            "kch_path": self.kch_path,
            "skip_origin": self.skip_origin,
            "g_drive_ok": self.g_drive_ok,
            "originpro_import_ok": self.originpro_import_ok,
        }


def prepare_live_full_native(kch_path: Optional[str] = None) -> LiveFullNativePrep:
    kch = (kch_path or os.getenv(LIVE_KCH_XLSX_ENV) or "").strip()
    skip = skip_origin_active()
    g_ok = _g_drive_ok()
    imp_ok = _originpro_import_ok()

    if not kch:
        return LiveFullNativePrep(
            False,
            f"set {LIVE_KCH_XLSX_ENV} or pass kch_path",
            kch,
            skip,
            g_ok,
            imp_ok,
        )
    if not os.path.isfile(kch):
        return LiveFullNativePrep(
            False,
            f"kch xlsx not found: {kch}",
            kch,
            skip,
            g_ok,
            imp_ok,
        )
    if skip:
        return LiveFullNativePrep(
            False, "DATA_PC_SKIP_ORIGIN=1", kch, skip, g_ok, imp_ok
        )
    if not g_ok:
        return LiveFullNativePrep(
            False, "G: drive not available", kch, skip, g_ok, imp_ok
        )
    if not imp_ok:
        return LiveFullNativePrep(
            False, "originpro import failed", kch, skip, g_ok, imp_ok
        )
    return LiveFullNativePrep(True, "ready", kch, skip, g_ok, imp_ok)


def run_live_full_native(
    kch_path: Optional[str] = None,
    *,
    artifact_dir: Optional[Path] = None,
    dry_run: bool = False,
    printer=print,
) -> Dict[str, object]:
    """
    FULL_ARCHIVE live — P6 process_excel + setup_experiment_folder + Origin in-place.

    P10-F 와 달리 stage3 주입 없음 — 실제 G: 폴더 생성·갱신.
    """
    prep = prepare_live_full_native(kch_path)
    out: Dict[str, Any] = {
        "status": "skipped",
        "prep": prep.to_dict(),
        "mode": WorkflowMode.FULL_ARCHIVE.value,
        "data_source": "kch_raw",
        "native_stage3": True,
    }

    if prep.ready and dry_run:
        try:
            from data_pc_origin.live_data import _load_catalyst_module

            catalyst = _load_catalyst_module()
            base = catalyst.generate_experiment_basename(prep.kch_path)
            rxn = catalyst.reaction_type_from_output_file(prep.kch_path)
            out = {
                "status": "dry_run",
                "prep": prep.to_dict(),
                "mode": WorkflowMode.FULL_ARCHIVE.value,
                "data_source": "kch_raw",
                "native_stage3": True,
                "experiment_basename": base,
                "reaction_type": rxn,
            }
        except Exception as exc:  # noqa: BLE001
            out = {
                "status": "error",
                "prep": prep.to_dict(),
                "error": f"{type(exc).__name__}: {exc}",
            }
    elif prep.ready and not dry_run:
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
                opju_path=None,
                auto_archive=True,
                skip_origin=False,
                catalyst_module=catalyst,
                environ=live_env,
                printer=_capture,
                stage2_runner=make_catalyst_stage2_runner(
                    catalyst, printer=_capture
                ),
                stage3_runner=make_stage3_runner(catalyst),
            )
            target_opju = ""
            archive_xlsx = ""
            save_path = ""
            sheets = 0
            row_count = 0
            sample_name = ""
            if wf is not None:
                if wf.stage2 is not None:
                    row_count = len(wf.stage2.artifacts.df)
                    sample_name = wf.stage2.metadata.sample_name
                if wf.stage3 is not None:
                    target_opju = wf.stage3.target_opju
                    archive_xlsx = wf.stage3.archive_xlsx
                    save_path = resolve_stage4_save_path(target_opju, save_in_place=True)
                if wf.stage4 is not None and wf.stage4.origin is not None:
                    sheets = wf.stage4.origin.sheets_updated
            if ok:
                out = {
                    "status": "ok",
                    "prep": prep.to_dict(),
                    "mode": WorkflowMode.FULL_ARCHIVE.value,
                    "data_source": "kch_raw",
                    "native_stage3": True,
                    "workflow_ok": ok,
                    "row_count": row_count,
                    "sample_name": sample_name,
                    "target_opju": target_opju,
                    "archive_xlsx": archive_xlsx,
                    "sheets_updated": sheets,
                    "save_path": save_path,
                    "save_path_exists": bool(save_path and os.path.isfile(save_path)),
                    "save_in_place": True,
                }
            else:
                out = {
                    "status": "error",
                    "prep": prep.to_dict(),
                    "mode": WorkflowMode.FULL_ARCHIVE.value,
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
    positional = [a for a in sys.argv[1:] if not a.startswith("--")]
    kch = positional[0] if positional else None
    result = run_live_full_native(kch, dry_run=dry)
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0 if result["status"] in ("ok", "skipped", "dry_run") else 1


if __name__ == "__main__":
    raise SystemExit(main())
