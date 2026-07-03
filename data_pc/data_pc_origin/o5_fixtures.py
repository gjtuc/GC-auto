# -*- coding: utf-8 -*-
"""O5 — mock originpro op / book / wks (live COM 금지)."""

from __future__ import annotations

from types import SimpleNamespace
from typing import Any, Callable, Iterator, List, Sequence


def make_wks(name: str) -> SimpleNamespace:
    return SimpleNamespace(name=name)


class MockBook:
    """`for wks in book:` — Origin worksheet book stub."""

    def __init__(self, name: str, lname: str, sheet_names: Sequence[str]) -> None:
        self.name = name
        self.lname = lname
        self._sheets = [make_wks(n) for n in sheet_names]

    def __iter__(self) -> Iterator[SimpleNamespace]:
        return iter(self._sheets)


def make_mock_op(
    books: Sequence[MockBook],
    *,
    pages_calls: List[str] | None = None,
) -> SimpleNamespace:
    """`op.pages('w')` → books list."""

    def pages(kind: str) -> List[MockBook]:
        if pages_calls is not None:
            pages_calls.append(kind)
        return list(books)

    return SimpleNamespace(pages=pages)


def fx_opju_two_books() -> tuple[SimpleNamespace, List[MockBook]]:
    """FX-O5: Book1 (8 sheets) + BookEmpty."""
    book1 = MockBook(
        "Book1",
        "DRM Data",
        (
            "H2yield",
            "CO2conversion",
            "CH4conversion",
            "H2rate",
            "CO2rate",
            "CH4rate",
            "H2sel",
            "CO2sel",
        ),
    )
    book_empty = MockBook("BookEmpty", "", ())
    books = [book1, book_empty]
    return make_mock_op(books), books


def fx_opju_book1_only() -> tuple[SimpleNamespace, List[MockBook]]:
    book1 = MockBook(
        "Book1",
        "DRM Data",
        (
            "H2yield",
            "CO2conversion",
            "CH4conversion",
            "H2rate",
            "CO2rate",
            "CH4rate",
            "H2sel",
            "CO2sel",
        ),
    )
    books = [book1]
    return make_mock_op(books), books


# DEFAULT_ORIGIN_MAPPING 8키 ↔ search text 매칭용 시트명
_DEFAULT_MAPPING_SHEETS = (
    "H2yield",
    "CO2conversion",
    "CH4conversion",
    "C2H6conversion",
    "COyield",
    "CH4pct",
    "C2H4wks",
    "C2H6pct",
)


def fx_default_mapping_op() -> tuple[SimpleNamespace, List[MockBook]]:
    """O5-M-03-h 8/8 — Book1 + DEFAULT_ORIGIN_MAPPING."""
    book1 = MockBook("Book1", "DRM Data", _DEFAULT_MAPPING_SHEETS)
    books = [book1]
    return make_mock_op(books), books


def fx_dup_wks_name_op() -> tuple[SimpleNamespace, List[MockBook]]:
    """동일 wks.name 두 book — 첫 book wins (O5-M-02-i)."""
    b1 = MockBook("BookFirst", "DRM Data", ("H2yield",))
    b2 = MockBook("BookSecond", "DRM Data", ("H2yield",))
    books = [b1, b2]
    return make_mock_op(books), books


MISS_MATRIX: dict[str, dict[str, str | bool]] = {
    "C1": {"kw": "H2 yield", "search": "Book1 H2yield DRM Data", "expect": True},
    "C2": {"kw": "H2 yield", "search": "Book1 H2 DRM Data", "expect": False},
    "C3": {"kw": "H2 yield", "search": "Book1 H2 yield DRM Data", "expect": True},
    "C4": {"kw": "CO2 conversion", "search": "Book1 H2yield DRM Data", "expect": False},
    "C5": {"kw": "H2 yield", "search": "   ", "expect": False},
}
