# -*- coding: utf-8 -*-
"""Windows 콘솔 한글 출력 — WriteConsoleW 로 코드페이지 우회."""

from __future__ import annotations

import sys


class _WindowsConsoleTextIO:
    """Unicode 문자열을 WriteConsoleW 로 직접 출력 (CP949/UTF-8 깨짐 방지)."""

    encoding = "utf-8"
    errors = "replace"

    def __init__(self, std_handle: int, fallback, name: str):
        import ctypes

        self._kernel32 = ctypes.windll.kernel32
        self._handle = self._kernel32.GetStdHandle(std_handle)
        self._fallback = fallback
        self.name = name

    def write(self, s: str) -> int:
        if not s:
            return 0
        if not isinstance(s, str):
            s = str(s)
        try:
            import ctypes

            if self._handle in (0, None):
                return self._fallback.write(s)
            written = ctypes.c_ulong(0)
            ok = self._kernel32.WriteConsoleW(
                self._handle,
                s,
                len(s),
                ctypes.byref(written),
                None,
            )
            if ok:
                return len(s)
        except (AttributeError, OSError, ValueError):
            pass
        try:
            return self._fallback.write(s)
        except UnicodeEncodeError:
            enc = getattr(self._fallback, "encoding", None) or "cp949"
            return self._fallback.buffer.write(s.encode(enc, errors="replace"))

    def flush(self) -> None:
        try:
            self._fallback.flush()
        except OSError:
            pass

    def isatty(self) -> bool:
        try:
            return self._fallback.isatty()
        except OSError:
            return False


def setup_console_encoding() -> None:
    """까만 cmd 창 한글 — WriteConsoleW 사용."""
    if sys.platform != "win32":
        return

    if getattr(sys.stdout, "_gc_console_wrapped", False):
        return

    try:
        import ctypes

        kernel32 = ctypes.windll.kernel32
        kernel32.SetConsoleOutputCP(949)
        kernel32.SetConsoleCP(949)
    except (AttributeError, OSError):
        pass

    stdout = _WindowsConsoleTextIO(-11, sys.__stdout__, "stdout")
    stderr = _WindowsConsoleTextIO(-12, sys.__stderr__, "stderr")
    stdout._gc_console_wrapped = True
    stderr._gc_console_wrapped = True
    sys.stdout = stdout
    sys.stderr = stderr
