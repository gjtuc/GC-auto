# -*- coding: utf-8 -*-
"""O6-I — worksheet column LT insert (촉매 L1644–1649)."""

from __future__ import annotations

from typing import Any, Callable, Optional

LtExecute = Callable[[str], None]


def build_insert_lt_command(wks: Any, col_idx: int) -> str:
    """촉매 `_insert_worksheet_column_before` LT 문자열 (byte-equal)."""
    lt_col = col_idx + 1
    lt_range = getattr(wks, "lt_range", None)
    if lt_range is None:
        raise AttributeError("wks.lt_range required")
    rng = lt_range()
    return f"page.xlcolname=0; {rng}.col={lt_col}; {rng}.insert(GCData);"


def insert_column_before(
    wks: Any,
    col_idx: int,
    *,
    lt_execute: Optional[LtExecute] = None,
) -> str:
    """0-based Origin col_idx 앞에 빈 열 삽입 — LT_execute 위임."""
    cmd = build_insert_lt_command(wks, col_idx)
    if lt_execute is None:
        from originpro.config import po

        lt_execute = po.LT_execute
    lt_execute(cmd)
    return cmd


def insert_column_if_needed(
    wks: Any,
    insert_at: int,
    *,
    lt_execute: Optional[LtExecute] = None,
) -> Optional[str]:
    """O6-P occupied → I-01 (촉매 L1681–1682)."""
    from data_pc_origin.o6_plan import needs_column_insert

    if needs_column_insert(wks, insert_at):
        return insert_column_before(wks, insert_at, lt_execute=lt_execute)
    return None
