# -*- coding: utf-8
"""P18 — production full E2E prep (IMAP → native s2+s3 → Origin)."""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Any, Dict, Optional

from data_pc_origin.live_run import _g_drive_ok, _originpro_import_ok
from data_pc_origin.p13_imap_adapter import prepare_imap
from data_pc_origin.p14_runtime_bridge import origin_pipeline_enabled
from data_pc_origin.p17_env_config import SKIP_ORIGIN_ENV, load_script_env, effective_origin_config

PRODUCTION_STACK = "imap_full_native_origin"
E2E_LIVE_ENV = "DATA_PC_E2E_LIVE"


@dataclass(frozen=True)
class ProductionE2ePrep:
    ready: bool
    reason: str
    stack: str
    origin_pipeline: bool
    skip_origin: bool
    full_e2e_ready: bool
    imap_ready: bool
    email_masked: str
    g_drive_ok: bool
    originpro_import_ok: bool

    def to_dict(self) -> Dict[str, Any]:
        return {
            "ready": self.ready,
            "reason": self.reason,
            "stack": self.stack,
            "origin_pipeline": self.origin_pipeline,
            "skip_origin": self.skip_origin,
            "full_e2e_ready": self.full_e2e_ready,
            "imap_ready": self.imap_ready,
            "email_masked": self.email_masked,
            "g_drive_ok": self.g_drive_ok,
            "originpro_import_ok": self.originpro_import_ok,
        }


def _blocking_reasons(
    *,
    origin_pipeline: bool,
    skip_origin: bool,
    imap_ready: bool,
    imap_reason: str,
    g_drive_ok: bool,
    originpro_ok: bool,
) -> list[str]:
    reasons: list[str] = []
    if not origin_pipeline:
        reasons.append("DATA_PC_ORIGIN_PIPELINE off")
    if skip_origin:
        reasons.append(f"{SKIP_ORIGIN_ENV}=1")
    if not imap_ready:
        reasons.append(imap_reason or "IMAP not ready")
    if not g_drive_ok:
        reasons.append("G: drive not available")
    if not originpro_ok:
        reasons.append("originpro import failed")
    return reasons


def prepare_production_e2e(
    script_dir: str,
    *,
    environ: Optional[Dict[str, str]] = None,
) -> ProductionE2ePrep:
    """Full production E2E 사전 조건 — env · IMAP · G: · originpro."""
    load_script_env(script_dir)
    cfg = effective_origin_config(script_dir, environ=environ)
    imap = prepare_imap()
    g_ok = _g_drive_ok()
    imp_ok = _originpro_import_ok()

    reasons = _blocking_reasons(
        origin_pipeline=bool(cfg["origin_pipeline"]),
        skip_origin=bool(cfg["skip_origin"]),
        imap_ready=imap.ready,
        imap_reason=imap.reason,
        g_drive_ok=g_ok,
        originpro_ok=imp_ok,
    )
    ready = not reasons
    reason = "ready" if ready else "; ".join(reasons)

    return ProductionE2ePrep(
        ready=ready,
        reason=reason,
        stack=PRODUCTION_STACK,
        origin_pipeline=bool(cfg["origin_pipeline"]),
        skip_origin=bool(cfg["skip_origin"]),
        full_e2e_ready=bool(cfg["full_e2e_ready"]),
        imap_ready=imap.ready,
        email_masked=imap.email_masked,
        g_drive_ok=g_ok,
        originpro_import_ok=imp_ok,
    )


def e2e_live_enabled(environ: Optional[Dict[str, str]] = None) -> bool:
    env = environ if environ is not None else os.environ
    return env.get(E2E_LIVE_ENV, "").strip().lower() in ("1", "true", "yes", "on")


def apply_production_e2e_env() -> None:
    """live 1회 실행용 — Origin on · origin pipeline on."""
    os.environ["DATA_PC_ORIGIN_PIPELINE"] = "1"
    os.environ[SKIP_ORIGIN_ENV] = "0"


def run_production_imap_once(
    *,
    artifact_dir=None,
    printer=print,
):
    """`live_imap` full path with production env applied."""
    from pathlib import Path

    from data_pc_origin.live_imap import run_live_imap

    apply_production_e2e_env()
    return run_live_imap(
        artifact_dir=artifact_dir or Path(__file__).resolve().parent,
        dry_run=False,
        printer=printer,
    )
