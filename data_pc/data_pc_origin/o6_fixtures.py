# -*- coding: utf-8 -*-
"""O6 — mock originpro worksheet (live COM 금지)."""

from __future__ import annotations

from typing import Dict, List, Mapping, Optional


class MockWks:
    """`wks.get_label(col, kind)` · `wks.cols` · `wks.lt_range()` — Origin worksheet stub."""

    def __init__(
        self,
        labels: Mapping[int, Mapping[str, str]],
        *,
        cols: Optional[int] = None,
        lt_range: str = "[Book1]Sheet1!",
        lt_calls: Optional[List[str]] = None,
    ) -> None:
        self._labels: Dict[int, Dict[str, str]] = {
            int(k): dict(v) for k, v in labels.items()
        }
        if cols is not None:
            self.cols = cols
        elif self._labels:
            self.cols = max(self._labels) + 1
        else:
            self.cols = 1
        self._lt_range = lt_range
        self.lt_calls: List[str] = lt_calls if lt_calls is not None else []

    def get_label(self, col_idx: int, kind: str) -> str:
        return self._labels.get(col_idx, {}).get(kind, "")

    def lt_range(self) -> str:
        return self._lt_range


def fx_wks_three_dated() -> MockWks:
    """FX-O6: Comments 3열 — 날짜순 정렬용."""
    return MockWks(
        {
            1: {"C": "202506010900 10Ni5Ce5 700C"},
            2: {"C": "202506151200 10Ni5Ce5 750C"},
            3: {"C": "202506201030 10Ni5Ce5 800C"},
        }
    )


def fx_wks_mixed_dated() -> MockWks:
    """날짜 Comments + 빈 Comments 1열."""
    return MockWks(
        {
            1: {"C": "202506010900 sample A"},
            2: {"C": ""},
            3: {"C": "202506201030 sample C"},
            4: {"C": "note only"},
        }
    )


def fx_wks_empty() -> MockWks:
    return MockWks({}, cols=1)


SAMPLE_EXACT = "202506151200 10Ni5Ce5 750C"
SAMPLE_NEW = "202506101030 10Ni5Ce5 725C"
IDENTITY_KEY = ("20260620", "dre(1.5) 600c ni5_ce5_al2o3")
IDENTITY_COMMENT = "20260620 DRE(1.5)@600°C 600CNi5_Ce5_Al2O3"


def fx_wks_exact_match() -> MockWks:
    """O6-F-01 — col 2 exact Comments hit."""
    return MockWks(
        {
            1: {"C": "202506010900 10Ni5Ce5 700C"},
            2: {"C": SAMPLE_EXACT},
            3: {"C": "202506201030 10Ni5Ce5 800C"},
        }
    )


def fx_wks_identity_match() -> MockWks:
    """O6-F-02 — identity 재전송 열."""
    return MockWks(
        {
            1: {"C": "202506010900 unrelated"},
            2: {"C": IDENTITY_COMMENT},
            3: {"C": "202506201030 other"},
        }
    )


def fx_wks_insert_plan() -> MockWks:
    """O6-P — 3 dated cols + occupied slot at insert."""
    return fx_wks_three_dated()
