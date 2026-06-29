# -*- coding: utf-8 -*-
"""O6-P — column insert planning (순수, 촉매 L1668–1679)."""

from __future__ import annotations

from typing import Any, List, Optional, Sequence, Tuple

from data_pc_origin.o0_comments import parse_comment_date

DatedCol = Tuple[int, str]


def sample_sort_date(sample_name: str) -> Optional[str]:
    """시료명 선두 YYYYMMDD — O0-C-01 위임."""
    return parse_comment_date(sample_name)


def plan_insert_index(
    dated: Sequence[DatedCol],
    new_date: Optional[str],
) -> int:
    """날짜순 삽입 위치 — 맨 끝 무조건 추가 금지 (촉매 insert_at)."""
    if not new_date:
        return dated[-1][0] + 1 if dated else 1
    for col_idx, sort_date in dated:
        if new_date < sort_date:
            return col_idx
    return dated[-1][0] + 1 if dated else 1


def column_comment_nonempty(wks: Any, col_idx: int) -> bool:
    """O6-P-04 — insert_at Comments 비어 있지 않으면 True."""
    get_label = getattr(wks, "get_label", None)
    if get_label is None:
        raise AttributeError("wks.get_label required")
    return bool((get_label(col_idx, "C") or "").strip())


def needs_column_insert(wks: Any, insert_at: int) -> bool:
    """삽입 위치가 기존 열을 덮으면 LT insert 필요 (촉매 L1681)."""
    cols = getattr(wks, "cols", None)
    if cols is None:
        raise AttributeError("wks.cols required")
    return insert_at < int(cols) and column_comment_nonempty(wks, insert_at)
