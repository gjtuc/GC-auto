# -*- coding: utf-8
"""P14 — runtime bridge harness (JobRunner callback dry/live)."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Dict, Optional

from data_pc_origin.p14_runtime_bridge import (
    ORIGIN_PIPELINE_ENV,
    make_runtime_job_callback,
    origin_pipeline_enabled,
    parse_imap_workflow_result,
    resolve_job_pipeline,
    run_runtime_pipeline_once,
)

ARTIFACT_NAME = "live_runtime_result.json"


def run_live_runtime(
    *,
    artifact_dir: Optional[Path] = None,
    dry_run: bool = False,
    dry_job: bool = False,
    printer=print,
) -> Dict[str, object]:
    """
    P14 실행 검증.

    · `--dry` — live_imap prep dry
    · `--dry-job` — JobRunner mock tick (skip_wifi, temp dir)
    · default — run_runtime_pipeline_once live (IMAP 1+건)
    """
    script_dir = str(Path(__file__).resolve().parent.parent)
    out: Dict[str, Any] = {
        "status": "skipped",
        "origin_pipeline_env": origin_pipeline_enabled(),
        "mode": "dry_job" if dry_job else ("dry" if dry_run else "live"),
    }

    if dry_job:
        try:
            import tempfile

            from data_pc_runtime.layer2_gates import GateConfig
            from data_pc_runtime.layer3_job import JobConfig, JobRunner
            from data_pc_runtime.layer1_state import RuntimePaths

            def _noop():
                return run_runtime_pipeline_once(dry_run=True, printer=printer)

            with tempfile.TemporaryDirectory() as tmp:
                paths = RuntimePaths(tmp, storage_subdir="KCH")
                os.makedirs(paths.storage_dir, exist_ok=True)
                gate = GateConfig(skip_wifi_check=True, cooldown_sec=0)
                runner = JobRunner(paths, _noop)
                job = runner.run_once(
                    JobConfig(gate=gate, reason="P14 dry-job verify")
                )
                out = {
                    "status": "ok" if job.ran else "skipped",
                    "origin_pipeline_env": True,
                    "mode": "dry_job",
                    "job_ran": job.ran,
                    "job_status_code": job.status_code,
                    "workflow_count": job.workflow_count,
                    "gdrive_retry": job.gdrive_retry,
                }
        except Exception as exc:  # noqa: BLE001
            out = {
                "status": "error",
                "mode": "dry_job",
                "error": f"{type(exc).__name__}: {exc}",
            }
    elif dry_run:
        result = run_runtime_pipeline_once(dry_run=True, printer=printer)
        out = {
            "status": "dry_run",
            "origin_pipeline_env": origin_pipeline_enabled(),
            "mode": "dry",
            "pipeline": result._asdict(),
        }
    else:
        try:
            if not origin_pipeline_enabled():
                os.environ[ORIGIN_PIPELINE_ENV] = "1"
            result = run_runtime_pipeline_once(dry_run=False, printer=printer)
            out = {
                "status": "ok",
                "origin_pipeline_env": True,
                "mode": "live",
                "pipeline": result._asdict(),
            }
        except Exception as exc:  # noqa: BLE001
            out = {
                "status": "error",
                "error": f"{type(exc).__name__}: {exc}",
            }

    root = artifact_dir or Path(__file__).resolve().parent
    path = root / ARTIFACT_NAME
    path.write_text(json.dumps(out, indent=2, ensure_ascii=False), encoding="utf-8")
    out["artifact"] = str(path)
    out["resolve_legacy"] = not origin_pipeline_enabled(
        {ORIGIN_PIPELINE_ENV: "0"}
    )
    return out


def main() -> int:
    import sys

    dry = "--dry" in sys.argv
    dry_job = "--dry-job" in sys.argv
    result = run_live_runtime(dry_run=dry, dry_job=dry_job)
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0 if result["status"] in ("ok", "skipped", "dry_run") else 1


if __name__ == "__main__":
    raise SystemExit(main())
