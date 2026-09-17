# -*- coding: utf-8 -*-
"""같은 Long Name 워크북이 둘 이상이면 Origin 쓰기를 막는다."""

from __future__ import annotations

from typing import Any


def _nonempty_count(vals: Any) -> int:
    n = 0
    for v in vals:
        if v is None:
            continue
        if isinstance(v, str) and not v.strip():
            continue
        if isinstance(v, float) and v != v:
            continue
        n += 1
    return n


def book_data_rows(book: Any) -> int:
    """마지막 날짜 열의 데이터 행 수. 없으면 0."""
    best = 0
    for wks in book:
        cols = int(getattr(wks, "cols", 0) or 0)
        get_label = getattr(wks, "get_label", None)
        dated = None
        if callable(get_label):
            for i in range(1, cols):
                comment = get_label(i, "C") or ""
                compact = str(comment).replace(" ", "")
                if len(compact) >= 8 and compact[:8].isdigit():
                    dated = i
        if dated is None:
            continue
        to_list = getattr(wks, "to_list", None)
        if not callable(to_list):
            continue
        try:
            vals = list(to_list(dated))
        except Exception:
            continue
        best = max(best, _nonempty_count(vals))
    return best


def duplicate_long_name_groups(op: Any) -> list[tuple[str, list[tuple[str, int]]]]:
    """Long Name 이 비어 있지 않고 같은 북이 2개 이상인 그룹.

    행 수가 같아도 자동으로 고르지 않는다. 화면에는 하나처럼 보이기 때문이다.
    반환: (long_name, [(short_name, rows), ...])
    """
    groups: dict[str, tuple[str, list[tuple[str, int]]]] = {}
    pages = getattr(op, "pages", None)
    if not callable(pages):
        return []
    for book in pages("w"):
        lname = str(getattr(book, "lname", "") or "").strip()
        if not lname:
            continue
        key = lname.lower()
        name = str(getattr(book, "name", "") or "")
        rows = book_data_rows(book)
        if key not in groups:
            groups[key] = (lname, [])
        groups[key][1].append((name, rows))
    return [item for item in groups.values() if len(item[1]) >= 2]
