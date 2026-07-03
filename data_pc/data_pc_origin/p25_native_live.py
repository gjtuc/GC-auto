# -*- coding: utf-8
"""P25 — native env production live (no harness env override)."""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Any, Dict, Optional

from data_pc_origin.p17_env_config import SKIP_ORIGIN_ENV, effective_origin_config, load_script_env
from data_pc_origin.p18_production_e2e import prepare_production_e2e
from data_pc_origin.p24_ops_rollup import build_ops_rollup_manifest

NATIVE_LIVE_ENV = "DATA_PC_NATIVE_LIVE"


@dataclass
class NativeLivePrep:
    ready: bool
    reason: str
    skip_origin: bool
    full_e2e_ready: bool
    ops_ready: bool
    production_e2e: Dict[str, Any]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "ready": self.ready,
            "reason": self.reason,
            "skip_origin": self.skip_origin,
            "full_e2e_ready": self.full_e2e_ready,
            "ops_ready": self.ops_ready,
            "production_e2e": dict(self.production_e2e),
        }


def native_live_enabled(environ: Optional[Dict[str, str]] = None) -> bool:
    env = environ if environ is not None else os.environ
    return env.get(NATIVE_LIVE_ENV, "").strip().lower() in ("1", "true", "yes", "on")


def prep_native_production_live(script_dir: str) -> NativeLivePrep:
    """P21 cutover env 파일만 사용 — `apply_production_e2e_env` 호출 없음."""
    load_script_env(script_dir)
    cfg = effective_origin_config(script_dir)
    e2e = prepare_production_e2e(script_dir)
    ops = build_ops_rollup_manifest(script_dir)

    failures: list[str] = []
    if cfg["skip_origin"]:
        failures.append(f"{SKIP_ORIGIN_ENV}=1 in env file")
    if not cfg["full_e2e_ready"]:
        failures.append("full_e2e_ready false")
    if not ops.production_ready:
        failures.append(f"ops: {ops.reason}")
    if not e2e.ready:
        failures.append(f"e2e: {e2e.reason}")

    ready = not failures
    return NativeLivePrep(
        ready=ready,
        reason="ready" if ready else "; ".join(failures),
        skip_origin=bool(cfg["skip_origin"]),
        full_e2e_ready=bool(cfg["full_e2e_ready"]),
        ops_ready=ops.production_ready,
        production_e2e=e2e.to_dict(),
    )


def run_native_production_imap_once(
    *,
    artifact_dir=None,
    printer=print,
):
    """`live_imap` — gc_automation.env 만 로드 (override 금지)."""
    from pathlib import Path

    from data_pc_origin.live_imap import run_live_imap

    script_dir = str(Path(__file__).resolve().parent.parent)
    load_script_env(script_dir)
    return run_live_imap(
        artifact_dir=artifact_dir or Path(__file__).resolve().parent,
        dry_run=False,
        printer=printer,
    )


def validate_native_live_artifact(payload: Dict[str, Any]) -> bool:
    if payload.get("status") not in ("ok", "skipped", "partial"):
        return False
    prep = payload.get("prep")
    if not isinstance(prep, dict):
        return False
    return "skip_origin" in prep and prep.get("skip_origin") is False
