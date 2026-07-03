# -*- coding: utf-8 -*-
"""작업 큐 Hook 진단 — Cursor UI에 안 보일 때 로컬에서 실동작 확인."""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / ".cursor" / "hooks"))

from agent_queue_lib import (  # noqa: E402
    LOG_PATH,
    QUEUE_PATH,
    STATE_PATH,
    evaluate_stop,
    first_unchecked_task,
    load_state,
)


def _safe_print(text: str) -> None:
    enc = sys.stdout.encoding or "utf-8"
    try:
        print(text)
    except UnicodeEncodeError:
        print(text.encode(enc, errors="replace").decode(enc, errors="replace"))


def main() -> int:
    print("=== GC Agent Task Queue Hook diagnose ===\n")
    print(f"repo: {ROOT}")
    print(f"hooks.json: {(ROOT / '.cursor' / 'hooks.json').is_file()}")
    print(f"state: {STATE_PATH}")
    print(f"queue: {QUEUE_PATH}")
    print(f"log:   {LOG_PATH}\n")

    state = load_state()
    print("--- agent_queue_state.json ---")
    print(json.dumps(state, ensure_ascii=False, indent=2) if state else "(missing)")

    task = first_unchecked_task()
    print("\n--- next [ ] task ---")
    _safe_print(task or "(none)")

    payload = {"status": "completed", "loop_count": 0}
    result = evaluate_stop(payload)
    print("\n--- continue Hook simulate (status=completed) ---")
    if result.get("followup_message"):
        msg = result["followup_message"]
        print(f"followup_message: {len(msg)} chars")
        preview = ROOT / ".cursor" / "hooks" / "LAST_FOLLOWUP_PREVIEW.txt"
        preview.write_text(msg, encoding="utf-8")
        print(f"saved: {preview}")
    else:
        print("followup_message: NONE (empty {})")

    print("\n--- agent_queue_stop.log (last 8 lines) ---")
    if LOG_PATH.is_file():
        for line in LOG_PATH.read_text(encoding="utf-8", errors="replace").splitlines()[-8:]:
            _safe_print(line)
    else:
        print("(no log file)")

    print("\n--- verdict ---")
    if state and state.get("armed") and task and result.get("followup_message"):
        print("SCRIPT OK: followup would be injected on stop Hook.")
        print("If chat shows nothing: Cursor stop Hook may not run on agent turn end.")
        print("  - Reload Window")
        print("  - Check Output > Hooks")
        print("  - Agent turn must end with status=completed")
    elif state and not state.get("armed"):
        print("armed=false: send '큐 시작' first")

    test_ps1 = ROOT / ".cursor" / "hooks" / "test_task_queue_continue.ps1"
    if test_ps1.is_file():
        print("\n--- test_task_queue_continue.ps1 ---")
        r = subprocess.run(
            [
                "powershell",
                "-NoProfile",
                "-ExecutionPolicy",
                "Bypass",
                "-File",
                str(test_ps1),
            ],
            cwd=str(ROOT),
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
        for line in (r.stdout or "").strip().splitlines()[-3:]:
            print(line)
        if r.returncode != 0:
            print(r.stderr or "")
            return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
