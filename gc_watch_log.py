# -*- coding: utf-8 -*-
"""
gc_watch_log.py — GC Watch 창용 활동 로그 (watch 숨김 프로세스 → watchdog 콘솔)

watch 는 CREATE_NO_WINDOW 로 실행되어 print 가 GC Watch 창에 안 보입니다.
install_watch_console_tee() 가 stdout 을 활동 로그에 그대로 복사하고,
gc_watchdog 이 tail 해서 GC2 와 동일한 [안내]/[진행]/[대기] 형식을 표시합니다.
"""

from __future__ import annotations

import os
import sys

from gc_config import default_watch_status_json


def watch_activity_log_path() -> str:
    """Desktop\\KCH\\.gc_watch_activity.log (status JSON 과 같은 폴더)."""
    return os.path.join(os.path.dirname(default_watch_status_json()), ".gc_watch_activity.log")


def watch_log_raw(message: str) -> None:
    """이미 포맷된 줄 (watchdog 과 동일 형식)."""
    _append_line(message)


def install_watch_console_tee() -> None:
    """Hidden watch 의 print → 활동 로그 (GC2 검은창 메시지 형식 유지)."""
    if getattr(sys.stdout, "_gc_watch_tee", False):
        return

    class _WatchTee:
        _gc_watch_tee = True

        def __init__(self, underlying):
            self._underlying = underlying
            self._buffer = ""

        def write(self, s: str) -> int:
            if not s:
                return 0
            if not isinstance(s, str):
                s = str(s)
            self._buffer += s
            while "\n" in self._buffer:
                line, self._buffer = self._buffer.split("\n", 1)
                stripped = line.rstrip("\r")
                if stripped:
                    watch_log_raw(stripped)
            try:
                return self._underlying.write(s)
            except (OSError, ValueError):
                return len(s)

        def flush(self) -> None:
            if self._buffer:
                stripped = self._buffer.rstrip("\r")
                if stripped:
                    watch_log_raw(stripped)
                self._buffer = ""
            try:
                self._underlying.flush()
            except OSError:
                pass

        def isatty(self) -> bool:
            try:
                return self._underlying.isatty()
            except OSError:
                return False

        @property
        def encoding(self):
            return getattr(self._underlying, "encoding", "utf-8")

        @property
        def errors(self):
            return getattr(self._underlying, "errors", "replace")

    sys.stdout = _WatchTee(sys.stdout)
    sys.stderr = _WatchTee(sys.stderr)


def _append_line(line: str) -> None:
    path = watch_activity_log_path()
    try:
        os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
        with open(path, "a", encoding="utf-8") as f:
            f.write(line + "\n")
    except OSError:
        pass
