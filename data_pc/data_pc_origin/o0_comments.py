# -*- coding: utf-8 -*-
"""O0 — Origin Comments 행 파싱·매칭 (originpro 불필요)."""

from __future__ import annotations

import re
from typing import Optional, Tuple

from data_pc_origin.o0_identity import identity_match_tokens

IdentityKey = Tuple[str, str]


def parse_comment_date(text: str | None) -> Optional[str]:
    """Origin Comments / 시료명 선두 YYYYMMDD — 열 날짜순 정렬용."""
    match = re.match(r"^(\d{8})", (text or "").strip())
    return match.group(1) if match else None


def sort_key_from_comment(text: str | None) -> tuple[int, str]:
    """날짜 없는 Comments → 맨 뒤 정렬 (1, '')."""
    date = parse_comment_date(text)
    if date:
        return (0, date)
    return (1, "")


def comment_matches_identity(comment: str | None, identity_key: IdentityKey | None) -> bool:
    """Origin Comments(기존 열)와 KCH identity (날짜·시료) 동일 실험 여부."""
    if not comment or not identity_key:
        return False
    date, sample = identity_key
    # 장비 접미사(_DRM/_OCM 장비)는 identity 토큰 비교에서 제외
    text = strip_equipment_suffix(comment).strip().lower()
    if not text.startswith(date):
        return False
    tokens = identity_match_tokens(sample)
    if not tokens:
        return False
    matched = sum(1 for token in tokens if token in text)
    return matched >= max(2, int(len(tokens) * 0.6))


# Origin Comments 끝 장비 접미사 — Task C (GC2→_DRM 장비, GC3→_OCM 장비)
_EQUIPMENT_SUFFIX_DRM = "_DRM 장비"
_EQUIPMENT_SUFFIX_OCM = "_OCM 장비"


def strip_equipment_suffix(comment: str | None) -> str:
    """Comments 끝 `_DRM 장비` / `_OCM 장비` 제거 — 열 매칭·정렬용 본문."""
    text = (comment or "").rstrip()
    if text.endswith(_EQUIPMENT_SUFFIX_OCM):
        return text[: -len(_EQUIPMENT_SUFFIX_OCM)].rstrip()
    if text.endswith(_EQUIPMENT_SUFFIX_DRM):
        return text[: -len(_EQUIPMENT_SUFFIX_DRM)].rstrip()
    return text


def parse_equipment_suffix(comment: str | None) -> Optional[str]:
    """Comments 접미사 → 장비 코드. 없으면 None."""
    text = (comment or "").rstrip()
    if text.endswith(_EQUIPMENT_SUFFIX_OCM):
        return "GC3"
    if text.endswith(_EQUIPMENT_SUFFIX_DRM):
        return "GC2"
    return None
