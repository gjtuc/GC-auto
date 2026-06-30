# -*- coding: utf-8 -*-
"""gc1_reaction_gate.py — GC1 PDF trim 후 반응 데이터 가용성 분류 (T94)

parse_gc1_pdf_path() 로 만든 Gc1PdfReport 가 엑셀·메일 단계로 갈 수 있는지 판별.
gc_pipeline.run_processing_gc1() 과 **동일한 fail_reason** 문자열을 유지한다.

환원 단계(반응 주입 전)에서는 availability=reduction_stage 로 구분해
force 실행 시 예외가 아니라 ok=False + 명시적 사유가 나가도록 한다.

관련: gc_gc1.trim_reduction_and_first_reaction, gc_pipeline.run_processing_gc1
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, Optional

from gc_gc1 import Gc1PdfReport


class Gc1ReactionAvailability(str, Enum):
    """trim 이후 파이프라인이 쓸 수 있는 데이터 종류."""

    NO_PEAKS = "no_peaks"
    """PDF 에서 FID/TCD 주입 자체를 찾지 못함."""

    REDUCTION_STAGE = "reduction_stage"
    """환원 H2 마커는 있으나 반응 시작 주입이 아직 없음 (현재 환원 중)."""

    TRIM_EMPTY = "trim_empty"
    """주입은 있으나 trim 후 비었고, 환원 마커도 없거나 기타 제외만 있음."""

    HAS_REACTION_DATA = "has_reaction_data"
    """첫 반응 주입 이후 데이터가 남아 엑셀 작성 가능."""


@dataclass(frozen=True)
class Gc1ReactionGateResult:
    """classify_gc1_report() 반환 — 정적·실행 검증 공용."""

    availability: Gc1ReactionAvailability
    can_write_excel: bool
    fail_reason: Optional[str]
    operator_hint: str
    kept_injections: int
    total_injections: int
    skipped_pre_reduction_count: int
    skipped_reduction_count: int
    skipped_transition_count: int
    skipped_first_reaction_count: int

    def to_dict(self) -> Dict[str, Any]:
        return {
            "availability": self.availability.value,
            "can_write_excel": self.can_write_excel,
            "fail_reason": self.fail_reason,
            "operator_hint": self.operator_hint,
            "kept_injections": self.kept_injections,
            "total_injections": self.total_injections,
            "skipped_pre_reduction_count": self.skipped_pre_reduction_count,
            "skipped_reduction_count": self.skipped_reduction_count,
            "skipped_transition_count": self.skipped_transition_count,
            "skipped_first_reaction_count": self.skipped_first_reaction_count,
        }


def build_trim_empty_fail_reason(report: Gc1PdfReport) -> str:
    """trim 후 사이클이 비었을 때 gc_pipeline 과 동일한 한글 메시지."""
    if report.total_injections == 0:
        return "PDF 에서 FID/TCD 피크를 찾지 못함"
    return (
        "사전노이즈·환원·전환·첫 반응 제외 후 남은 데이터 없음 "
        f"(제외: 사전노이즈 {report.skipped_pre_reduction_count}, "
        f"환원 {report.skipped_reduction_count}, "
        f"전환 {report.skipped_transition_count}, "
        f"첫 반응 {report.skipped_first_reaction_count})"
    )


def _operator_hint_for(availability: Gc1ReactionAvailability) -> str:
    if availability is Gc1ReactionAvailability.NO_PEAKS:
        return "PDF 피크 없음 - Autochro보내기·PDF 경로 확인"
    if availability is Gc1ReactionAvailability.REDUCTION_STAGE:
        return "환원 단계 - 반응 주입이 쌓이면 force/watch 가 엑셀 생성 가능"
    if availability is Gc1ReactionAvailability.TRIM_EMPTY:
        return "주입은 있으나 환원 마커·반응 데이터 없음 - trim 규칙·H2 area 확인"
    return "반응 데이터 있음 - 엑셀·메일 단계 진행 가능"


def classify_gc1_report(report: Gc1PdfReport) -> Gc1ReactionGateResult:
    """Gc1PdfReport 한 건을 반응 가용성으로 분류."""
    kept = max(len(report.fid_cycles), len(report.tcd_cycles))
    if kept > 0:
        return Gc1ReactionGateResult(
            availability=Gc1ReactionAvailability.HAS_REACTION_DATA,
            can_write_excel=True,
            fail_reason=None,
            operator_hint=_operator_hint_for(Gc1ReactionAvailability.HAS_REACTION_DATA),
            kept_injections=kept,
            total_injections=report.total_injections,
            skipped_pre_reduction_count=report.skipped_pre_reduction_count,
            skipped_reduction_count=report.skipped_reduction_count,
            skipped_transition_count=report.skipped_transition_count,
            skipped_first_reaction_count=report.skipped_first_reaction_count,
        )

    if report.total_injections == 0:
        availability = Gc1ReactionAvailability.NO_PEAKS
    elif report.skipped_reduction_count > 0:
        # trim 이 환원 구간을 본 뒤 반응 시작을 못 찾은 경우 (환원 중)
        availability = Gc1ReactionAvailability.REDUCTION_STAGE
    else:
        availability = Gc1ReactionAvailability.TRIM_EMPTY

    fail_reason = build_trim_empty_fail_reason(report)
    return Gc1ReactionGateResult(
        availability=availability,
        can_write_excel=False,
        fail_reason=fail_reason,
        operator_hint=_operator_hint_for(availability),
        kept_injections=0,
        total_injections=report.total_injections,
        skipped_pre_reduction_count=report.skipped_pre_reduction_count,
        skipped_reduction_count=report.skipped_reduction_count,
        skipped_transition_count=report.skipped_transition_count,
        skipped_first_reaction_count=report.skipped_first_reaction_count,
    )
