# -*- coding: utf-8 -*-
"""
사용자 마우스 감지 — GC1 런 중 **학습·케이스 스터디만** 일시 중단.

실험실 진동(작은 떨림)은 무시하고, 사용자가 마우스를 **휙** 움직일 때만 중단.
자동화(Autochro 클릭)는 계속 — 은규 사용자 불편 최소화.
"""
from __future__ import annotations

import math
import sys
import threading
import time
from typing import Optional, Tuple

_GUARD: Optional["UserMouseGuard"] = None

# 한 번에 이 거리 이상 이동 → 사용자 조작
_SWIPE_SINGLE_PX = float(
    __import__("os").getenv("GC1_LEARN_MOUSE_SWIPE_PX", "55")
)
# 짧은 시간에 누적 이동 + 최대 한 번은 확실히 큰 이동
_SWIPE_WINDOW_SEC = float(
    __import__("os").getenv("GC1_LEARN_MOUSE_WINDOW_SEC", "0.35")
)
_SWIPE_WINDOW_TOTAL_PX = float(
    __import__("os").getenv("GC1_LEARN_MOUSE_WINDOW_TOTAL_PX", "180")
)
_SWIPE_WINDOW_MIN_SINGLE_PX = float(
    __import__("os").getenv("GC1_LEARN_MOUSE_WINDOW_MIN_PX", "38")
)
# 이 값 이하만 연속이면 진동으로 간주 (학습 중단 안 함)
_VIBRATION_MAX_PX = float(
    __import__("os").getenv("GC1_LEARN_VIBRATION_MAX_PX", "22")
)
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

    @property
    def paused(self) -> bool:
        return self._paused

    @property
    def pause_reason(self) -> str:
        return self._pause_reason

    def start(self) -> None:
        if sys.platform != "win32":
            return
        self.stop()
        self._paused = False
        self._pause_reason = ""
        self._last = None
        self._moves = []
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

    def _trigger(self, reason: str) -> None:
        if self._paused:
            return
        self._paused = True
        self._pause_reason = reason

    def _loop(self) -> None:
        while not self._stop.is_set():
            try:
                pos = _cursor_pos()
                now = time.time()
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


def learning_collection_allowed() -> bool:
    """케이스 스터디·overlay patch·관측 기록 허용 여부."""
    from gc1_runtime.layer3_ocr_learn import learnings_enabled

    if not learnings_enabled():
        return False
    return not is_learning_paused_by_user()
