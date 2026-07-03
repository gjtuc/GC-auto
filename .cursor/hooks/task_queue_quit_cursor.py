# -*- coding: utf-8 -*-
"""task_queue_quit_cursor.py — Cursor stop Hook #2 (큐 완료 시 Cursor 종료)

=============================================================================
[역할]
=============================================================================
  continue Hook 이 큐를 전부 끝냈을 때 agent_queue_state.json 에 남기는
  request_quit_cursor=true 를 **소비**하고, 실제로 Cursor 앱을 종료.

  continue Hook **바로 다음** stop 항목으로 등록할 것 (같은 턴에서 실행).

=============================================================================
[왜 continue 와 분리?]
=============================================================================
  · continue → followup_message 또는 {} + request_quit_cursor 설정
  · quit     → followup 없이 {} 만 + 백그라운드 quit_cursor_delayed.ps1

  한 스크립트에서 followup 과 quit 을 동시에 하면 Cursor 동작이 꼬일 수 있음.

=============================================================================
[안전장치]
=============================================================================
  · request_quit_cursor 는 **한 번만** 소비 후 false 로 되돌림
  · GC_AGENT_QUEUE_QUIT_CURSOR=0 이면 종료 스킵 (플래그만 해제)
  · armed=false 인 일반 세션에서는 quit Hook 도 {} 만 반환

=============================================================================
[로그]
=============================================================================
  agent_queue_stop.log (agent_queue_lib._log 경유)
  quit_cursor.log (quit_cursor_delayed.ps1)
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from agent_queue_lib import _log, load_state, save_state  # noqa: E402

HOOK_DIR = Path(__file__).resolve().parent
QUIT_SCRIPT = HOOK_DIR / "quit_cursor_delayed.ps1"


def _out(obj: dict) -> None:
    data = json.dumps(obj, ensure_ascii=False)
    if hasattr(sys.stdout, "buffer"):
        sys.stdout.buffer.write(data.encode("utf-8"))
        sys.stdout.buffer.flush()
    else:
        sys.stdout.write(data)
        sys.stdout.flush()


def _quit_enabled() -> bool:
    """환경변수로 종료 기능 끄기 — 팀/CI PC 에서 유용."""
    return os.environ.get("GC_AGENT_QUEUE_QUIT_CURSOR", "1").strip().lower() not in (
        "0",
        "false",
        "no",
        "off",
    )


def _schedule_quit() -> None:
    """Hook 본체가 끝난 뒤 2초 후 종료 — DETACHED 로 Cursor 와 분리."""
    if not QUIT_SCRIPT.is_file():
        _log("quit: script missing")
        return
    flags = 0
    if sys.platform == "win32":
        flags = subprocess.DETACHED_PROCESS | subprocess.CREATE_NEW_PROCESS_GROUP
    subprocess.Popen(
        [
            "powershell",
            "-NoProfile",
            "-ExecutionPolicy",
            "Bypass",
            "-File",
            str(QUIT_SCRIPT),
        ],
        cwd=str(HOOK_DIR.parent.parent),
        creationflags=flags,
        stdin=subprocess.DEVNULL,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        close_fds=True,
    )
    _log("quit: scheduled quit_cursor_delayed.ps1")


def main() -> int:
    try:
        raw = sys.stdin.read()
        payload = json.loads(raw) if raw.strip() else {}
    except (json.JSONDecodeError, ValueError):
        _out({})
        return 0

    if payload.get("status") != "completed":
        _out({})
        return 0

    state = load_state()
    if not state or not state.get("request_quit_cursor"):
        _out({})
        return 0

    if state.get("status") != "complete":
        _out({})
        return 0

    # 중복 종료 방지 — 플래그 먼저 해제
    state["request_quit_cursor"] = False
    save_state(state)

    if _quit_enabled():
        _schedule_quit()
        _log("quit: all tasks complete, exiting Cursor")
    else:
        _log("quit: disabled by GC_AGENT_QUEUE_QUIT_CURSOR")

    _out({})
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
