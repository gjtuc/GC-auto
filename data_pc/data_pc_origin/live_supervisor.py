# -*- coding: utf-8
"""P15 — L4 Supervisor harness (resolve pipeline + dry tick)."""

from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

from data_pc_origin.p14_runtime_bridge import (
    ORIGIN_PIPELINE_ENV,
    origin_pipeline_enabled,
    resolve_job_pipeline,
)

ARTIFACT_NAME = "live_supervisor_result.json"


def build_dry_supervisor_tick(
    script_dir: str,
    *,
    origin_pipeline: bool = True,
    dry_run_pipeline: bool = True,
) -> Tuple[Any, str]:
    """
    temp storage + JobRunner(resolve) + Supervisor 1 tick.

    Returns (job_result_dict, storage_root).
    """
    from data_pc_runtime.layer1_state import RuntimePaths, StateStore
    from data_pc_runtime.layer2_gates import GateConfig
    from data_pc_runtime.layer3_job import JobConfig, JobRunner
    from data_pc_runtime.layer4_supervisor import Supervisor, SupervisorConfig

    env_path = os.path.join(script_dir, "gc_automation.env")
    if os.path.isfile(env_path):
        try:
            from dotenv import load_dotenv

            load_dotenv(env_path)
        except ImportError:
            pass

    os.environ[ORIGIN_PIPELINE_ENV] = "1" if origin_pipeline else "0"
    tmp = tempfile.mkdtemp(prefix="p15_sup_")
    paths = RuntimePaths(tmp, storage_subdir="KCH")
    os.makedirs(paths.storage_dir, exist_ok=True)
    gate = GateConfig(skip_wifi_check=True, cooldown_sec=0)
    pipeline = resolve_job_pipeline(script_dir, dry_run=dry_run_pipeline)
    job = JobRunner(paths, pipeline, store=StateStore(paths))
    sup = Supervisor(
        script_dir,
        job=job,
        sup_cfg=SupervisorConfig(boot_mail_check=False),
        gate=gate,
    )
    sup.run_once_tick()
    status = StateStore(paths).load_status()
    return (
        {
            "status_code": status.status_code,
            "message": status.message,
            "gate_detail": status.gate_detail,
        },
        tmp,
    )


def run_live_supervisor(
    *,
    artifact_dir: Optional[Path] = None,
    dry_tick: bool = True,
    origin_pipeline: bool = True,
) -> Dict[str, object]:
    """
    P15 실행 검증.

    · default — Supervisor 1 tick, origin pipeline dry_run callback
    """
    script_dir = str(Path(__file__).resolve().parent.parent)
    out: Dict[str, Any] = {
        "status": "skipped",
        "origin_pipeline_env": origin_pipeline_enabled(),
        "mode": "dry_tick" if dry_tick else "live_tick",
    }

    if dry_tick:
        try:
            tick, storage_root = build_dry_supervisor_tick(
                script_dir,
                origin_pipeline=origin_pipeline,
                dry_run_pipeline=True,
            )
            out = {
                "status": "ok",
                "origin_pipeline_env": origin_pipeline,
                "mode": "dry_tick",
                "tick": tick,
                "storage_root": storage_root,
                "pipeline_resolved": origin_pipeline,
            }
        except Exception as exc:  # noqa: BLE001
            out = {
                "status": "error",
                "mode": "dry_tick",
                "error": f"{type(exc).__name__}: {exc}",
            }
    else:
        try:
            from data_pc_runtime.layer4_supervisor import Supervisor, SupervisorConfig

            os.environ[ORIGIN_PIPELINE_ENV] = "1"
            sup = Supervisor(
                script_dir,
                sup_cfg=SupervisorConfig(boot_mail_check=False, poll_sec=60),
            )
            sup.run_once_tick()
            out = {
                "status": "ok",
                "origin_pipeline_env": True,
                "mode": "live_tick",
            }
        except Exception as exc:  # noqa: BLE001
            out = {
                "status": "error",
                "mode": "live_tick",
                "error": f"{type(exc).__name__}: {exc}",
            }

    root = artifact_dir or Path(__file__).resolve().parent
    path = root / ARTIFACT_NAME
    path.write_text(json.dumps(out, indent=2, ensure_ascii=False), encoding="utf-8")
    out["artifact"] = str(path)
    return out


def main() -> int:
    import sys

    dry = "--live" not in sys.argv
    origin = "--legacy" not in sys.argv
    result = run_live_supervisor(dry_tick=dry, origin_pipeline=origin)
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0 if result["status"] in ("ok", "skipped") else 1


if __name__ == "__main__":
    raise SystemExit(main())
