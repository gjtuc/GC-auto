# -*- coding: utf-8 -*-
"""O5-M — worksheet keyword match (촉매 L1707–1714)."""

from __future__ import annotations

from typing import Any, Dict, List, Mapping, MutableMapping, Tuple

from data_pc_origin.o0_keys import normalize_origin_key
from data_pc_origin.o0_types import OriginWarning
from data_pc_origin.o5_iterate import iter_pages_w
from data_pc_origin.o5_text import compose_search_text


def keyword_in_text(text: str, keyword: str) -> bool:
    """`_normalize_origin_key(kw) in _normalize_origin_key(text)` — O0-K 위임."""
    if keyword is None or not str(keyword).strip():
        return False
    nk = normalize_origin_key(keyword)
    if not nk:
        return False
    nt = normalize_origin_key(text)
    return nk in nt


def find_worksheet_for_keyword(op: Any, keyword: str) -> Any | None:
    """촉매 nested loop + break (L1710–1714)."""
    for book in iter_pages_w(op):
        for wks in book:
            search_str = compose_search_text(book, wks)
            if keyword_in_text(search_str, keyword):
                return wks
    return None


def resolve_worksheets(
    op: Any,
    mapping: Mapping[str, str],
    df: Any,
) -> Tuple[Dict[str, Any], List[str]]:
    """mapping 순회 · df col 없으면 skip · (hits by origin kw, misses)."""
    cols = set(getattr(df, "columns", df))
    hits: Dict[str, Any] = {}
    misses: List[str] = []
    for _df_col, origin_kw in mapping.items():
        if _df_col not in cols:
            continue
        wks = find_worksheet_for_keyword(op, origin_kw)
        if wks is not None:
            hits[origin_kw] = wks
        else:
            misses.append(origin_kw)
    return hits, misses


def report_missing(misses: List[str]) -> List[OriginWarning]:
    if not misses:
        return []
    return [OriginWarning(code="WKS_MISS", detail=", ".join(misses))]
