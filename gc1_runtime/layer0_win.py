# -*- coding: utf-8 -*-
"""
L0-WIN 프로브 (Ω.A.L0.WIN.01~07) — Autochro 메인 창 탐색·점수·rect.

``gc_autochro.connect_main_window`` 의 find/score 로직을 leaf 단위로 분리 (T30).
pywinauto 는 **호출부·connect_fn** 에서만 — 본 모듈은 mock 테스트 가능한 순수 함수 위주.
"""

from __future__ import annotations

import re
import sys
from dataclasses import dataclass
from typing import Any, Callable, Sequence

ConnectFn = Callable[[int], Any]
FindWindowsFn = Callable[..., Sequence[int]]


@dataclass(frozen=True)
class WindowRect:
    """Ω.A.L0.WIN.06 — ``rectangle()`` 결과."""

    left: int
    top: int
    right: int
    bottom: int

    @property
    def width(self) -> int:
        return self.right - self.left

    @property
    def height(self) -> int:
        return self.bottom - self.top

    @classmethod
    def from_obj(cls, rect: Any) -> WindowRect:
        return cls(int(rect.left), int(rect.top), int(rect.right), int(rect.bottom))


@dataclass(frozen=True)
class WinProbeResult:
    """WIN.01~05 요약."""

    handles: tuple[int, ...]
    best_handle: int | None
    best_score: int
    best_window: Any | None


def build_title_re(title_pattern: str) -> str:
    """WIN.01 — ``findwindows(title_re=...)`` 용 정규식."""
    return f".*{re.escape(title_pattern)}.*"


def find_handles(
    title_pattern: str,
    *,
    find_windows: FindWindowsFn,
) -> tuple[int, ...]:
    """Ω.A.L0.WIN.01 — handle 목록 (없으면 빈 tuple)."""
    handles = find_windows(title_re=build_title_re(title_pattern))
    return tuple(int(h) for h in handles)


def count_handles(handles: Sequence[int]) -> int:
    """Ω.A.L0.WIN.02 — len(handles)."""
    return len(handles)


def score_autochro_window(win: Any) -> int:
    """
    Ω.A.L0.WIN.04a~04d — ``gc_autochro._score_autochro_window`` 와 동일 규칙.

    visible +100, area min(w*h//1000,500), tree +200, list +100.
    """
    score = 0
    try:
        if win.is_visible():
            score += 100
    except Exception:
        pass
    try:
        rect = win.rectangle()
        score += min(rect.width() * rect.height() // 1000, 500)
    except Exception:
        pass
    try:
        if win.descendants(class_name="SysTreeView32"):
            score += 200
    except Exception:
        pass
    try:
        if win.descendants(class_name="SysListView32"):
            score += 100
    except Exception:
        pass
    return score


def pick_best_window(
    handles: Sequence[int],
    *,
    connect: ConnectFn,
) -> WinProbeResult:
    """
    Ω.A.L0.WIN.03 + 05 — handle마다 connect 후 argmax score.

    connect 실패 handle 은 건너뜀 (``gc_autochro`` 와 동일).
    """
    hs = tuple(handles)
    if not hs:
        return WinProbeResult(handles=(), best_handle=None, best_score=-1, best_window=None)
    if len(hs) == 1:
        win = connect(hs[0])
        sc = score_autochro_window(win)
        return WinProbeResult(handles=hs, best_handle=hs[0], best_score=sc, best_window=win)
    best_handle: int | None = None
    best_window = None
    best_score = -1
    for handle in hs:
        try:
            candidate = connect(handle)
            sc = score_autochro_window(candidate)
            if sc > best_score:
                best_score = sc
                best_handle = handle
                best_window = candidate
        except Exception:
            continue
    return WinProbeResult(
        handles=hs,
        best_handle=best_handle,
        best_score=best_score,
        best_window=best_window,
    )


def read_window_rect(win: Any) -> WindowRect:
    """Ω.A.L0.WIN.06."""
    return WindowRect.from_obj(win.rectangle())


def is_foreground(hwnd: int, *, foreground_hwnd: int | None = None) -> bool:
    """Ω.A.L0.WIN.07 — GetForegroundWindow() == hwnd."""
    if foreground_hwnd is None:
        if sys.platform != "win32":
            return False
        foreground_hwnd = int(__import__("ctypes").windll.user32.GetForegroundWindow())
    return int(hwnd) == int(foreground_hwnd)


class WinProbe:
    """WIN 체인 편의 래퍼 — find → pick."""

    def __init__(
        self,
        *,
        find_windows: FindWindowsFn,
        connect: ConnectFn,
    ) -> None:
        self._find_windows = find_windows
        self._connect = connect

    def probe(self, title_pattern: str) -> WinProbeResult:
        handles = find_handles(title_pattern, find_windows=self._find_windows)
        return pick_best_window(handles, connect=self._connect)
