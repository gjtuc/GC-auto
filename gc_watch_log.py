# -*- coding: utf-8 -*-
"""
gc_watch_log.py — GC Watch 창용 활동 로그 (watch 숨김 프로세스 → watchdog 콘솔)

watch 는 CREATE_NO_WINDOW 로 실행되어 print 가 GC Watch 창에 안 보입니다.
[tag] HH:mm:ss message 형식으로 파일에 기록하고, gc_watchdog 이 tail 합니다.
"""

from __future__ import annotations

import os
from datetime import datetime

from gc_config import default_watch_status_json


def watch_activity_log_path() -> str:
    """Desktop\\KCH\\.gc_watch_activity.log (status JSON 과 같은 폴더)."""
    return os.path.join(os.path.dirname(default_watch_status_json()), ".gc_watch_activity.log")


def watch_log(tag: str, message: str) -> None:
    """GC Watch 창에 표시될 한 줄 — [tag] HH:mm:ss message."""
    line = f"[{tag}] {datetime.now().strftime('%H:%M:%S')} {message}"
    _append_line(line)


def watch_log_raw(message: str) -> None:
    """이미 포맷된 줄 (watchdog 과 동일 형식)."""
    _append_line(message)


def watch_emit(tag: str, message: str) -> None:
    """수동 실행 콘솔 + GC Watch 창 동시 기록."""
    line = f"[{tag}] {datetime.now().strftime('%H:%M:%S')} {message}"
    _append_line(line)
    print(line)


def _append_line(line: str) -> None:
    path = watch_activity_log_path()
    try:
        os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
        with open(path, "a", encoding="utf-8") as f:
            f.write(line + "\n")
    except OSError:
        pass
