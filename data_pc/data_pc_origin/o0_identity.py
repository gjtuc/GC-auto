# -*- coding: utf-8 -*-
"""O0 — 시료 identity 토큰 (Comments 매칭용, originpro 불필요)."""

from __future__ import annotations

import re


def identity_match_tokens(sample_key: str) -> set[str]:
    """시료 문자열에서 G:/Origin 열 중복 비교용 토큰."""
    key = (sample_key or "").lower()
    tokens = set(re.findall(r"@\d+|\d+\.?\d*g|dre|drm|drme", key))
    tokens.update(re.findall(r"[a-z]+\d*|[a-z]{1,2}\d+", key))
    return {t for t in tokens if len(t) >= 2 or t.endswith("g")}


def token_match_score(text: str, reference_tokens: set[str]) -> float:
    """reference_tokens 중 text에 포함된 비율."""
    if not reference_tokens:
        return 0.0
    lowered = text.lower()
    matched = sum(1 for token in reference_tokens if token in lowered)
    return matched / len(reference_tokens)


def token_match_threshold(token_count: int) -> int:
    """comment_matches_identity 와 동일: max(2, int(0.6 * n))."""
    return max(2, int(token_count * 0.6))
