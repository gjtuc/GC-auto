# -*- coding: utf-8 -*-
"""
gc_win32_overlay.py — GC1 OCR 포커스 빨간/라임 테두리 (Win32 layered, Tcl 없음)

메인 스레드에서 동기 show/hide — tkinter 스레드 충돌 없음.
``WS_EX_TRANSPARENT`` 로 클릭은 Autochro 쪽으로 통과.
"""
from __future__ import annotations

import array
import ctypes
import sys
import time
from ctypes import wintypes
from typing import Optional

if sys.platform != "win32":
    raise RuntimeError("gc_win32_overlay is Windows-only (GC1)")

user32 = ctypes.windll.user32
gdi32 = ctypes.windll.gdi32
kernel32 = ctypes.windll.kernel32

LRESULT = ctypes.c_longlong if ctypes.sizeof(ctypes.c_void_p) == 8 else ctypes.c_long
user32.DefWindowProcW.restype = LRESULT
user32.DefWindowProcW.argtypes = [wintypes.HWND, wintypes.UINT, wintypes.WPARAM, wintypes.LPARAM]

WS_POPUP = 0x80000000
WS_EX_LAYERED = 0x00080000
WS_EX_TOPMOST = 0x00000008
WS_EX_TOOLWINDOW = 0x00000080
WS_EX_TRANSPARENT = 0x00000020

ULW_ALPHA = 0x00000002
AC_SRC_OVER = 0x00
AC_SRC_ALPHA = 0x01

_COLOR_RGB = {
    "red": (255, 0, 0),
    "lime": (0, 255, 0),
    "green": (0, 255, 0),
}


class _POINT(ctypes.Structure):
    _fields_ = [("x", ctypes.c_long), ("y", ctypes.c_long)]


class _SIZE(ctypes.Structure):
    _fields_ = [("cx", ctypes.c_long), ("cy", ctypes.c_long)]


class _BLENDFUNCTION(ctypes.Structure):
    _fields_ = [
        ("BlendOp", ctypes.c_byte),
        ("BlendFlags", ctypes.c_byte),
        ("SourceConstantAlpha", ctypes.c_byte),
        ("AlphaFormat", ctypes.c_byte),
    ]


class _BITMAPINFOHEADER(ctypes.Structure):
    _fields_ = [
        ("biSize", wintypes.DWORD),
        ("biWidth", wintypes.LONG),
        ("biHeight", wintypes.LONG),
        ("biPlanes", wintypes.WORD),
        ("biBitCount", wintypes.WORD),
        ("biCompression", wintypes.DWORD),
        ("biSizeImage", wintypes.DWORD),
        ("biXPelsPerMeter", wintypes.LONG),
        ("biYPelsPerMeter", wintypes.LONG),
        ("biClrUsed", wintypes.DWORD),
        ("biClrImportant", wintypes.DWORD),
    ]


class _BITMAPINFO(ctypes.Structure):
    _fields_ = [("bmiHeader", _BITMAPINFOHEADER), ("bmiColors", wintypes.DWORD * 3)]


_WNDPROC = ctypes.WINFUNCTYPE(
    LRESULT,
    wintypes.HWND,
    wintypes.UINT,
    wintypes.WPARAM,
    wintypes.LPARAM,
)


@_WNDPROC
def _default_wnd_proc(hwnd, msg, wparam, lparam):
    return user32.DefWindowProcW(hwnd, msg, wparam, lparam)

# Python 3.12+ ctypes.wintypes 에 WNDCLASSW 없음 — 직접 정의
class WNDCLASSW(ctypes.Structure):
    _fields_ = [
        ("style", wintypes.UINT),
        ("lpfnWndProc", _WNDPROC),
        ("cbClsExtra", ctypes.c_int),
        ("cbWndExtra", ctypes.c_int),
        ("hInstance", wintypes.HINSTANCE),
        ("hIcon", wintypes.HICON),
        ("hCursor", wintypes.HANDLE),
        ("hbrBackground", wintypes.HBRUSH),
        ("lpszMenuName", wintypes.LPCWSTR),
        ("lpszClassName", wintypes.LPCWSTR),
    ]


_CLASS_NAME = "GCFocusOverlayLayer2026"
_class_ready = False
_hwnd: Optional[int] = None

ERROR_CLASS_ALREADY_EXISTS = 1410
HWND_TOPMOST = -1
SWP_NOACTIVATE = 0x0010
SWP_SHOWWINDOW = 0x0040


class _MSG(ctypes.Structure):
    _fields_ = [
        ("hwnd", wintypes.HWND),
        ("message", wintypes.UINT),
        ("wParam", wintypes.WPARAM),
        ("lParam", wintypes.LPARAM),
        ("time", wintypes.DWORD),
        ("pt", _POINT),
    ]


def _pump_ui_brief(ms: int = 80) -> None:
    """레이어 창이 실제로 그려지도록 메시지 펌프 (OCR 블로킹 전 짧게)."""
    deadline = time.perf_counter() + max(10, ms) / 1000.0
    msg = _MSG()
    while time.perf_counter() < deadline:
        while user32.PeekMessageW(ctypes.byref(msg), None, 0, 0, 1):
            user32.TranslateMessage(ctypes.byref(msg))
            user32.DispatchMessageW(ctypes.byref(msg))
        time.sleep(0.01)


def _raise_overlay(hwnd: int, pl: int, pt: int, w: int, h: int) -> None:
    user32.SetWindowPos(
        hwnd,
        HWND_TOPMOST,
        pl,
        pt,
        w,
        h,
        SWP_NOACTIVATE | SWP_SHOWWINDOW,
    )


