# -*- coding: utf-8 -*-
"""작업 큐 Hook end-to-end 자가 검증 (Agent가 실행·결과 JSON 저장)."""
from __future__ import annotations

import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / ".cursor" / "hooks"))

from agent_queue_lib import (  # noqa: E402
    LOG_PATH,
    evaluate_stop,
    first_unchecked_task,
    load_state,
)

RESULT_PATH = ROOT / ".cursor" / "hooks" / "LAST_HOOK_E2E_RESULT.json"


def _run_ps1_test() -> dict:
    ps1 = ROOT / ".cursor" / "hooks" / "test_task_queue_continue.ps1"
    r = subprocess.run(
        [
            "powershell",
            "-NoProfile",
            "-ExecutionPolicy",
            "Bypass",
            "-File",
            str(ps1),
        ],
        cwd=str(ROOT),
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    return {
        "exit_code": r.returncode,
        "pass": r.returncode == 0 and "ALL PASS" in (r.stdout or ""),
        "tail": (r.stdout or "").strip().splitlines()[-2:],
    }


def _simulate_continue() -> dict:
    before_lines = 0
    if LOG_PATH.is_file():
        before_lines = len(LOG_PATH.read_text(encoding="utf-8", errors="replace").splitlines())
    payload = {"status": "completed", "loop_count": 1}
    out = evaluate_stop(payload)
    after_lines = len(LOG_PATH.read_text(encoding="utf-8", errors="replace").splitlines())
    task = first_unchecked_task()
    msg = out.get("followup_message") or ""
    return {
        "next_task": task,
        "followup_len": len(msg),
        "followup_has_task": bool(task and task in msg),
        "followup_preview": msg[:200] if msg else "",
        "log_lines_added": after_lines - before_lines,
    }


def main() -> int:
    state = load_state()
    ps1 = _run_ps1_test()
    cont = _simulate_continue()
    ok = (
        state
        and state.get("armed")
        and state.get("status") == "running"
        and ps1["pass"]
        and cont["next_task"]
        and cont["followup_has_task"]
        and cont["log_lines_added"] >= 1
    )
    result = {
        "at": datetime.now(timezone.utc).isoformat(),
        "ok": ok,
        "state": state,
        "ps1_test": ps1,
        "continue_sim": cont,
        "verdict": (
            "HOOK_CHAIN_OK"
            if ok
            else "HOOK_CHAIN_FAIL — Cursor stop Hook on turn end may still not fire"
        ),
    }
    RESULT_PATH.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    try:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    except UnicodeEncodeError:
        print(json.dumps(result, ensure_ascii=True, indent=2))
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
