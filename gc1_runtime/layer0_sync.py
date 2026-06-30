# -*- coding: utf-8 -*-
"""
gc1_runtime.layer0_sync — 제어목록→분석목록 동기화 (P1) 순수 규칙 (T95)

Autochro 운영 맥락 (실장비):
  · 제어목록 하단 표 **고정 좌표** 더블클릭 → 분석목록으로 주입 데이터 복사
  · ``1.raw`` **텍스트**를 찾는 것이 아님 — 주입이 쌓이면 1.raw 는 위로 스크롤되어
    화면에서 사라지지만 **같은 클릭 위치**를 씀
  · 복사 내용: 완료된 주입 + 진행 중 주입의 **현재까지** 구간 (예: 4.raw 분석 중)

설계: ``deploy/GC1_RUNTIME_DESIGN_PART2_L4_P0_P4.md`` §P1.05~P1.11
구현 좌표: ``gc_autochro.step_sync_control_to_analysis`` 와 동일
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


def sync_double_click_coords(width: int, height: int) -> tuple[int, int]:
    """
    제어목록 SysListView32 내부 더블클릭 상대 좌표 (P1.05 + P1.06).

    ``1.raw`` 라벨이 아니라 **표 안 고정 위치** — 스크롤로 라벨이 바뀌어도 동일 좌표.
    """
    rel_y = max(12, height - 24)
    rel_x = max(20, width // 4)
    return rel_x, rel_y


def verify_analysis_list_populated(item_count: int, *, minimum: int = 1) -> bool:
    """동기화 직후 분석목록 상단 시료 표에 행이 있는지 (Ω.A.L0.SYNC.01)."""
    return int(item_count) >= int(minimum)


class SyncPostStatus(str, Enum):
    """제어목록 더블클릭 후 분석목록 상태."""

    OK = "ok"
    """분석목록 시료 표에 최소 1행 이상."""

    ANALYSIS_EMPTY = "analysis_empty"
    """제어목록에는 행이 있는데 분석목록이 비어 있음 — 동기화 실패."""

    CONTROL_EMPTY = "control_empty"
    """제어목록 자체가 비어 있음 — 아직 주입 없음."""

    BOTH_EMPTY = "both_empty"
    """양쪽 표 모두 비어 있음."""


@dataclass(frozen=True)
class SyncPostCheckResult:
    """``evaluate_sync_post_check`` 반환 — gc_autochro·probe 공용."""

    status: SyncPostStatus
    ok: bool
    control_item_count: int
    analysis_item_count: int
    operator_hint: str

    def to_dict(self) -> dict[str, object]:
        return {
            "status": self.status.value,
            "ok": self.ok,
            "control_item_count": self.control_item_count,
            "analysis_item_count": self.analysis_item_count,
            "operator_hint": self.operator_hint,
        }


def evaluate_sync_post_check(
    control_item_count: int,
    analysis_item_count: int,
    *,
    minimum_analysis_rows: int = 1,
) -> SyncPostCheckResult:
    """
    동기화 직후 제어·분석 표 행 수로 성공 여부 판정.

    control > 0 이고 analysis == 0 이면 사용자가 수동으로 더블클릭 안 한 것과
    동일한 실패 (분석목록 빈 화면).
    """
    ctrl = max(0, int(control_item_count))
    anal = max(0, int(analysis_item_count))

    if ctrl <= 0 and anal <= 0:
        return SyncPostCheckResult(
            status=SyncPostStatus.BOTH_EMPTY,
            ok=False,
            control_item_count=ctrl,
            analysis_item_count=anal,
            operator_hint="제어목록·분석목록 모두 비어 있음 - 주입 대기",
        )
    if ctrl <= 0:
        return SyncPostCheckResult(
            status=SyncPostStatus.CONTROL_EMPTY,
            ok=False,
            control_item_count=ctrl,
            analysis_item_count=anal,
            operator_hint="제어목록에 주입 없음 - GC 시퀀스 시작 대기",
        )
    if not verify_analysis_list_populated(anal, minimum=minimum_analysis_rows):
        return SyncPostCheckResult(
            status=SyncPostStatus.ANALYSIS_EMPTY,
            ok=False,
            control_item_count=ctrl,
            analysis_item_count=anal,
            operator_hint=(
                "제어목록 동기화 실패 - 제어목록 고정 위치 더블클릭 후 "
                "분석목록 시료 표가 채워져야 함"
            ),
        )
    return SyncPostCheckResult(
        status=SyncPostStatus.OK,
        ok=True,
        control_item_count=ctrl,
        analysis_item_count=anal,
        operator_hint="제어목록->분석목록 동기화 OK",
    )
