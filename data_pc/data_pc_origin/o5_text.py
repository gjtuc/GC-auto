# -*- coding: utf-8 -*-
"""O5-T — worksheet search text (촉매 L1709)."""

from __future__ import annotations

from typing import Any


def _field_str(value: Any) -> str:
    """None → '' · strip 금지 (O5-T-01-d-1)."""
    if value is None:
        return ""
    if isinstance(value, str):
        return value
    return str(value)


def book_name(book: Any) -> str:
    return _field_str(book.name)


def book_lname(book: Any) -> str:
    return _field_str(book.lname)


def wks_name(wks: Any) -> str:
    return _field_str(wks.name)


def compose_search_text(book: Any, wks: Any) -> str:
    """`f"{book.name} {wks.name} {book.lname}"` — normalize 없음."""
    return f"{book_name(book)} {wks_name(wks)} {book_lname(book)}"
