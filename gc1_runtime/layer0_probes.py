# -*- coding: utf-8 -*-
"""
B-HOST 프로브 (Ω.A.B.HOST.*) — 환경 **읽기만**, UI·상태 파일 쓰기 없음.

T21 범위:
  HOST.01  sys.platform
  HOST.02  platform.architecture()[0] → 32bit / 64bit
  HOST.06  SM_CXSCREEN / SM_CYSCREEN
  HOST.07  GetDpiForWindow(hwnd) 또는 96
  HOST.08  profile_key = ``{w}x{h}@{dpi}`` (screen_regions용)

HOST.03~05 (tasklist, hancom windows, foreground) 는 T30+ 에서 추가.
"""

from __future__ import annotations

import platform
import sys
from dataclasses import dataclass
from typing import Callable

# Win32 API 상수 (설계 §B-HOST.06)
_SM_CXSCREEN = 0
_SM_CYSCREEN = 1
_DEFAULT_DPI = 96


@dataclass(frozen=True)
class DisplayMetrics:
    """Ω.A.B.HOST.06~08 — 주 모니터 해상도·DPI·프로필 키."""

    width: int
    height: int
    dpi: int

    @property
    def profile_key(self) -> str:
        """Ω.A.B.HOST.08 — gc_screen_read display_profile 조회 키."""
        return f"{self.width}x{self.height}@{self.dpi}"


def read_platform() -> str:
    """Ω.A.B.HOST.01.PURE.platform — ``sys.platform`` 그대로."""
    return sys.platform


def read_python_bitness() -> str:
    """Ω.A.B.HOST.02.PURE.arch — ``32bit`` / ``64bit`` (설계 표기와 동일)."""
    arch, _bits = platform.architecture()
    if arch not in ("32bit", "64bit"):
        # 일부 환경에서 '' 반환 시 machine 기반 추정
        machine = platform.machine().lower()
        if machine.endswith("64") or machine in ("amd64", "x86_64", "arm64"):
            return "64bit"
        return "32bit"
    return arch


def _win32_display_metrics(hwnd: int | None) -> DisplayMetrics:
    """Windows 전용 — ctypes, 실패 시 0×0·96 (호출부에서 검증)."""
    if sys.platform != "win32":
        return DisplayMetrics(0, 0, _DEFAULT_DPI)
    user32 = __import__("ctypes").windll.user32  # noqa: PLC0415 — win32 only
    width = int(user32.GetSystemMetrics(_SM_CXSCREEN))
    height = int(user32.GetSystemMetrics(_SM_CYSCREEN))
    dpi = _DEFAULT_DPI
    if hwnd:
        try:
            got = int(user32.GetDpiForWindow(hwnd))
            if got > 0:
                dpi = got
        except (AttributeError, OSError, ValueError):
            pass
    return DisplayMetrics(width=width, height=height, dpi=dpi)


class HostProbe:
    """B-HOST leaf 묶음 — 테스트 시 ``metrics_reader`` 주입."""

    def __init__(
        self,
        *,
        metrics_reader: Callable[[int | None], DisplayMetrics] | None = None,
    ) -> None:
        self._metrics_reader = metrics_reader or _win32_display_metrics

    def platform(self) -> str:
        return read_platform()

    def python_bitness(self) -> str:
        return read_python_bitness()

    def display_metrics(self, hwnd: int | None = None) -> DisplayMetrics:
        """Ω.A.B.HOST.06~08 — 주 모니터 메트릭 (hwnd 있으면 DPI 조회 시도)."""
        return self._metrics_reader(hwnd)


def build_profile_key(width: int, height: int, dpi: int) -> str:
    """HOST.08 순수 함수 — DisplayMetrics 와 동일 규칙."""
    return DisplayMetrics(width=width, height=height, dpi=dpi).profile_key
