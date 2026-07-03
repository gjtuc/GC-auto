# -*- coding: utf-8
"""P16 — legacy data_pc_watch → data_pc_runtime supervisor bridge."""

from __future__ import annotations

import os
from typing import Dict, Optional

from data_pc_origin.p14_runtime_bridge import ORIGIN_PIPELINE_ENV, origin_pipeline_enabled

LEGACY_WATCH_ENV = "DATA_PC_LEGACY_WATCH"
RUNTIME_WATCH_ENV = "DATA_PC_RUNTIME_WATCH"
SKIP_WIFI_ENV = "DATA_PC_SKIP_WIFI_CHECK"


def should_use_runtime_watch(environ: Optional[Dict[str, str]] = None) -> bool:
    """
    기본: runtime supervisor 사용.

    · `DATA_PC_LEGACY_WATCH=1` → 구 DataPcWatchRunner
    · `DATA_PC_RUNTIME_WATCH=0` → legacy (명시적 off)
    · `DATA_PC_ORIGIN_PIPELINE=1` → runtime (origin 경로)
    """
    env = environ if environ is not None else os.environ
    if env.get(LEGACY_WATCH_ENV, "").strip().lower() in ("1", "true", "yes", "on"):
        return False
    if env.get(RUNTIME_WATCH_ENV, "").strip().lower() in ("0", "false", "no", "off"):
        return False
    if origin_pipeline_enabled(env):
        return True
    if env.get(RUNTIME_WATCH_ENV, "").strip().lower() in ("1", "true", "yes", "on"):
        return True
    return True


def apply_watch_env(*, skip_wifi_check: bool = False, origin_pipeline: bool | None = None) -> None:
    """`--watch` / harness 공통 env 준비."""
    if skip_wifi_check:
        os.environ[SKIP_WIFI_ENV] = "1"
    if origin_pipeline is True:
        os.environ[ORIGIN_PIPELINE_ENV] = "1"
    elif origin_pipeline is False:
        os.environ[ORIGIN_PIPELINE_ENV] = "0"


def run_watch_via_runtime(script_dir: str, *, skip_wifi_check: bool = False) -> None:
    """`촉매 반응 계산.py --watch` → L4 supervisor (resolve_job_pipeline)."""
    env_path = os.path.join(script_dir, "gc_automation.env")
    if os.path.isfile(env_path):
        try:
            from dotenv import load_dotenv

            load_dotenv(env_path)
        except ImportError:
            pass
    apply_watch_env(skip_wifi_check=skip_wifi_check)
    from data_pc_runtime.layer4_supervisor import run_supervisor

    run_supervisor(script_dir)


def describe_watch_mode(environ: Optional[Dict[str, str]] = None) -> str:
    env = environ if environ is not None else os.environ
    if not should_use_runtime_watch(env):
        return "legacy"
    if origin_pipeline_enabled(env):
        return "runtime_origin"
    return "runtime_legacy_pipeline"
