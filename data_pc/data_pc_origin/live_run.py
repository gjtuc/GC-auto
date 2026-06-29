# -*- coding: utf-8
"""Live E2E harness — Origin/G: 준비·실행 (DATA_PC_SKIP_ORIGIN=0)."""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Optional

from data_pc_origin.o0_types import ProbeResult
from data_pc_origin.o1_opju_path import probe_opju_path
from data_pc_origin.o2_env import skip_origin_active
from data_pc_origin.live_data import LiveJobContext, resolve_live_job
from data_pc_origin.o8_fixtures import SAMPLE_JOB, fx_job_df_full
from data_pc_origin.pipeline_bridge import run_origin_update

LIVE_OPJU_ENV = "DATA_PC_LIVE_OPJU"
ARTIFACT_NAME = "live_e2e_result.json"


@dataclass
class LivePrepResult:
    ready: bool
    reason: str
    opju_path: str
    skip_origin: bool
    g_drive_ok: bool
    probe: ProbeResult
    originpro_import_ok: bool

    def to_dict(self) -> Dict[str, object]:
        return {
            "ready": self.ready,
            "reason": self.reason,
            "opju_path": self.opju_path,
            "skip_origin": self.skip_origin,
            "g_drive_ok": self.g_drive_ok,
            "probe_ok": self.probe.ok,
            "probe_detail": self.probe.detail,
            "originpro_import_ok": self.originpro_import_ok,
        }


def _g_drive_ok() -> bool:
    try:
        return os.path.isdir("G:\\")
    except OSError:
        return False


def _originpro_import_ok() -> bool:
    try:
        import originpro  # noqa: F401

        return True
    except ImportError:
        return False


def prepare_live_e2e(opju_path: Optional[str] = None) -> LivePrepResult:
    """사전 조건 검사 — 실행 전 dry prep."""
    path = (opju_path or os.getenv(LIVE_OPJU_ENV) or "").strip()
    skip = skip_origin_active()
    g_ok = _g_drive_ok()
    imp_ok = _originpro_import_ok()
    probe = probe_opju_path(path) if path else ProbeResult(ok=False, detail="no path")

    if skip:
        return LivePrepResult(False, "DATA_PC_SKIP_ORIGIN=1", path, skip, g_ok, probe, imp_ok)
    if not path:
        return LivePrepResult(False, f"set {LIVE_OPJU_ENV} or pass opju_path", path, skip, g_ok, probe, imp_ok)
    if not g_ok:
        return LivePrepResult(False, "G: drive not available", path, skip, g_ok, probe, imp_ok)
    if not imp_ok:
        return LivePrepResult(False, "originpro import failed", path, skip, g_ok, probe, imp_ok)
    if not probe.ok:
        return LivePrepResult(False, probe.detail or "opju probe failed", path, skip, g_ok, probe, imp_ok)

    return LivePrepResult(True, "ready", path, skip, g_ok, probe, imp_ok)


def run_live_e2e(
    opju_path: Optional[str] = None,
    *,
    artifact_dir: Optional[Path] = None,
    force: bool = False,
    use_fixture: bool = False,
    save_in_place: bool = False,
) -> Dict[str, object]:
    """
    Live 1회 — 준비 실패 시 skip 기록, ready 시 run_origin_update.

    `use_fixture=True` — mock df (gate/CI). 기본은 companion xlsx.
    `save_in_place=False` — `*_Updated.opju` (촉매 --opju 와 동일).
    """
    prep = prepare_live_e2e(opju_path)
    out: Dict[str, object] = {"status": "skipped", "prep": prep.to_dict()}

    if prep.ready or force:
        job_ctx: LiveJobContext | None = None
        try:
            if use_fixture:
                df_data = fx_job_df_full()
                sample_name = SAMPLE_JOB
                identity_key = None
                data_src = "fixture"
            else:
                job_ctx = resolve_live_job(prep.opju_path)
                df_data = job_ctx.df
                sample_name = job_ctx.sample_name
                identity_key = job_ctx.identity_key
                data_src = job_ctx.xlsx_path

            res = run_origin_update(
                prep.opju_path,
                df_data,
                sample_name,
                save_in_place=save_in_place,
                identity_key=identity_key,
            )
            out = {
                "status": "ok" if res.ok else "partial",
                "prep": prep.to_dict(),
                "data_source": data_src,
                "sample_name": sample_name,
                "row_count": res.row_count,
                "sheets_updated": res.sheets_updated,
                "warnings": [w.code for w in res.warnings],
                "save_in_place": save_in_place,
            }
            if job_ctx is not None:
                out["xlsx_path"] = job_ctx.xlsx_path
                out["df_columns"] = list(job_ctx.columns)
        except Exception as exc:  # noqa: BLE001 — live harness records failure
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

    opju = sys.argv[1] if len(sys.argv) > 1 else None
    result = run_live_e2e(opju)
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0 if result["status"] in ("ok", "skipped", "partial") else 1


if __name__ == "__main__":
    raise SystemExit(main())