def _ensure_class() -> None:
    global _class_ready
    if _class_ready:
        return

    wc = WNDCLASSW()
    wc.lpfnWndProc = _default_wnd_proc
    wc.hInstance = kernel32.GetModuleHandleW(None)
    wc.lpszClassName = _CLASS_NAME
    wc.hbrBackground = gdi32.GetStockObject(0)  # NULL_BRUSH
    atom = user32.RegisterClassW(ctypes.byref(wc))
    if not atom:
        err = kernel32.GetLastError()
        if err != ERROR_CLASS_ALREADY_EXISTS:
            raise OSError(f"RegisterClassW failed for focus overlay (err={err})")
    _class_ready = True


_dpi_ready = False


def _ensure_dpi_aware() -> None:
    global _dpi_ready
    if _dpi_ready:
        return
    try:
        user32.SetProcessDPIAware()
    except Exception:
        pass
    _dpi_ready = True


def _border_bgra(
    width: int,
    height: int,
    border: int,
    rgb: tuple[int, int, int],
    *,
    fill_alpha: int = 55,
) -> array.array:
    """32bpp BGRA — 굵은 테두리 + 내부 반투명 채움 (빈 테두리만이면 잘 안 보임)."""
    r, g, b = rgb
    buf = array.array("B", [0] * (width * height * 4))
    bd = max(2, min(border, min(width, height) // 2))
    inner_a = max(0, min(120, fill_alpha))
    for y in range(height):
        for x in range(width):
            on_border = x < bd or x >= width - bd or y < bd or y >= height - bd
            if on_border:
                alpha = 255
            elif inner_a > 0:
                alpha = inner_a
            else:
                continue
            i = (y * width + x) * 4
            buf[i] = b
            buf[i + 1] = g
            buf[i + 2] = r
            buf[i + 3] = alpha
    return buf


def _update_layered(hwnd: int, width: int, height: int, pixels: array.array) -> None:
    hdc_screen = user32.GetDC(0)
    hdc_mem = gdi32.CreateCompatibleDC(hdc_screen)
    try:
        bmi = _BITMAPINFO()
        bmi.bmiHeader.biSize = ctypes.sizeof(_BITMAPINFOHEADER)
        bmi.bmiHeader.biWidth = width
        bmi.bmiHeader.biHeight = -height  # top-down
        bmi.bmiHeader.biPlanes = 1
        bmi.bmiHeader.biBitCount = 32
        bmi.bmiHeader.biCompression = 0  # BI_RGB

        bits = ctypes.c_void_p()
        hbmp = gdi32.CreateDIBSection(hdc_mem, ctypes.byref(bmi), 0, ctypes.byref(bits), None, 0)
        if not hbmp or not bits.value:
            raise OSError("CreateDIBSection failed")

        ctypes.memmove(bits.value, pixels.buffer_info()[0], len(pixels))
        old = gdi32.SelectObject(hdc_mem, hbmp)

        pt_src = _POINT(0, 0)
        size = _SIZE(width, height)
        blend = _BLENDFUNCTION(AC_SRC_OVER, 0, 255, AC_SRC_ALPHA)

        if not user32.UpdateLayeredWindow(
            hwnd,
            hdc_screen,
            None,
            ctypes.byref(size),
            hdc_mem,
            ctypes.byref(pt_src),
            0,
            ctypes.byref(blend),
            ULW_ALPHA,
        ):
            raise OSError("UpdateLayeredWindow failed")

        gdi32.SelectObject(hdc_mem, old)
        gdi32.DeleteObject(hbmp)
    finally:
        gdi32.DeleteDC(hdc_mem)
        user32.ReleaseDC(0, hdc_screen)


def overlay_hide() -> None:
    global _hwnd
    if _hwnd:
        user32.DestroyWindow(_hwnd)
        _hwnd = None


def overlay_show_border(
    left: int,
    top: int,
    width: int,
    height: int,
    *,
    border: int = 6,
    color: str = "red",
    pad: int = 0,
    fill_alpha: int = 55,
) -> None:
    """화면 좌표에 반투명 채움+테두리 창 (클릭 통과)."""
    global _hwnd
    if width < 2 or height < 2:
        return

    _ensure_dpi_aware()
    overlay_hide()
    _ensure_class()

    pl, pt = left - pad, top - pad
    w = width + 2 * pad
    h = height + 2 * pad
    w = max(w, border * 2 + 2)
    h = max(h, border * 2 + 2)

    rgb = _COLOR_RGB.get(color.lower(), _COLOR_RGB["red"])
    ex_style = WS_EX_LAYERED | WS_EX_TOPMOST | WS_EX_TOOLWINDOW | WS_EX_TRANSPARENT

    hwnd = user32.CreateWindowExW(
        ex_style,
        _CLASS_NAME,
        "",
        WS_POPUP,
        pl,
        pt,
        w,
        h,
        None,
        None,
        kernel32.GetModuleHandleW(None),
        None,
    )
    if not hwnd:
        raise OSError("CreateWindowExW failed for focus overlay")

    pixels = _border_bgra(w, h, border, rgb, fill_alpha=fill_alpha)
    _update_layered(hwnd, w, h, pixels)
    _raise_overlay(hwnd, pl, pt, w, h)
    user32.ShowWindow(hwnd, 5)  # SW_SHOW
    user32.UpdateWindow(hwnd)
    _pump_ui_brief(120)
    _hwnd = hwnd
