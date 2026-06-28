# -*- coding: utf-8
"""P16 — watch delegation harness (runtime vs legacy)."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Dict, Optional

from data_pc_origin.live_supervisor import build_dry_supervisor_tick
from data_pc_origin.p14_runtime_bridge import ORIGIN_PIPELINE_ENV
from data_pc_origin.p16_watch_bridge import (
    LEGACY_WATCH_ENV,
    describe_watch_mode,
    run_watch_via_runtime,
    should_use_runtime_watch,
)

ARTIFACT_NAME = "live_watch_result.json"


def run_live_watch(
    *,
    artifact_dir: Optional[Path] = None,
    dry_tick: bool = True,
    origin_pipeline: bool = True,
) -> Dict[str, object]:
    """
    P16 실행 검증.

    · default — runtime watch 1 tick (supervisor dry, origin pipeline)
    · infinite `run_supervisor` 는 실행하지 않음
    """
    script_dir = str(Path(__file__).resolve().parent.parent)
    mode = describe_watch_mode(
        {
            ORIGIN_PIPELINE_ENV: "1" if origin_pipeline else "0",
            LEGACY_WATCH_ENV: "0",
        }
    )
    out: Dict[str, Any] = {
        "status": "skipped",
        "watch_mode": mode,
        "runtime_watch": should_use_runtime_watch(
            {ORIGIN_PIPELINE_ENV: "1" if origin_pipeline else "0"}
        ),
    }

    if dry_tick:
        try:
            os.environ[ORIGIN_PIPELINE_ENV] = "1" if origin_pipeline else "0"
            os.environ[LEGACY_WATCH_ENV] = "0"
            tick, storage_root = build_dry_supervisor_tick(
                script_dir,
                origin_pipeline=origin_pipeline,
                dry_run_pipeline=True,
            )
            out = {
                "status": "ok",
                "watch_mode": describe_watch_mode(),
                "runtime_watch": True,
                "mode": "dry_tick",
                "tick": tick,
                "storage_root": storage_root,
                "delegates_to": "data_pc_runtime.layer4_supervisor",
            }
        except Exception as exc:  # noqa: BLE001
            out = {
                "status": "error",
                "mode": "dry_tick",
                "error": f"{type(exc).__name__}: {exc}",
            }
    else:
        try:
            os.environ[ORIGIN_PIPELINE_ENV] = "1"
            os.environ[LEGACY_WATCH_ENV] = "0"
            with _patch_run_supervisor_once() as called:
                run_watch_via_runtime(script_dir, skip_wifi_check=True)
            out = {
                "status": "ok" if called["n"] == 1 else "error",
                "watch_mode": "runtime_origin",
                "mode": "delegate_once",
                "supervisor_called": called["n"] == 1,
            }
        except Exception as exc:  # noqa: BLE001
            out = {
                "status": "error",
                "mode": "delegate_once",
                "error": f"{type(exc).__name__}: {exc}",
            }

    root = artifact_dir or Path(__file__).resolve().parent
    path = root / ARTIFACT_NAME
    path.write_text(json.dumps(out, indent=2, ensure_ascii=False), encoding="utf-8")
    out["artifact"] = str(path)
    return out


def _patch_run_supervisor_once():
    from contextlib import contextmanager
    from unittest.mock import patch

    state = {"n": 0}

    @contextmanager
    def _cm():
        def _fake(_script_dir: str) -> None:
            state["n"] += 1

        with patch(
            "data_pc_runtime.layer4_supervisor.run_supervisor",
            side_effect=_fake,
        ):
            yield state

    return _cm()


def main() -> int:
    import sys

    dry = "--delegate" not in sys.argv
    origin = "--legacy-pipeline" not in sys.argv
    result = run_live_watch(dry_tick=dry, origin_pipeline=origin)
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0 if result["status"] in ("ok", "skipped") else 1


if __name__ == "__main__":
    raise SystemExit(main())
