# -*- coding: utf-8 -*-
"""같은 Long Name 워크북의 행 수가 다르면 Origin 쓰기를 막는다.

행 수가 같으면 막지 않는다. 북시트는 둘 다 남기고, 쓰기는 pages('w') 양쪽에 한다.
그래프 pages('g') 는 여기 대상이 아니다.
"""

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

    워크북만 본다. 그래프는 ``pages('g')`` 라서 여기 오지 않는다.
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


def row_count_conflict_groups(op: Any) -> list[tuple[str, list[tuple[str, int]]]]:
    """같은 Long Name 인데 데이터 행 수가 다른 북만.

    114행과 114행은 정상이다. 각 북의 그래프가 따로 있으므로 하나를 고르지 않고
    양쪽 북시트에 쓴다. 140행과 114행처럼 행 수가 다르면 어느 쪽이 맞는
    데이터인지 알 수 없어 쓰기를 멈춘다.
    """
    conflicts: list[tuple[str, list[tuple[str, int]]]] = []
    for lname, books in duplicate_long_name_groups(op):
        counts = {rows for _name, rows in books}
        if len(counts) > 1:
            conflicts.append((lname, books))
    return conflicts
