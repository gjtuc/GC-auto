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
from ctypes import wintypes
from typing import Optional

if sys.platform != "win32":
    raise RuntimeError("gc_win32_overlay is Windows-only (GC1)")

user32 = ctypes.windll.user32
gdi32 = ctypes.windll.gdi32
kernel32 = ctypes.windll.kernel32

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
    ctypes.c_longlong if ctypes.sizeof(ctypes.c_void_p) == 8 else ctypes.c_long,
    wintypes.HWND,
    wintypes.UINT,
    wintypes.WPARAM,
    wintypes.LPARAM,
)

_CLASS_NAME = "GCFocusOverlayLayer2026"
_class_atom: Optional[int] = None
_hwnd: Optional[int] = None


def _ensure_class() -> None:
    global _class_atom
    if _class_atom is not None:
        return

    @_WNDPROC
    def _proc(hwnd, msg, wparam, lparam):
        return user32.DefWindowProcW(hwnd, msg, wparam, lparam)

    wc = wintypes.WNDCLASSW()
    wc.lpfnWndProc = _proc
    wc.hInstance = kernel32.GetModuleHandleW(None)
    wc.lpszClassName = _CLASS_NAME
    wc.hbrBackground = gdi32.GetStockObject(0)  # NULL_BRUSH
    _class_atom = user32.RegisterClassW(ctypes.byref(wc))
    if not _class_atom:
        raise OSError("RegisterClassW failed for focus overlay")


def _border_bgra(width: int, height: int, border: int, rgb: tuple[int, int, int]) -> array.array:
    """32bpp BGRA — 테두리만 alpha=255."""
    r, g, b = rgb
    buf = array.array("B", [0] * (width * height * 4))
    bd = max(1, min(border, min(width, height) // 2))
    for y in range(height):
        for x in range(width):
            if x < bd or x >= width - bd or y < bd or y >= height - bd:
                i = (y * width + x) * 4
                buf[i] = b
                buf[i + 1] = g
                buf[i + 2] = r
                buf[i + 3] = 255
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
        pt_dst = _POINT(0, 0)
        blend = _BLENDFUNCTION(AC_SRC_OVER, 0, 255, AC_SRC_ALPHA)

        if not user32.UpdateLayeredWindow(
            hwnd,
            hdc_screen,
            ctypes.byref(pt_dst),
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
    border: int = 3,
    color: str = "red",
    pad: int = 0,
) -> None:
    """화면 좌표에 속이 빈 테두리 창 (클릭 통과)."""
    global _hwnd
    if width < 2 or height < 2:
        return

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

    pixels = _border_bgra(w, h, border, rgb)
    _update_layered(hwnd, w, h, pixels)
    user32.ShowWindow(hwnd, 5)  # SW_SHOW
    user32.UpdateWindow(hwnd)
    _hwnd = hwnd
