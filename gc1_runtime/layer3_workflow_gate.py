# -*- coding: utf-8 -*-
"""
워크플로 vs OCR/UI 실패 구분 — 다음 단계를 모를 때만 사용자에게 질문.

OCR·마우스·키보드 조작 문제 → 케이스 스터디·학습으로 자체 해결.
업무 순서·파일·실험 맥락 불명 → 사용자에게 질문.
"""
from __future__ import annotations

import re
from typing import Optional, Tuple

# OCR/UI — 에이전트가 스스로 탐색·학습
_OCR_UI_MARKERS = (
    "ocr",
    "gate fail",
    "anchor",
    "menu missing",
    "menu ocr",
    "tesseract",
    "sync",
    "listview",
    "ctrl+a",
    "더블클릭",
    "우클릭",
    "컨텍스트 메뉴",
    "토큰",
    "영역",
    "캡처",
)

# 워크플로 — 사용자 확인 필요
_WORKFLOW_ASK_MARKERS = (
    "mtd",
    "분석방법",
    "파일 없음",
    "파일 대화상자 없음",
    "데이터명",
    "data_name",
    "crm",
    "어떤 시료",
    "어떤 실험",
    "순서",
    "다음에 뭘",
    "한컴",
    "pdf 저장 실패",
    "메뉴 없음:",  # pywinauto — 항목 자체가 없음 (UI 변경·업무 절차)
    "적분 대기",
    "인쇄 대화",
)


def classify_failure(message: str, *, step_id: str = "") -> str:
    """
    Returns:
        ``ocr_ui`` | ``workflow_ask`` | ``infra``
    """
    msg = (message or "").lower()
    step = (step_id or "").lower()

    if any(m in msg for m in _WORKFLOW_ASK_MARKERS):
        return "workflow_ask"
    if "메뉴 없음" in msg and "초기화+정량" in msg:
        return "workflow_ask"
    if any(m in msg for m in _OCR_UI_MARKERS):
        return "ocr_ui"
    if step.startswith("p") and "sync" in msg:
        return "ocr_ui"
    if re.search(r"(timeout|연결|handle|32-bit|access denied)", msg):
        return "infra"
    return "ocr_ui"  # 기본: 탐색·학습 시도


def user_question_if_needed(
    message: str,
    *,
    step_id: str = "",
) -> Optional[Tuple[str, str]]:
    """
    workflow_ask 일 때 (제목, 질문문) 반환. 아니면 None.

    에이전트는 이를 로그·채팅에 노출하고 사용자에게만 물어봄.
    """
    kind = classify_failure(message, step_id=step_id)
    if kind != "workflow_ask":
        return None
    title = f"단계 {step_id or '?'} — 업무 순서 확인"
    question = (
        f"Autochro 자동화 중 다음을 알 수 없습니다:\n"
        f"  {message}\n\n"
        f"OCR/클릭 문제가 아니라 **다음에 무엇을 해야 하는지** (파일·시료·메뉴 절차) "
        f"알려주시면 반영하겠습니다."
    )
    return title, question


def log_failure_disposition(message: str, *, step_id: str = "", log_fn=print) -> str:
    """실패 유형 로그 — workflow_ask 면 [사용자 확인 필요] 강조."""
    kind = classify_failure(message, step_id=step_id)
    if kind == "workflow_ask":
        pair = user_question_if_needed(message, step_id=step_id)
        log_fn("[사용자 확인 필요] OCR/조작이 아닌 업무·절차 문제입니다.")
        if pair:
            log_fn(f"[사용자 확인 필요] {pair[0]}")
            log_fn(pair[1])
    elif kind == "ocr_ui":
        log_fn("[케이스] OCR/UI 실패 — 전체화면 탐색·학습으로 극복 시도합니다.")
    else:
        log_fn(f"[인프라] 환경·연결 문제 — {message[:120]}")
    return kind
