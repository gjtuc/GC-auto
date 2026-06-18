# -*- coding: utf-8 -*-
"""
data_pc_request.py — 은규 PC / 차헌 PC 개시 요청 판별

=============================================================================
[LLM/에이전트 참고]
=============================================================================

  **데이터 PC** (은규 PC · 차헌 PC) 전용. **장비 PC gc_automation.py 와 별개.**

  은규 사용자는 일상적으로 맥락 없는 짧은 말만 함:
    "시작", "진행", "해봐", "작업", "돌려", "go" …

  Cursor 에이전트는 이를 **작업 시작**으로 해석하고 즉시 실행:
    python "%USERPROFILE%\\gc-data-pc\\촉매 반응 계산.py"   (은규 PC)
    python "%USERPROFILE%\\Desktop\\.cursor\\촉매 반응 계산.py" (차헌 PC)

  파이프라인: 메일(IMAP) → 수율/전환율 계산 → 실험 폴더 → Origin

  판별 로직은 장비 PC `gc_request.py` 와 **동일 키워드** (연구실 통일).
  장비 PC force: gc_automation.py — **은규 PC에서 실행 금지**

  Cursor 규칙: `.cursor/rules/eungyu-pc-initiation.mdc`

=============================================================================
[사용 예]
=============================================================================

  python -c "from data_pc_request import message_is_initiation as m; print(m('진행'))"
  → True

  python -c "from data_pc_request import message_is_initiation as m; print(m('코드 수정해줘'))"
  → False
"""

from __future__ import annotations

import re

# gc_request.INITIATION_KEYWORDS 와 동기화 (장비·데이터 PC 개시 문구 통일)
INITIATION_KEYWORDS = (
    "시작", "진행", "실행", "동작", "동작해", "작업", "처리", "처리해", "보내", "돌려", "가자",
    "해보자", "해줘", "해봐", "해", "go", "start", "run", "force",
    "proceed", "launch", "begin",
)

# 기술 맥락이 섞이면 개시 아님 (질문·설정·코드 작업)
CONTEXT_MARKERS = (
    "sequence", "sample", "시료", "chemstation", "acam", "엑셀", "메일",
    "wifi", "와이파이", "핫스팟", "hotspot", "watch", "폴더", "folder",
    ".py", ".bat", ".txt", "gc_", "코드", "수정", "설치", "cursor", "커서",
    "리팩", "refactor", "bug", "오류", "에러", "설명", "확인해", "검토",
    "how", "why", "what", "깃", "git", "github", "clone", "push", "pull",
    "경로", "설정", "env", "originpro",
)

SHORT_INITIATION_RE = re.compile(
    r"^[\s!?]*("
    r"시작|진행|실행|동작|동작해|작업|처리|처리해|보내|가자|go|start|run|force|proceed|launch|begin"
    r"|(?:동작|작업|실행|처리|보내|메일)?\s*해\s*줘?"
    r")(\s+(시작|진행|go|동작|처리))*[\s!?]*$",
    re.IGNORECASE,
)


def _normalize(text: str) -> str:
    return text.strip().lower().replace(" ", "")


def has_technical_context(text: str) -> bool:
    """[LLM] True → 개시 트리거 아님 (코드·경로·설정·질문 맥락)."""
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
    [LLM] 한 줄이 맥락 없는 **작업 시작** 문구인지.

    True 예:  "시작", "진행", "해봐", "작업", "돌려", "go"
    False 예: "코드 수정해줘", "경로 알려줘?", "깃허브 push 해줘"
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
    """[LLM] Cursor 채팅 전체 메시지 — 개시 요청이면 True."""
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
    if not lines:
        return False
    if has_technical_context("\n".join(lines)):
        return False
    return any(is_initiation_phrase(line) for line in lines)


def default_script_path_eungyu() -> str:
    """[LLM] 은규 PC 기본 운영 스크립트 절대경로 (gc-data-pc)."""
    import os
    return os.path.join(os.path.expanduser("~"), "gc-data-pc", "촉매 반응 계산.py")


def default_script_path_chaheon() -> str:
    """[LLM] 차헌 PC 기본 운영 스크립트 절대경로 (Desktop\\.cursor)."""
    import os
    return os.path.join(os.path.expanduser("~"), "Desktop", ".cursor", "촉매 반응 계산.py")


def resolve_data_pc_script() -> str:
    """
    [LLM] 이 PC에서 실행할 촉매 반응 계산.py 경로.
    gc-data-pc (은규) 우선, 없으면 Desktop\\.cursor (차헌).
    """
    import os
    eungyu = default_script_path_eungyu()
    if os.path.isfile(eungyu):
        return eungyu
    chaheon = default_script_path_chaheon()
    if os.path.isfile(chaheon):
        return chaheon
    return eungyu
