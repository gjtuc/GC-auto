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
    """촉매 nested loop + break (L1710–1714) — 첫 매칭만."""
    for wks in find_all_worksheets_for_keyword(op, keyword):
        return wks
    return None


def find_all_worksheets_for_keyword(op: Any, keyword: str) -> List[Any]:
    """동일 Long Name 복제 북 전부 (예: CO2conversion / CO2conversioA).

    짧은 키워드(``CH4``, ``C2H6``)는 같은 북 안의 다른 시트 이름에도
    부분 매칭될 수 있어, **북이 하나뿐이면 첫 시트만** 반환한다.
    북이 여러 개이고 ``lname`` 이 같으면(복제 폴더) 그 북들의 매칭 시트를
    모두 반환 — UI 에 동명 폴더가 둘일 때 한쪽만 갱신되는 문제를 막는다.
    """
    from data_pc_origin.o5_text import book_lname, book_name

    matches: List[Tuple[Any, Any]] = []
    for book in iter_pages_w(op):
        for wks in book:
            search_str = compose_search_text(book, wks)
            if keyword_in_text(search_str, keyword):
                matches.append((book, wks))
    if not matches:
        return []

    primary_book, primary_wks = matches[0]
    book_ids = {id(b) for b, _ in matches}
    if len(book_ids) == 1:
        return [primary_wks]

    def _book_key(book: Any) -> str:
        ln = normalize_origin_key(book_lname(book))
        return ln if ln else normalize_origin_key(book_name(book))

    primary_key = _book_key(primary_book)
    return [wks for book, wks in matches if _book_key(book) == primary_key]


def resolve_worksheets(
    op: Any,
    mapping: Mapping[str, str],
    df: Any,
) -> Tuple[Dict[str, Any], List[str]]:
    """mapping 순회 · df col 없으면 skip · (hits by origin kw, misses).

    hits 값은 하위 호환을 위해 **첫 매칭 시트**만 담는다.
    복제 시트 전부 쓰기는 ``run_writes`` + ``find_all_worksheets_for_keyword``.
    """
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
