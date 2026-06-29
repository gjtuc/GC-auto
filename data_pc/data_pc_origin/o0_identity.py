# -*- coding: utf-8 -*-
"""O0 — 시료 identity 토큰 (Comments 매칭용, originpro 불필요).

KCH 파일명 sample_key → 토큰 집합 → Origin Comments(열 C)와 부분 일치 비교.
Task C 형식(DRE(1.5%)@600°C Ni5/Ce5/Al2O3_장비)과 KCH stem(DRE(1.5) 600C Ni5_Ce5) 모두 커버.
"""

from __future__ import annotations

import re

# 장비 접미사·라벨 — identity 토큰에서 제외 (반응 drm/dre 와 혼동 방지)
_IDENTITY_STOPWORDS = frozenset({"장비", "ocm"})


def identity_match_tokens(sample_key: str) -> set[str]:
    """시료 문자열에서 G:/Origin 열 중복·재전송 매칭용 토큰."""
    key = (sample_key or "").lower().strip()
    if not key:
        return set()

    # _ / 공백 동등 — 촉매명 토큰 추출용
    normalized = key.replace("_", " ").replace("/", " ")

    tokens: set[str] = set(re.findall(r"@\d+|\d+\.?\d*g|dre|drm|drme", normalized))

    # 농도 (1.5) / (1.5%) — Comments 의 DRE(1.5%) 와 매칭
    conc_m = re.search(r"(?:dre|drm|drme)\s*\((\d+\.?\d*)\)?%?", normalized)
    if conc_m:
        tokens.add(conc_m.group(1))
    else:
        bare_conc = re.search(r"\((\d+\.?\d*)\)?%?", normalized)
        if bare_conc:
            tokens.add(bare_conc.group(1))

    # 온도 — @600 또는 파일명 600C / 600°c
    temp_at = re.search(r"@(\d{2,4})", normalized)
    if temp_at:
        tokens.add(f"@{temp_at.group(1)}")
    else:
        temp_c = re.search(r"\b(\d{3,4})\s*°?c\b", normalized)
        if temp_c:
            tokens.add(f"@{temp_c.group(1)}")

    tokens.update(re.findall(r"[a-z]+\d*|[a-z]{1,2}\d+", normalized))
    # 산화물형 촉매 (al2o3, ceo2) — [a-z]+\d* 만으로는 al2+o3 로 쪼개짐
    tokens.update(re.findall(r"[a-z]{1,2}\d+[a-z]*\d*", normalized))

    filtered = {
        t
        for t in tokens
        if (len(t) >= 2 or t.endswith("g"))
        and t not in _IDENTITY_STOPWORDS
        and not t.endswith("장비")
    }
    return filtered


def token_match_score(text: str, reference_tokens: set[str]) -> float:
    """reference_tokens 중 text에 포함된 비율."""
    if not reference_tokens:
        return 0.0
    lowered = (text or "").lower()
    matched = sum(1 for token in reference_tokens if token in lowered)
    return matched / len(reference_tokens)


def token_match_threshold(token_count: int) -> int:
    """comment_matches_identity 와 동일: max(2, int(0.6 * n))."""
    return max(2, int(token_count * 0.6))
