# -*- coding: utf-8
"""Live harness 공통 — prep · companion stage2 · stage3 주입."""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Dict, Optional

from data_pc_origin.live_data import LiveJobContext, find_companion_xlsx
from data_pc_origin.live_run import LIVE_OPJU_ENV, _g_drive_ok, _originpro_import_ok
from data_pc_origin.o0_types import ProbeResult
from data_pc_origin.o1_opju_path import probe_opju_path
from data_pc_origin.o2_env import skip_origin_active
from data_pc_origin.p0_types import Stage2Artifacts
from data_pc_origin.p1_payload import assemble_stage2_metadata
from data_pc_origin.p5_workflow import Stage2RunResult, Stage3Result, Stage3Runner

LIVE_XLSX_ENV = "DATA_PC_LIVE_XLSX"
LIVE_MAIL_XLSX_ENV = "DATA_PC_LIVE_MAIL_XLSX"
LIVE_KCH_XLSX_ENV = "DATA_PC_LIVE_KCH_XLSX"


@dataclass
class LiveHarnessPrep:
    ready: bool
    reason: str
    opju_path: str
    excel_path: str
    skip_origin: bool
    g_drive_ok: bool
    probe: ProbeResult
    originpro_import_ok: bool

    def to_dict(self) -> Dict[str, object]:
        return {
            "ready": self.ready,
            "reason": self.reason,
            "opju_path": self.opju_path,
            "excel_path": self.excel_path,
            "skip_origin": self.skip_origin,
            "g_drive_ok": self.g_drive_ok,
            "probe_ok": self.probe.ok,
            "probe_detail": self.probe.detail,
            "originpro_import_ok": self.originpro_import_ok,
        }


def resolve_live_excel_path(
    opju_path: str,
    *,
    xlsx_path: Optional[str] = None,
    mail_xlsx: Optional[str] = None,
) -> str:
    """explicit xlsx · mail env · companion 순."""
    for candidate in (
        (xlsx_path or "").strip(),
        (mail_xlsx or os.getenv(LIVE_MAIL_XLSX_ENV) or "").strip(),
        (os.getenv(LIVE_XLSX_ENV) or "").strip(),
    ):
        if candidate:
            return candidate
    return find_companion_xlsx(opju_path) or ""


def prepare_live_harness(
    opju_path: Optional[str] = None,
    *,
    xlsx_path: Optional[str] = None,
    mail_xlsx: Optional[str] = None,
    require_opju: bool = True,
) -> LiveHarnessPrep:
    path = (opju_path or os.getenv(LIVE_OPJU_ENV) or "").strip()
    skip = skip_origin_active()
    g_ok = _g_drive_ok()
    imp_ok = _originpro_import_ok()
    probe = probe_opju_path(path) if path else ProbeResult(ok=False, detail="no path")
    excel = ""
    if path:
        excel = resolve_live_excel_path(path, xlsx_path=xlsx_path, mail_xlsx=mail_xlsx)
    elif mail_xlsx or os.getenv(LIVE_MAIL_XLSX_ENV):
        excel = (mail_xlsx or os.getenv(LIVE_MAIL_XLSX_ENV) or "").strip()

    if skip:
        return LiveHarnessPrep(
            False, "DATA_PC_SKIP_ORIGIN=1", path, excel, skip, g_ok, probe, imp_ok
        )
    if require_opju and not path:
        return LiveHarnessPrep(
            False,
            f"set {LIVE_OPJU_ENV} or pass opju_path",
            path,
            excel,
            skip,
            g_ok,
            probe,
            imp_ok,
        )
    if not g_ok:
        return LiveHarnessPrep(
            False, "G: drive not available", path, excel, skip, g_ok, probe, imp_ok
        )
    if not imp_ok:
        return LiveHarnessPrep(
            False, "originpro import failed", path, excel, skip, g_ok, probe, imp_ok
        )
    if require_opju and not probe.ok:
        return LiveHarnessPrep(
            False,
            probe.detail or "opju probe failed",
            path,
            excel,
            skip,
            g_ok,
            probe,
            imp_ok,
        )
    if not excel or not os.path.isfile(excel):
        return LiveHarnessPrep(
            False,
            "xlsx not found (set DATA_PC_LIVE_XLSX or DATA_PC_LIVE_MAIL_XLSX)",
            path,
            excel,
            skip,
            g_ok,
            probe,
            imp_ok,
        )
    return LiveHarnessPrep(True, "ready", path, excel, skip, g_ok, probe, imp_ok)


def make_companion_stage2_runner(
    job: LiveJobContext,
    *,
    label: str = "companion xlsx",
    printer=print,
):
    def _run(_excel_path: str) -> Stage2RunResult | None:
        printer(f"\n[2단계] {label}: {os.path.basename(job.xlsx_path)}")
        meta = assemble_stage2_metadata(
            sample_name=job.sample_name,
            identity_key=job.identity_key,
            saved_excel=job.xlsx_path,
        )
        arts = Stage2Artifacts(
            df=job.df,
            saved_excel=job.xlsx_path,
            warnings=(),
            feed_source_desc=f"{label} (live)",
        )
        printer(f" ✅ 엑셀 계산 완료: {os.path.basename(job.xlsx_path)}")
        printer(f" 🏷️ Origin 시료명: {job.sample_name}")
        printer(f" 📊 {job.row_count}행 · {len(job.columns)}열")
        return Stage2RunResult(artifacts=arts, metadata=meta)

    return _run


def make_catalyst_stage2_runner(
    module,
    *,
    printer=print,
):
    """P6 `process_excel` — companion shortcut 없음 (P11-K live)."""
    from data_pc_origin.workflow_bridge import make_stage2_runner_with_ux

    return make_stage2_runner_with_ux(module, printer=printer)


def make_injected_stage3_runner(
    target_opju: str,
    archive_xlsx: str,
) -> Stage3Runner:
    """기존 G: 폴더 — `setup_experiment_folder` 생략 (live in-place)."""

    def _run(_excel_path: str, _stage2: Stage2RunResult) -> Stage3Result | None:
        return Stage3Result(
            target_opju=target_opju,
            archive_xlsx=archive_xlsx,
        )

    return _run
