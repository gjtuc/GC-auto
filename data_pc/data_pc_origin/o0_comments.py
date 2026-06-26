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
    text = comment.strip().lower()
    if not text.startswith(date):
        return False
    tokens = identity_match_tokens(sample)
    if not tokens:
        return False
    matched = sum(1 for token in tokens if token in text)
    return matched >= max(2, int(len(tokens) * 0.6))
