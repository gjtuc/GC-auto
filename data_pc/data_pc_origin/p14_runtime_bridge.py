# -*- coding: utf-8
"""P14 — data_pc_runtime L3 ↔ P층(live_imap) bridge."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Callable, Dict, NamedTuple, Optional

PrintFn = Callable[[str], None]

ORIGIN_PIPELINE_ENV = "DATA_PC_ORIGIN_PIPELINE"


class RuntimePipelineResult(NamedTuple):
    """촉매 `PipelineRunResult` · L3 `_parse_pipeline_result` 호환."""

    workflow_count: int
    gdrive_retry_needed: bool = False


def origin_pipeline_enabled(environ: Optional[Dict[str, str]] = None) -> bool:
    env = environ if environ is not None else os.environ
    return env.get(ORIGIN_PIPELINE_ENV, "").strip().lower() in (
        "1",
        "true",
        "yes",
        "on",
    )


def parse_imap_workflow_result(out: Dict[str, Any]) -> RuntimePipelineResult:
    """`live_imap` / `run_live_imap` JSON → runtime result."""
    status = str(out.get("status", ""))
    prep = out.get("prep") if isinstance(out.get("prep"), dict) else {}
    reason = " ".join(
        str(x)
        for x in (
            out.get("reason", ""),
            prep.get("reason", ""),
            out.get("error", ""),
        )
        if x
    ).lower()

    if status == "ok" and out.get("workflow_ok"):
        return RuntimePipelineResult(1, False)

    gdrive_retry = any(
        token in reason
        for token in (
            "g: drive not available",
            "g: 잠금",
            "gdrive",
            "secuyousb",
        )
    )
    if status == "skipped" and gdrive_retry:
        return RuntimePipelineResult(0, True)
    if status == "error" and gdrive_retry:
        return RuntimePipelineResult(0, True)

    return RuntimePipelineResult(0, False)


def run_runtime_pipeline_once(
    *,
    max_mails: int = 10,
    dry_run: bool = False,
    printer: PrintFn = print,
) -> RuntimePipelineResult:
    """
    P13 `live_imap` 1회 또는 dry — JobRunner callback용.

    pending 여러 건이면 max_mails 까지 반복 (legacy process_new_gc_emails 유사).
    """
    from data_pc_origin.live_imap import run_live_imap

    if dry_run:
        out = run_live_imap(dry_run=True, printer=printer)
        if out.get("status") == "dry_run":
            return RuntimePipelineResult(0, False)
        return parse_imap_workflow_result(out)

    total = 0
    gdrive_retry = False
    for _ in range(max(1, max_mails)):
        out = run_live_imap(dry_run=False, printer=printer)
        parsed = parse_imap_workflow_result(out)
        total += parsed.workflow_count
        gdrive_retry = gdrive_retry or parsed.gdrive_retry_needed
        if parsed.gdrive_retry_needed:
            break
        if out.get("status") == "skipped":
            if "no pending" in str(out.get("reason", "")).lower():
                break
            if any(
                x in str(out.get("reason", "")).lower()
                for x in ("g:", "originpro", "skip_origin")
            ):
                break
        if parsed.workflow_count == 0:
            break
    return RuntimePipelineResult(total, gdrive_retry)


def make_runtime_job_callback(
    *,
    max_mails: int = 10,
    dry_run: bool = False,
    printer: PrintFn = print,
) -> Callable[[], RuntimePipelineResult]:
    """data_pc_runtime `JobRunner` pipeline 인자."""

    def _run() -> RuntimePipelineResult:
        return run_runtime_pipeline_once(
            max_mails=max_mails,
            dry_run=dry_run,
            printer=printer,
        )

    return _run


def load_runtime_pipeline(
    script_dir: str,
    *,
    dry_run: bool = False,
) -> Callable[[], RuntimePipelineResult]:
    """script_dir 기준 env 로드 후 origin pipeline callback."""
    env_path = os.path.join(script_dir, "gc_automation.env")
    if os.path.isfile(env_path):
        try:
            from dotenv import load_dotenv

            load_dotenv(env_path)
        except ImportError:
            pass
    return make_runtime_job_callback(dry_run=dry_run)


def resolve_job_pipeline(
    script_dir: str,
    *,
    dry_run: bool = False,
    environ: Optional[Dict[str, str]] = None,
) -> Callable[[], Any]:
    """`DATA_PC_ORIGIN_PIPELINE=1` → P14 bridge, else legacy 촉매."""
    if origin_pipeline_enabled(environ):
        return load_runtime_pipeline(script_dir, dry_run=dry_run)
    from data_pc_runtime.layer3_job import load_calc_pipeline

    return load_calc_pipeline(script_dir)
