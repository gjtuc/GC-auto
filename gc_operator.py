# -*- coding: utf-8 -*-
"""
gc_operator.py — GC2 공유 장비: 차완 / 차헌 작업자 → 메일 수신처

GC2 한 대를 두 연구원이 사용:
  차완 → MAIL_TO_CHAWAN (기본 yangcw0103@kier.re.kr)
  차헌 → MAIL_TO_CHAHEON (기본 kimcha0809@naver.com)

활성 작업자는 Desktop\\KCH\\.gc_operator.json 에 저장.
watch / force 발송 시마다 다시 읽어 MAIL_TO 를 결정한다.
GC1 은 MAIL_TO_CHAWAN·CHAHEON 미설정 → 기존 MAIL_TO 만 사용.
"""

from __future__ import annotations

import json
import os
import re
from typing import Optional

OPERATOR_CHAWAN = "chawan"
OPERATOR_CHAHEON = "chaheon"

OPERATOR_ALIASES = {
    "차완": OPERATOR_CHAWAN,
    "chawan": OPERATOR_CHAWAN,
    "yangcw": OPERATOR_CHAWAN,
    "차헌": OPERATOR_CHAHEON,
    "chaheon": OPERATOR_CHAHEON,
    "kimcha": OPERATOR_CHAHEON,
}

DEFAULT_MAIL_BY_OPERATOR = {
    OPERATOR_CHAWAN: "yangcw0103@kier.re.kr",
    OPERATOR_CHAHEON: "kimcha0809@naver.com",
}

OPERATOR_FILE_NAME = ".gc_operator.json"

# 「차완」「차헌」만 (전환)
_OPERATOR_ONLY_RE = re.compile(
    r"^[\s!?]*("
    + "|".join(re.escape(k) for k in ("차완", "차헌", "chawan", "chaheon"))
    + r")[\s!?]*$",
    re.IGNORECASE,
)

# 문장 안 작업자 토큰
_OPERATOR_TOKEN_RE = re.compile(
    r"(?<![가-힣A-Za-z0-9_])"
    r"(차완|차헌|chawan|chaheon)"
    r"(?![가-힣A-Za-z0-9_])",
    re.IGNORECASE,
)

ASK_OPERATOR_MESSAGE = (
    "GC2 작업자를 지정해 주세요: 「차완」또는「차헌」\n"
    "  차완 → yangcw0103@kier.re.kr\n"
    "  차헌 → kimcha0809@naver.com"
)


def operator_file_path(excel_output_dir: str) -> str:
    return os.path.join(os.path.normpath(excel_output_dir), OPERATOR_FILE_NAME)


def normalize_operator(token: Optional[str]) -> Optional[str]:
    if not token:
        return None
    key = token.strip().lower().replace(" ", "")
    # 한글은 lower 영향 없음 — aliases 에 원문 키 있음
    if token.strip() in OPERATOR_ALIASES:
        return OPERATOR_ALIASES[token.strip()]
    if key in OPERATOR_ALIASES:
        return OPERATOR_ALIASES[key]
    return None


def dual_operator_mail_enabled() -> bool:
    """env 에 차완·차헌 수신 주소가 둘 다 있으면 GC2 공유 모드."""
    a = os.getenv("MAIL_TO_CHAWAN", "").strip()
    b = os.getenv("MAIL_TO_CHAHEON", "").strip()
    return bool(a and b)


def mail_for_operator(operator: str) -> str:
    op = normalize_operator(operator) or operator
    if op == OPERATOR_CHAWAN:
        return (
            os.getenv("MAIL_TO_CHAWAN", "").strip()
            or DEFAULT_MAIL_BY_OPERATOR[OPERATOR_CHAWAN]
        )
    if op == OPERATOR_CHAHEON:
        return (
            os.getenv("MAIL_TO_CHAHEON", "").strip()
            or DEFAULT_MAIL_BY_OPERATOR[OPERATOR_CHAHEON]
        )
    return ""


def load_operator(excel_output_dir: str) -> Optional[str]:
    path = operator_file_path(excel_output_dir)
    if not os.path.isfile(path):
        env_op = normalize_operator(os.getenv("GC_OPERATOR", "").strip())
        return env_op
    try:
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
    except (OSError, json.JSONDecodeError):
        return None
    return normalize_operator(str(data.get("operator", "")).strip())


def save_operator(excel_output_dir: str, operator: str) -> str:
    """작업자 저장. 반환: 정규화된 operator id."""
    op = normalize_operator(operator)
    if not op:
        raise ValueError(f"알 수 없는 작업자: {operator!r}")
    os.makedirs(os.path.normpath(excel_output_dir), exist_ok=True)
    path = operator_file_path(excel_output_dir)
    payload = {
        "operator": op,
        "label": "차완" if op == OPERATOR_CHAWAN else "차헌",
        "mail_to": mail_for_operator(op),
    }
    with open(path, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)
        f.write("\n")
    # 현재 프로세스·dotenv 캐시용
    os.environ["GC_OPERATOR"] = op
    os.environ["MAIL_TO"] = payload["mail_to"]
    return op


def resolve_recipient(excel_output_dir: str, fallback_mail_to: str) -> tuple[str, Optional[str]]:
    """
    (recipient, operator_or_None).

    dual 모드에서 작업자 미지정이면 recipient="" 와 operator=None.
    """
    if not dual_operator_mail_enabled():
        return (fallback_mail_to or "").strip(), None
    op = load_operator(excel_output_dir)
    if not op:
        return "", None
    mail = mail_for_operator(op)
    return mail, op


def message_is_operator_only(text: str) -> bool:
    """「차완」「차헌」만 — 작업자 전환."""
    stripped = text.strip()
    if not stripped or len(stripped) > 24:
        return False
    return bool(_OPERATOR_ONLY_RE.match(stripped))


def extract_operator_from_message(text: str) -> Optional[str]:
    """메시지에 포함된 첫 작업자 토큰."""
    if not text or not text.strip():
        return None
    only = _OPERATOR_ONLY_RE.match(text.strip())
    if only:
        return normalize_operator(only.group(1))
    match = _OPERATOR_TOKEN_RE.search(text)
    if match:
        return normalize_operator(match.group(1))
    return None


def operator_label(operator: str) -> str:
    op = normalize_operator(operator) or operator
    if op == OPERATOR_CHAWAN:
        return "차완"
    if op == OPERATOR_CHAHEON:
        return "차헌"
    return op
