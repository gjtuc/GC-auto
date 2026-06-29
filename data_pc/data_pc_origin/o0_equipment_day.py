# -*- coding: utf-8 -*-
"""O0 — 같은 장비·날짜 실험 제한 (Origin 열 추가 전 검사, originpro 불필요).

규칙 (연구실):
  · 동일 장비(GC2/_DRM, GC3/_OCM)에서는 하루에 실험 2회 불가.
  · 새 열을 추가할 때 **바로 왼쪽 열** Comments 와 비교.
  · 동일 장비 + (같은 날짜 OR 왼쪽 날짜가 더 최근) → 사용자 확인 필요.
  · 기존 열 갱신(exact/identity match)은 사용자 수동 수정 가능 → 이 모듈 미적용.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from data_pc_origin.o0_comments import parse_comment_date, parse_equipment_suffix


@dataclass(frozen=True)
class EquipmentDayGuardResult:
    """왼쪽 이웃 열 대비 새 시료명 검사 결과."""

    needs_user_confirm: bool
    reason_code: str
    question: str
    left_comment: str
    new_sample_name: str
    equipment: Optional[str] = None
    left_date: Optional[str] = None
    new_date: Optional[str] = None


def evaluate_equipment_day_guard(
    left_comment: str | None,
    new_sample_name: str,
) -> EquipmentDayGuardResult:
    """
    새 Origin 열 삽입 직전 — 왼쪽 열 Comments 와 새 sample_name 비교.

    Returns:
        needs_user_confirm True 이면 Origin 기록 전 사용자 확인 필수.
    """
    left = (left_comment or "").strip()
    new = (new_sample_name or "").strip()
    base = EquipmentDayGuardResult(
        needs_user_confirm=False,
        reason_code="",
        question="",
        left_comment=left,
        new_sample_name=new,
    )
    if not left or not new:
        return base

    left_eq = parse_equipment_suffix(left)
    new_eq = parse_equipment_suffix(new)
    if not left_eq or not new_eq or left_eq != new_eq:
        return base

    left_date = parse_comment_date(left)
    new_date = parse_comment_date(new)
    if not left_date or not new_date:
        return base

    issues: list[str] = []
    if left_date == new_date:
        issues.append(
            f"같은 장비({left_eq})에서 같은 날짜({left_date}) 실험이 "
            f"왼쪽 열에 이미 있습니다. 하루 2회 실험은 불가합니다."
        )
    elif left_date > new_date:
        issues.append(
            f"왼쪽 열 날짜({left_date})가 새 시료({new_date})보다 최근입니다. "
            f"날짜순 정렬이 어긋나거나 수동 수정·중복 실험일 수 있습니다."
        )

    if not issues:
        return EquipmentDayGuardResult(
            needs_user_confirm=False,
            reason_code="ok",
            question="",
            left_comment=left,
            new_sample_name=new,
            equipment=left_eq,
            left_date=left_date,
            new_date=new_date,
        )

    question = (
        "Origin 열 추가 전 확인이 필요합니다:\n"
        + "\n".join(f"- {line}" for line in issues)
        + f"\n\n  왼쪽 Comments: {left}\n  추가 예정: {new}\n"
        + "  (기존 열 수정이면 파이프라인이 identity 로 찾아야 합니다. 새 열이 맞는지 확인하세요.)"
    )
    code = "same_date" if left_date == new_date else "left_date_ahead"
    return EquipmentDayGuardResult(
        needs_user_confirm=True,
        reason_code=code,
        question=question,
        left_comment=left,
        new_sample_name=new,
        equipment=left_eq,
        left_date=left_date,
        new_date=new_date,
    )
