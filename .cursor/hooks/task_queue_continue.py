# -*- coding: utf-8 -*-
"""task_queue_continue.py — Cursor stop Hook #1 (이어가기 / 종결 플래그)

=============================================================================
[등록 위치]
=============================================================================
  .cursor/hooks.json → hooks.stop 배열 **안에서 git sync 등 뒤에** 등록:

    {"command": "python .cursor/hooks/task_queue_continue.py", "loop_limit": null}

  loop_limit: null → 단계가 많아도 followup 횟수 제한 없음 (기본 5회 제한 해제)

=============================================================================
[실행 시점]
=============================================================================
  에이전트 **한 턴이 끝날 때마다** Cursor가 이 스크립트를 실행.
  stdin 으로 JSON, stdout 으로 JSON 을 주고받음.

=============================================================================
[stdout 계약]
=============================================================================
  · {"followup_message": "..."}  → Cursor가 이 문자열을 **다음 사용자 메시지**로 삽입
  · {}                           → 아무 것도 안 함

=============================================================================
[에이전트가 할 일 vs Hook이 할 일]
=============================================================================
  에이전트: 코드 작업, [x] 표시, blocked 시 state 변경
  Hook:     남은 [ ] 있으면 followup / 없으면 request_quit_cursor (종료는 quit Hook)

=============================================================================
[테스트]
=============================================================================
  powershell -File .cursor/hooks/test_task_queue_continue.ps1
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

# 같은 폴더의 agent_queue_lib import
sys.path.insert(0, str(Path(__file__).resolve().parent))

from agent_queue_lib import evaluate_stop  # noqa: E402


def _out(obj: dict) -> None:
    """stdout 을 UTF-8 바이트로 출력 (Windows cp949 콘솔 깨짐 방지)."""
    data = json.dumps(obj, ensure_ascii=False)
    if hasattr(sys.stdout, "buffer"):
        sys.stdout.buffer.write(data.encode("utf-8"))
        sys.stdout.buffer.flush()
    else:
        sys.stdout.write(data)
        sys.stdout.flush()


def main() -> int:
    try:
        raw = sys.stdin.read()
        payload = json.loads(raw) if raw.strip() else {}
    except (json.JSONDecodeError, ValueError):
        _out({})
        return 0
    _out(evaluate_stop(payload))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
