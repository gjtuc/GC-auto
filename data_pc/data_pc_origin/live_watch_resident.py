# -*- coding: utf-8
"""P26 — watch resident smoke harness."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, Optional
from unittest.mock import patch

from data_pc_origin.p26_watch_resident import (
    inspect_watchdog_runtime_command,
    prep_watch_resident_smoke,
    run_watch_resident_delegate,
    validate_watch_resident_artifact,
)

ARTIFACT_NAME = "live_watch_resident_result.json"


def run_live_watch_resident(
    *,
    artifact_dir: Optional[Path] = None,
    script_dir: Optional[str] = None,
    delegate: bool = False,
) -> Dict[str, object]:
    """
    P26 실행 검증.

    · default — native env prep + watchdog inspect
    · `--delegate` — `run_data_pc_watch` → patched `run_supervisor` 1회
    """
    root_dir = script_dir or str(Path(__file__).resolve().parent.parent)
    prep = prep_watch_resident_smoke(root_dir)
    watchdog = inspect_watchdog_runtime_command(root_dir)

    out: Dict[str, Any] = {
        "status": "ok" if prep.ready else "partial",
        "mode": "prep",
        "prep": prep.to_dict(),
        "watchdog": watchdog,
        "native_env": True,
    }

    if delegate:
        if not prep.ready:
            out = {
                "status": "skipped",
                "mode": "delegate",
                "reason": prep.reason,
                "prep": prep.to_dict(),
                "native_env": True,
            }
        else:
            try:
                state = {"n": 0}

                def _supervisor_once(_script_dir: str) -> None:
                    state["n"] += 1

                with patch(
                    "data_pc_runtime.layer4_supervisor.run_supervisor",
                    side_effect=_supervisor_once,
                ):
                    delegate_out = run_watch_resident_delegate(
                        root_dir,
                        skip_wifi_check=True,
                    )
                out = {
                    "status": "ok" if state["n"] == 1 else "error",
                    "mode": "delegate",
                    "prep": prep.to_dict(),
                    "watchdog": watchdog,
                    "delegate": delegate_out,
                    "supervisor_called": state["n"] == 1,
                    "native_env": True,
                }
            except Exception as exc:  # noqa: BLE001
                out = {
                    "status": "error",
                    "mode": "delegate",
                    "prep": prep.to_dict(),
                    "native_env": True,
                    "error": f"{type(exc).__name__}: {exc}",
                }

    root = artifact_dir or Path(__file__).resolve().parent
    path = root / ARTIFACT_NAME
    path.write_text(json.dumps(out, indent=2, ensure_ascii=False), encoding="utf-8")
    out["artifact"] = str(path)
    out["artifact_valid"] = validate_watch_resident_artifact(out)
    if delegate and out.get("mode") == "delegate" and out.get("status") == "ok":
        out["artifact_valid"] = out["artifact_valid"] and out.get("supervisor_called") is True
    path.write_text(json.dumps(out, indent=2, ensure_ascii=False), encoding="utf-8")
    return out


def main() -> int:
    import sys

    do_delegate = "--delegate" in sys.argv
    result = run_live_watch_resident(delegate=do_delegate)
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0 if result.get("status") in ("ok", "partial", "skipped") else 1


if __name__ == "__main__":
    raise SystemExit(main())
