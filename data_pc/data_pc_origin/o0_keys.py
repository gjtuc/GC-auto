# -*- coding: utf-8 -*-
"""O0 — Origin 키 정규화 (originpro 불필요)."""

from __future__ import annotations

import re


def normalize_origin_key(text: str | None) -> str:
    """Origin 북명(H2yield) ↔ 매핑 키(H2 yield) 비교용 — 공백 제거 후 소문자."""
    return re.sub(r"\s+", "", (text or "").lower())


def keys_match(a: str | None, b: str | None) -> bool:
    """정규화 후 동일 키."""
    return normalize_origin_key(a) == normalize_origin_key(b)


def keyword_in_normalized_text(keyword: str | None, search_text: str | None) -> bool:
    """정규화 키워드가 search_text 정규화 문자열에 포함되는지."""
    nk = normalize_origin_key(keyword)
    ns = normalize_origin_key(search_text)
    return bool(nk) and nk in ns
