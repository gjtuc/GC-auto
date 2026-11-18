# -*- coding: utf-8 -*-
"""Origin Project Explorer — 반응×장비 폴더 이름.

한 opju 안에 ``DRE-GC3`` / ``DRME-GC3`` 처럼 반응·장비를 나눠 둔다.
쓰기는 해당 폴더의 워크북만 대상으로 한다.
"""

from __future__ import annotations

import re
from typing import Any, Optional


_REACTION_IN_TEXT = re.compile(r"\b(DRME|DRE|DRM)\b", re.IGNORECASE)


def pe_folder_label(reaction: str | None, equipment: str | None) -> str:
    """예: DRE + GC3 → ``DRE-GC3``."""
    r = (reaction or "").strip().upper()
    e = (equipment or "").strip().upper()
    if not r or not e:
        return ""
    if r not in ("DRE", "DRME", "DRM"):
        return ""
    if not e.startswith("GC"):
        return ""
    return f"{r}-{e}"


def reaction_from_sample_name(sample_name: str | None) -> str:
    text = sample_name or ""
    m = _REACTION_IN_TEXT.search(text)
    return m.group(1).upper() if m else ""


def book_pe_path(op: Any, book: Any) -> str:
    """``op.pe.search(book.name)`` 경로. 없으면 빈 문자열."""
    name = str(getattr(book, "name", "") or "").strip()
    if not name:
        return ""
    pe = getattr(op, "pe", None)
    search = getattr(pe, "search", None) if pe is not None else None
    if not callable(search):
        # tests: book.pe_path optional stub
        return str(getattr(book, "pe_path", "") or "")
    try:
        return str(search(name) or "")
    except Exception:
        return str(getattr(book, "pe_path", "") or "")


def path_in_pe_folder(pe_path: str, pe_folder: str) -> bool:
    """경로 세그먼트에 ``DRE-GC3`` 가 있으면 True (대소문자 무시)."""
    folder = (pe_folder or "").strip()
    if not folder:
        return True
    parts = [p for p in str(pe_path or "").replace("\\", "/").split("/") if p]
    target = folder.casefold()
    return any(p.casefold() == target for p in parts)


def resolve_pe_folder(
    *,
    pe_folder: str | None = None,
    reaction_type: str | None = None,
    equipment: str | None = None,
    sample_name: str | None = None,
) -> str:
    """명시 pe_folder > reaction+equipment > sample_name 반응만(장비 없으면 빈 값)."""
    explicit = (pe_folder or "").strip()
    if explicit:
        return explicit
    reaction = (reaction_type or "").strip() or reaction_from_sample_name(sample_name)
    return pe_folder_label(reaction, equipment)
