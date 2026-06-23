# -*- coding: utf-8 -*-
"""
gc_request.py — 사용자 개시 요청 판별 (--user-message / --request)

=============================================================================
[역할]
=============================================================================

  연구원/Cursor가 "시작", "진행", "go" 처럼 **맥락 없이 진행을 요청**하면
  gc_automation 이 **force 모드**로 엑셀+메일을 실행해야 합니다.

  · "동작해줘" 같은 **고정 명령어 하나**가 아닙니다.
  · "코드 수정해줘", "watch 재시작" 처럼 **다른 맥락**이 섞이면 force 아님.

  force 는 --watch 규칙과 **무관**. GC1 **장비** PC force 시 Autochro PDF 포함 전체 pipeline.

  실행 위치: **장비 PC** 만 (GC1 장비 / GC2·GC3 장비). 은규 PC·차헌 PC 아님.
  PC 명칭: docs/PC_NAMING.md

  GC1 Cursor 예: python gc_automation.py --user-message "진행"
  GC1 bat 예:     Desktop\\박은규\\GC1_동작해줘.bat  (GC1 **장비** PC)

=============================================================================
[Cursor 종료 코드] (gc_automation.handle_user_message)
=============================================================================

  0 … force + 바탕화면 MMDDHHmm ±5분 OK  → Cursor 추가 작업 불필요
  1 … force 했지만 heartbeat FAIL        → watch 재시작 등 수리
  2 … 개시 문구 아님                     → 일반 Cursor 대화
"""

from __future__ import annotations

import re
from dataclasses import dataclass, replace
from typing import Optional

from gc_config import AppConfig
from gc_sanitize import InvalidSampleNameError, sanitize_sample_name

INITIATION_KEYWORDS = (
    "시작", "진행", "실행", "동작", "동작해", "작업", "처리", "처리해", "보내", "돌려", "가자",
    "해보자", "해줘", "해봐", "해", "go", "start", "run", "force",
    "proceed", "launch", "begin",
)

CONTEXT_MARKERS = (
    "sequence", "sample", "시료", "chemstation", "acam", "엑셀", "메일",
    "wifi", "와이파이", "핫스팟", "hotspot", "watch", "폴더", "folder",
    ".py", ".bat", ".txt", "gc_", "코드", "수정", "설치", "cursor", "커서",
    "리팩", "refactor", "bug", "오류", "에러", "설명", "확인해", "검토",
    "how", "why", "what",
)

OPTION_SAMPLE = re.compile(r"^sample[-_]?name\s*[=:]\s*(.+)$", re.IGNORECASE)
OPTION_DATE = re.compile(r"^sequence[-_]?date\s*[=:]\s*(\d{8})$", re.IGNORECASE)
OPTION_FOLDER = re.compile(r"^sequence[-_]?folder\s*[=:]\s*(.+)$", re.IGNORECASE)

SHORT_INITIATION_RE = re.compile(
    r"^[\s!?]*("
    r"시작|진행|실행|동작|동작해|작업|처리|처리해|보내|가자|go|start|run|force|proceed|launch|begin"
    r"|(?:동작|작업|실행|처리|보내|메일)?\s*해\s*줘?"
    r")(\s+(시작|진행|go|동작|처리))*[\s!?]*$",
    re.IGNORECASE,
)


@dataclass
class UserForceRequest:
    """--user-message 에서 파싱된 force 요청."""

    raw_text: str
    trigger_line: str
    sample_name: Optional[str] = None
    sequence_date: Optional[str] = None
    sequence_folder: Optional[str] = None


def _normalize(text: str) -> str:
    return text.strip().lower().replace(" ", "")


def has_technical_context(text: str) -> bool:
    """True → force 트리거 아님 (코드·경로·설정 등 맥락 있음)."""
    lower = text.lower()
    compact = _normalize(text)
    for marker in CONTEXT_MARKERS:
        m = marker.lower()
        if m in lower or m.replace(" ", "") in compact:
            return True
    if re.search(r"--[a-z]", lower):
        return True
    if re.search(r"[\\/:]", text):
        return True
    return False


def is_initiation_phrase(text: str) -> bool:
    """
    한 줄이 맥락 없는 개시 문구인지.

    True 예:  "시작", "진행", "go", "동작해", "처리해", "처리해 진행", "작업해줘"
    False 예: "코드 수정해줘", "설명해줘?"
    """
    stripped = text.strip()
    if not stripped or len(stripped) > 48:
        return False
    if stripped.endswith("?"):
        return False
    if has_technical_context(stripped):
        return False
    if SHORT_INITIATION_RE.match(stripped):
        return True
    compact = _normalize(stripped)
    if not compact:
        return False
    for keyword in INITIATION_KEYWORDS:
        if _normalize(keyword) in compact:
            return True
    return False


def message_is_initiation(text: str) -> bool:
    """Cursor 채팅 전체 — 개시 줄 + sample-name= 옵션 조합 허용."""
    stripped = text.strip()
    if not stripped:
        return False
    if is_initiation_phrase(stripped):
        return True

    lines = [
        line.strip()
        for line in stripped.splitlines()
        if line.strip() and not line.strip().startswith("#")
    ]
    option_lines = [
        line
        for line in lines
        if OPTION_SAMPLE.match(line) or OPTION_DATE.match(line) or OPTION_FOLDER.match(line)
    ]
    content_lines = [line for line in lines if line not in option_lines]
    if not content_lines:
        return False
    if has_technical_context("\n".join(content_lines)):
        return False
    return any(is_initiation_phrase(line) for line in content_lines)


def line_is_force_trigger(line: str) -> bool:
    return is_initiation_phrase(line)


def _parse_request_body(raw: str) -> Optional[UserForceRequest]:
    if not raw.strip():
        return None

    trigger_line = None
    sample_name = None
    sequence_date = None
    sequence_folder = None

    for line in raw.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        if line_is_force_trigger(stripped):
            trigger_line = stripped
            continue
        match = OPTION_SAMPLE.match(stripped)
        if match:
            try:
                sample_name = sanitize_sample_name(match.group(1).strip())
            except InvalidSampleNameError:
                return None
            continue
        match = OPTION_DATE.match(stripped)
        if match:
            sequence_date = match.group(1).strip()
            continue
        match = OPTION_FOLDER.match(stripped)
        if match:
            sequence_folder = match.group(1).strip()
            continue

    if not trigger_line:
        return None

    return UserForceRequest(
        raw_text=raw,
        trigger_line=trigger_line,
        sample_name=sample_name,
        sequence_date=sequence_date,
        sequence_folder=sequence_folder,
    )


def parse_message_as_request(text: str) -> Optional[UserForceRequest]:
    if not message_is_initiation(text):
        return None
    stripped = text.strip()
    trigger = stripped.splitlines()[0].strip()
    for line in stripped.splitlines():
        if is_initiation_phrase(line.strip()):
            trigger = line.strip()
            break
    parsed = _parse_request_body(stripped)
    if parsed:
        return parsed
    return UserForceRequest(raw_text=stripped, trigger_line=trigger)


def config_for_user_request(base: AppConfig, request: UserForceRequest) -> AppConfig:
    """force=True — 핫스팟·메일 쿨다운·input() 우회."""
    return replace(
        base,
        force=True,
        allow_prompt=False,
        sample_name=request.sample_name or base.sample_name,
        sequence_date=request.sequence_date or base.sequence_date,
        sequence_folder=request.sequence_folder or base.sequence_folder,
    )
