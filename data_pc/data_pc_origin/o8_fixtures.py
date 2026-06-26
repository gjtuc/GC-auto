# -*- coding: utf-8 -*-
"""O8 — mock op / job sheets (live COM 금지)."""

from __future__ import annotations

from typing import Any, Dict, List, Mapping, Optional

from data_pc_origin.o6_fixtures import SAMPLE_EXACT
from data_pc_origin.o7_fixtures import MockWriteWks, SAMPLE_WRITE, _FakeDf, gc3_gap_series

_DEFAULT_JOB_SHEETS = (
    "H2yield",
    "CO2conversion",
    "CH4conversion",
    "C2H6conversion",
    "COyield",
    "CH4pct",
    "C2H4wks",
    "C2H6pct",
)


class JobSheet(MockWriteWks):
    """O5 match name + O7 from_list + O6 resolve labels."""

    def __init__(
        self,
        name: str,
        *,
        labels: Optional[Mapping[int, Mapping[str, str]]] = None,
        cols: int = 5,
    ) -> None:
        super().__init__(cols=cols)
        self.name = name
        self._labels: Dict[int, Dict[str, str]] = {
            int(k): dict(v) for k, v in (labels or {}).items()
        }

    def get_label(self, col_idx: int, kind: str) -> str:
        return self._labels.get(col_idx, {}).get(kind, "")

    def lt_range(self) -> str:
        return f"[Book1]{self.name}!"


class JobMockOp:
    """Origin op stub — open/save/exit 추적."""

    def __init__(self, books: List[MockBook]) -> None:
        self._books = books
        self.open_calls: List[str] = []
        self.save_calls: List[str] = []
        self.exit_calls: List[str] = []

    def pages(self, kind: str) -> List[MockBook]:
        return self._books

    def set_show(self, value: bool) -> None:
        pass

    def oext(self, value: bool) -> None:
        pass

    def open(self, path: str) -> bool:
        self.open_calls.append(path)
        return True

    def save(self, path: str) -> None:
        self.save_calls.append(path)

    def exit(self) -> None:
        self.exit_calls.append("exit")


def _sheet_with_exact(name: str, comment: str, col: int = 2) -> JobSheet:
    return JobSheet(name, labels={col: {"C": comment}}, cols=col + 1)


class JobBook:
    """Book with JobSheet children."""

    def __init__(self, name: str, lname: str, sheets: List[JobSheet]) -> None:
        self.name = name
        self.lname = lname
        self._sheets = sheets

    def __iter__(self):
        return iter(self._sheets)


def fx_job_op_full() -> tuple[JobMockOp, List[JobSheet]]:
    """8/8 mapping sheets — H2 exact comment for col reuse."""
    sheets = [
        _sheet_with_exact("H2yield", SAMPLE_EXACT, 2),
    ]
    for n in _DEFAULT_JOB_SHEETS[1:]:
        sheets.append(JobSheet(n, labels={1: {"C": "202506010900 seed"}}, cols=4))
    book = JobBook("Book1", "DRM Data", sheets)
    op = JobMockOp([book])
    return op, sheets


def fx_job_op_partial() -> tuple[JobMockOp, List[JobSheet]]:
    """2 sheets only — partial hits + misses."""
    sheets = [
        _sheet_with_exact("H2yield", SAMPLE_EXACT, 2),
        JobSheet("CO2conversion", labels={1: {"C": "202506010900 seed"}}, cols=4),
    ]
    book = JobBook("Book1", "DRM Data", sheets)
    return JobMockOp([book]), sheets


def fx_job_df_full() -> _FakeDf:
    return _FakeDf({col: gc3_gap_series() for col in (
        "C2H6 Conversion (%)",
        "CH4 Conversion (%)",
        "CO2 Conversion (%)",
        "H2 Yield (%)",
        "CO Yield (%)",
        "CH4 (%)",
        "C2H4 (%)",
        "C2H6 (%)",
    )})


def fx_job_df_partial() -> _FakeDf:
    return _FakeDf(
        {
            "H2 Yield (%)": gc3_gap_series(),
            "CO2 Conversion (%)": [0.1, 0.2, 0.3],
            "C2H6 Conversion (%)": [1.0, 2.0],
        }
    )


OPJU_FX = r"G:\test\Ni5_Ce5.opju"
SAMPLE_JOB = SAMPLE_WRITE
