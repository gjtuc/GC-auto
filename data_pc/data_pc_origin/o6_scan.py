# -*- coding: utf-8 -*-
"""O6-S — worksheet column comment scan (촉매 L1635–1642)."""

from __future__ import annotations

from typing import Any, Iterator, List, Tuple

from data_pc_origin.o0_comments import parse_comment_date

ColComment = Tuple[int, str]


def iter_col_comments(wks: Any) -> Iterator[ColComment]:
    """`range(1, wks.cols)` — 각 열 Comments(C) 문자열."""
    cols = getattr(wks, "cols", None)
    if cols is None:
        raise AttributeError("wks.cols required")
    get_label = getattr(wks, "get_label", None)
    if get_label is None:
        raise AttributeError("wks.get_label required")
    for i in range(1, int(cols)):
        yield i, get_label(i, "C") or ""


def dated_columns(wks: Any) -> List[Tuple[int, str]]:
    """Comments 에 YYYYMMDD 가 있는 열만 — 왼쪽→오른쪽 (촉매 _worksheet_dated_columns)."""
    dated: List[Tuple[int, str]] = []
    for i, comment in iter_col_comments(wks):
        sort_date = parse_comment_date(comment)
        if sort_date:
            dated.append((i, sort_date))
    return dated


def comment_at_column(wks: Any, col_idx: int) -> str:
    """단일 열 Comments(C) — O6 장비·날짜 가드용."""
    get_label = getattr(wks, "get_label", None)
    if get_label is None:
        raise AttributeError("wks.get_label required")
    return get_label(int(col_idx), "C") or ""
