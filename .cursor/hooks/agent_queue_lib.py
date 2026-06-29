# -*- coding: utf-8 -*-
"""agent_queue_lib.py — 작업 큐 stop Hook **공통 라이브러리**

=============================================================================
[이 파일의 역할]
=============================================================================
  task_queue_continue.py / task_queue_quit_cursor.py 가 **공유**하는 로직.

  · 큐 파일(AGENT_TASK_QUEUE.md)에서 첫 번째 미완료 `- [ ]` 줄 읽기
  · 상태 파일(agent_queue_state.json) 읽기/쓰기
  · continue Hook용: followup_message 내용 조립
  · continue Hook용: 큐가 비었을 때 complete + request_quit_cursor 설정

=============================================================================
[경로 규칙]
=============================================================================
  REPO_ROOT = 이 .py 가 있는 hooks/ 의 상위 상위
              예: your-project/.cursor/hooks/agent_queue_lib.py
                  → REPO_ROOT = your-project/

  상태·큐는 항상 your-project/.cursor/ 아래 고정 경로.

=============================================================================
[상태 머신 요약]
=============================================================================
  armed=false        → Hook 무시 (일반 채팅, 큐 미개시)
  armed=true, running, [ ] 남음 → followup_message
  armed=true, running, [ ] 없음  → complete + request_quit_cursor → quit Hook
  status=blocked     → 사람 개입 필요, followup 없음

=============================================================================
[Cursor stop Hook stdin (참고)]
=============================================================================
  {"status": "completed"|"aborted"|"error", "loop_count": N}

  followup 은 status=="completed" 일 때만 처리 (aborted/error 는 이어가지 않음).

=============================================================================
[로그]
=============================================================================
  .cursor/hooks/agent_queue_stop.log — evaluate_stop() 판단 기록
"""
from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

# ---------------------------------------------------------------------------
# 경로 상수 — install.ps1 이 package/hooks/ 를 .cursor/hooks/ 에 복사하면
# REPO_ROOT 는 자동으로 «프로젝트 루트» 가 됨.
# ---------------------------------------------------------------------------
HOOK_DIR = Path(__file__).resolve().parent
REPO_ROOT = HOOK_DIR.parent.parent
STATE_PATH = REPO_ROOT / ".cursor" / "agent_queue_state.json"
QUEUE_PATH = REPO_ROOT / ".cursor" / "AGENT_TASK_QUEUE.md"
TEMPLATE_PATH = HOOK_DIR / "task_queue_followup_template.txt"
LOG_PATH = HOOK_DIR / "agent_queue_stop.log"

# 마크다운 체크박스: "- [ ] 작업 설명" (공백은 \s, x 는 소문자만 미완료)
UNCHECKED = re.compile(r"^\s*-\s*\[\s\]\s+(.+)$")


def _log(msg: str) -> None:
    """디버그·운영 로그. Hook 실패 시 agent_queue_stop.log 확인."""
    stamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    try:
        with LOG_PATH.open("a", encoding="utf-8") as fh:
            fh.write(f"[{stamp}] {msg}\n")
    except OSError:
        pass  # 로그 실패해도 Hook 자체는 fail-open


def load_state() -> dict[str, Any] | None:
    """agent_queue_state.json 읽기. utf-8-sig → PowerShell BOM 호환."""
    if not STATE_PATH.is_file():
        return None
    try:
        return json.loads(STATE_PATH.read_text(encoding="utf-8-sig"))
    except (json.JSONDecodeError, OSError):
        return None


def save_state(state: dict[str, Any]) -> None:
    """상태 파일 저장. 에이전트·Hook 양쪽에서 동일 형식 유지."""
    STATE_PATH.write_text(
        json.dumps(state, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def first_unchecked_task() -> str | None:
    """큐 파일 **위에서부터** 첫 `- [ ]` 줄의 설명 텍스트 반환. 없으면 None."""
    if not QUEUE_PATH.is_file():
        return None
    for line in QUEUE_PATH.read_text(encoding="utf-8").splitlines():
        m = UNCHECKED.match(line)
        if m:
            return m.group(1).strip()
    return None


def build_followup(task: str) -> str:
    """task_queue_followup_template.txt 의 {{TASK}} 를 현재 단계 설명으로 치환."""
    template = TEMPLATE_PATH.read_text(encoding="utf-8")
    return template.replace("{{TASK}}", task)


def evaluate_stop(payload: dict[str, Any]) -> dict[str, Any]:
    """continue Hook 핵심 판단 — stop stdin → stdout dict.

    Returns:
        {"followup_message": "..."}  다음 단계 자동 채팅 입력
        {}                           아무 것도 안 함 (종료 또는 quit Hook에 위임)
    """
    # --- 1) 이번 턴이 정상 완료가 아니면 이어가지 않음 ---
    if payload.get("status") != "completed":
        _log(f"skip: turn status={payload.get('status')}")
        return {}

    # --- 2) 큐 세션이 armed 되지 않았으면 무시 (일반 대화) ---
    state = load_state()
    if not state:
        _log("idle: no state file")
        return {}

    if not state.get("armed"):
        _log("skip: not armed")
        return {}

    if state.get("status") in ("complete", "blocked"):
        _log(f"skip: status={state.get('status')}")
        return {}

    # --- 3) 미완료 단계 있음 → followup ---
    next_task = first_unchecked_task()
    if next_task:
        _log(f"continue: {next_task[:80]}")
        return {"followup_message": build_followup(next_task)}

    # --- 4) 큐 전부 [x] → 종결 플래그만 켜고 followup 없음 ---
    # quit Hook(task_queue_quit_cursor.py)이 request_quit_cursor 를 보고 Cursor 종료
    done = {
        "armed": False,
        "status": "complete",
        "request_quit_cursor": True,
        "updated": datetime.now(timezone.utc).isoformat(),
    }
    save_state(done)
    _log("complete: queue empty, quit requested")
    return {}
