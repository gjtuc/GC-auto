# -*- coding: utf-8 -*-
"""
사용자 마우스 감지 — GC1 런 중 **학습·케이스 스터디만** 일시 중단.

실험실 진동(작은 떨림)은 무시하고, 사용자가 마우스를 **휙** 움직일 때만 중단.
**자동화(OCR·pywinauto) 커서 이동은 제외** — notify_automation_cursor_at() 으로 표시.

환경 변수 (기본값은 자동화 오탐 방지에 맞춤):
  GC1_LEARN_MOUSE_SWIPE_PX          한 번에 이상(px) — 기본 140
  GC1_LEARN_MOUSE_WINDOW_SEC        누적 창(초) — 기본 0.30
  GC1_LEARN_MOUSE_WINDOW_TOTAL_PX   창 안 누적 이동 — 기본 420
  GC1_LEARN_MOUSE_WINDOW_MIN_PX     창 안 최대 1회 이동 — 기본 100
  GC1_LEARN_VIBRATION_MAX_PX        진동 무시 상한 — 기본 25
  GC1_LEARN_AUTOMATION_GRACE_SEC    자동화 직후 무시(초) — 기본 1.0
"""
from __future__ import annotations

import math
import os
import sys
import threading
import time
from typing import Optional, Tuple

_GUARD: Optional["UserMouseGuard"] = None

# 사용자가 **의도적으로** 휙 움직일 때만 (자동화 점프보다 크게)
_SWIPE_SINGLE_PX = float(os.getenv("GC1_LEARN_MOUSE_SWIPE_PX", "140"))
_SWIPE_WINDOW_SEC = float(os.getenv("GC1_LEARN_MOUSE_WINDOW_SEC", "0.30"))
_SWIPE_WINDOW_TOTAL_PX = float(os.getenv("GC1_LEARN_MOUSE_WINDOW_TOTAL_PX", "420"))
_SWIPE_WINDOW_MIN_SINGLE_PX = float(os.getenv("GC1_LEARN_MOUSE_WINDOW_MIN_PX", "100"))
_VIBRATION_MAX_PX = float(os.getenv("GC1_LEARN_VIBRATION_MAX_PX", "25"))
_AUTOMATION_GRACE_SEC = float(os.getenv("GC1_LEARN_AUTOMATION_GRACE_SEC", "1.0"))
_POLL_SEC = 0.05


def _cursor_pos() -> Tuple[int, int]:
    if sys.platform != "win32":
        return (0, 0)
    import ctypes

    class _POINT(ctypes.Structure):
        _fields_ = [("x", ctypes.c_long), ("y", ctypes.c_long)]

    pt = _POINT()
    ctypes.windll.user32.GetCursorPos(ctypes.byref(pt))
    return int(pt.x), int(pt.y)


class UserMouseGuard:
    def __init__(self) -> None:
        self._stop = threading.Event()
        self._thread: Optional[threading.Thread] = None
        self._paused = False
        self._pause_reason = ""
        self._last: Optional[Tuple[int, int]] = None
        self._moves: list[tuple[float, float]] = []
        self._ignore_until = 0.0

    @property
    def paused(self) -> bool:
        return self._paused

    @property
    def pause_reason(self) -> str:
        return self._pause_reason

    def on_automation_cursor(
        self, x: int, y: int, *, grace_sec: Optional[float] = None
    ) -> None:
        """자동화가 커서를 옮기기 **직전** — 이 점프는 사용자 스와이프로 보지 않음."""
        sec = _AUTOMATION_GRACE_SEC if grace_sec is None else grace_sec
        self._last = (int(x), int(y))
        self._moves.clear()
        self._ignore_until = time.time() + max(0.05, sec)

    def start(self) -> None:
        if sys.platform != "win32":
            return
        self.stop()
        self._paused = False
        self._pause_reason = ""
        self._last = None
        self._moves = []
        self._ignore_until = 0.0
        self._stop.clear()
        self._thread = threading.Thread(target=self._loop, daemon=True, name="gc1-mouse-guard")
        self._thread.start()

    def stop(self) -> None:
        self._stop.set()
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=1.0)
        self._thread = None

    def reset_pause(self) -> None:
        """새 런 시작 시."""
        self._paused = False
        self._pause_reason = ""
        self._ignore_until = 0.0

    def _trigger(self, reason: str) -> None:
        if self._paused:
            return
        self._paused = True
        self._pause_reason = reason
        try:
            from gc1_runtime.layer3_ocr_maturity import (
                invalidate_run_learning_on_contamination,
            )

            invalidate_run_learning_on_contamination(reason=reason)
        except Exception:
            pass

    def _loop(self) -> None:
        while not self._stop.is_set():
            try:
                pos = _cursor_pos()
                now = time.time()
                if now < self._ignore_until:
                    self._last = pos
                    self._stop.wait(_POLL_SEC)
                    continue
                if self._last is not None:
                    dx = pos[0] - self._last[0]
                    dy = pos[1] - self._last[1]
                    delta = math.hypot(dx, dy)
                    if delta >= _VIBRATION_MAX_PX or delta >= 8:
                        self._moves.append((now, delta))
                    cut = now - _SWIPE_WINDOW_SEC
                    self._moves = [(t, d) for t, d in self._moves if t >= cut]
                    if delta >= _SWIPE_SINGLE_PX:
                        self._trigger("single_swipe")
                    elif self._moves:
                        total = sum(d for _, d in self._moves)
                        peak = max(d for _, d in self._moves)
                        if (
                            total >= _SWIPE_WINDOW_TOTAL_PX
                            and peak >= _SWIPE_WINDOW_MIN_SINGLE_PX
                        ):
                            self._trigger("window_swipe")
                self._last = pos
            except Exception:
                pass
            self._stop.wait(_POLL_SEC)


def notify_automation_cursor_at(
    x: int, y: int, *, grace_sec: Optional[float] = None
) -> None:
    """OCR·pywinauto 가 커서를 옮기기 직전 호출."""
    if _GUARD is not None:
        _GUARD.on_automation_cursor(x, y, grace_sec=grace_sec)


def notify_automation_cursor_here(*, grace_sec: Optional[float] = None) -> None:
    """현재 커서 위치 기준 자동화 grace (클릭 직후)."""
    x, y = _cursor_pos()
    notify_automation_cursor_at(x, y, grace_sec=grace_sec)


def start_learning_guard() -> None:
    global _GUARD
    if _GUARD is None:
        _GUARD = UserMouseGuard()
    _GUARD.reset_pause()
    _GUARD.start()


def stop_learning_guard() -> None:
    global _GUARD
    if _GUARD is not None:
        _GUARD.stop()


def is_learning_paused_by_user() -> bool:
    if _GUARD is None:
        return False
    return _GUARD.paused


def get_learning_pause_reason() -> str:
    """일시 중단 사유 — ``single_swipe`` / ``window_swipe`` / 빈 문자열."""
    if _GUARD is None or not _GUARD.paused:
        return ""
    return _GUARD.pause_reason or "unknown"


def learning_collection_allowed() -> bool:
    """케이스 스터디·overlay patch·관측 기록 허용 여부."""
    from gc1_runtime.layer3_ocr_learn import learnings_enabled

    if not learnings_enabled():
        return False
    return not is_learning_paused_by_user()
