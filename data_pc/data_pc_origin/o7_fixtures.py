# -*- coding: utf-8 -*-
"""O7 — mock worksheet write capture (live COM 금지)."""

from __future__ import annotations

from typing import Any, Dict, List, Mapping, Optional, Tuple

WriteCall = Tuple[int, List[Any], str]


class MockWriteWks:
    """`from_list(col, values, comments=)` 호출 기록."""

    def __init__(self, *, cols: int = 5) -> None:
        self.cols = cols
        self.writes: List[WriteCall] = []

    def from_list(self, col_idx: int, values: List[Any], *, comments: str = "") -> None:
        self.writes.append((col_idx, list(values), comments))


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
