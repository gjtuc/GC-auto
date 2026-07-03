# -*- coding: utf-8 -*-
"""
gc_tk_overlay.py — OCR 포커스 테두리 (tkinter, 메인 스레드 전용)

옵션 A: ``GC_SCREEN_FOCUS_BACKEND=tk``
백그라운드 스레드 없음 — ``stage()`` 동안만 생성·destroy (Tcl 스레드 충돌 방지).
"""
from __future__ import annotations

import sys
from typing import Optional

if sys.platform != "win32":
    raise RuntimeError("gc_tk_overlay is Windows-only (GC1)")

_tk_root = None
_outline_colors = {"red": "#FF0000", "lime": "#00FF00", "green": "#00FF00"}


def tk_overlay_hide() -> None:
    global _tk_root
    if _tk_root is not None:
        try:
            _tk_root.destroy()
        except Exception:
            pass
        _tk_root = None


def tk_overlay_show_border(
    left: int,
    top: int,
    width: int,
    height: int,
    *,
    border: int = 6,
    color: str = "red",
    pad: int = 6,
) -> None:
    """속이 빈 테두리 — magenta 배경을 투명 처리."""
    global _tk_root
    if width < 2 or height < 2:
        return

    import tkinter as tk

    tk_overlay_hide()
    pl, pt = left - pad, top - pad
    w = max(width + 2 * pad, border * 2 + 4)
    h = max(height + 2 * pad, border * 2 + 4)
    outline = _outline_colors.get(color.lower(), "#FF0000")

    root = tk.Tk()
    root.overrideredirect(True)
    root.attributes("-topmost", True)
    root.configure(bg="magenta")
    try:
        root.attributes("-transparentcolor", "magenta")
    except tk.TclError:
        pass
    root.geometry(f"{w}x{h}+{pl}+{pt}")

    canvas = tk.Canvas(root, width=w, height=h, highlightthickness=0, bg="magenta")
    canvas.pack()
    bd = max(2, border)
    canvas.create_rectangle(
        pad,
        pad,
        w - pad,
        h - pad,
        outline=outline,
        width=bd,
    )
    root.update_idletasks()
    root.update()
    _tk_root = root

