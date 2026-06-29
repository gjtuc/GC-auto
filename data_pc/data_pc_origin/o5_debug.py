# -*- coding: utf-8
"""O5-DEBUG — worksheet search trace (optional, live COM 금지)."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from data_pc_origin.o0_keys import normalize_origin_key
from data_pc_origin.o5_fixtures import MISS_MATRIX
from data_pc_origin.o5_iterate import iter_worksheets
from data_pc_origin.o5_match import keyword_in_text
from data_pc_origin.o5_text import compose_search_text, wks_name


@dataclass
class WorksheetSearchDebug:
    keyword: str
    candidates: List[Dict[str, str]] = field(default_factory=list)
    scanned: int = 0
    hit: Optional[Dict[str, str]] = None
    first_miss_fx: Optional[str] = None

    def as_dict(self) -> Dict[str, object]:
        return {
            "keyword": self.keyword,
            "scanned": self.scanned,
            "hit": self.hit,
            "first_miss_fx": self.first_miss_fx,
            "candidates": list(self.candidates),
        }


def _classify_first_miss(kw: str, search_str: str) -> Optional[str]:
    """FX C2/C4 유형 — norm miss vs wrong kw."""
    nk = normalize_origin_key(kw)
    nt = normalize_origin_key(search_str)
    if nk in nt:
        return None
    for fx_id in ("C2", "C4"):
        row = MISS_MATRIX.get(fx_id)
        if row and str(row["kw"]) == kw:
            return fx_id
    return "C2"


def find_worksheet_for_keyword_debug(op: Any, keyword: str) -> tuple[Any | None, WorksheetSearchDebug]:
    """O5-M 루프 + DEBUG 로그 (#106–110)."""
    dbg = WorksheetSearchDebug(keyword=keyword)
    for book, wks in iter_worksheets(op):
        search_str = compose_search_text(book, wks)
        nk = normalize_origin_key(keyword)
        nt = normalize_origin_key(search_str)
        matched = keyword_in_text(search_str, keyword)
        dbg.scanned += 1
        dbg.candidates.append(
            {
                "raw_search": search_str,
                "norm_kw": nk,
                "norm_search": nt,
                "book": getattr(book, "name", ""),
                "wks": wks_name(wks),
                "matched": str(matched),
            }
        )
        if matched:
            dbg.hit = dbg.candidates[-1]
            return wks, dbg
        if dbg.first_miss_fx is None:
            dbg.first_miss_fx = _classify_first_miss(keyword, search_str)
    return None, dbg
