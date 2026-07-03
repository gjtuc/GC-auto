# -*- coding: utf-8 -*-
"""O6 — 장비·날짜 가드 (열 삽입 전 왼쪽 이웃 비교)."""

from __future__ import annotations

from typing import Any, Callable, Optional

from data_pc_origin.o0_equipment_day import EquipmentDayGuardResult, evaluate_equipment_day_guard
from data_pc_origin.o6_scan import comment_at_column

ColumnGuardConfirm = Callable[[EquipmentDayGuardResult], bool]


class OriginColumnGuardError(Exception):
    """사용자 확인 없이 장비·날짜 규칙 위반 가능 — Origin 기록 중단."""

    def __init__(self, guard: EquipmentDayGuardResult) -> None:
        self.guard = guard
        super().__init__(guard.question)


def left_neighbor_comment(wks: Any, insert_at: int) -> Optional[str]:
    """삽입 예정 열 바로 왼쪽(col-1) Comments — 없으면 None."""
    if insert_at <= 1:
        return None
    text = comment_at_column(wks, insert_at - 1)
    return text if (text or "").strip() else None


def enforce_equipment_day_guard(
    wks: Any,
    insert_at: int,
    sample_name: str,
    *,
    confirm: ColumnGuardConfirm | None = None,
    skip: bool = False,
) -> None:
    """
    새 열 삽입 직전 가드.

    confirm 이 None 이고 규칙 위반 → OriginColumnGuardError.
    confirm 이 False 반환 → 동일 예외.
    """
    if skip or insert_at <= 1:
        return
    left = left_neighbor_comment(wks, insert_at)
    guard = evaluate_equipment_day_guard(left, sample_name)
    if not guard.needs_user_confirm:
        return
    if confirm is None:
        raise OriginColumnGuardError(guard)
    if not confirm(guard):
        raise OriginColumnGuardError(guard)
