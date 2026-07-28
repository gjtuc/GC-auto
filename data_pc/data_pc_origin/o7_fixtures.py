# -*- coding: utf-8 -*-
"""O7 — mock worksheet write capture (live COM 금지)."""

from __future__ import annotations

from typing import Any, Dict, List, Mapping, Optional, Tuple

WriteCall = Tuple[int, List[Any], str]


class MockWriteWks:
    """`from_list(col, values, comments=)` 호출 기록 · ``to_list`` 검증용."""

    def __init__(self, *, cols: int = 5) -> None:
        self.cols = cols
        self.writes: List[WriteCall] = []
        self._columns: Dict[int, List[Any]] = {}

    def from_list(
        self,
        col_idx: int,
        values: List[Any],
        *,
        comments: str = "",
        start: int | None = None,
    ) -> None:
        self.writes.append((col_idx, list(values), comments))
        if start is None or start <= 1:
            self._columns[col_idx] = list(values)
            return
        # Origin 1-based start — 기존 열에 구간 덮어쓰기
        base = list(self._columns.get(col_idx, []))
        need = start - 1 + len(values)
        if len(base) < need:
            base.extend([""] * (need - len(base)))
        for i, v in enumerate(values):
            base[start - 1 + i] = v
        self._columns[col_idx] = base

    def to_list(self, col_idx: int) -> List[Any]:
        return list(self._columns.get(col_idx, []))


def gc3_gap_series(length: int = 107) -> List[float]:
    """O0-S-06-b / O7-G — idx 99·100 NaN."""
    values = [1.0] * length
    values[99] = float("nan")
    values[100] = float("nan")
    return values


class _FakeDf:
    def __init__(self, data: Mapping[str, List[Any]]) -> None:
        self.columns = list(data.keys())
        self._data = data

    def __getitem__(self, key: str) -> List[Any]:
        return self._data[key]


def fx_df_two_cols() -> _FakeDf:
    return _FakeDf(
        {
            "H2 Yield (%)": gc3_gap_series(),
            "CO2 Conversion (%)": [0.5, 1.0, 2.0],
        }
    )


SAMPLE_WRITE = "202506101030 10Ni5Ce5 725C"
