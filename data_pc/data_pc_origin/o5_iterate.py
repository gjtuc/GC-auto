# -*- coding: utf-8 -*-
"""O5-I — worksheet page iteration (mock originpro op)."""

from __future__ import annotations

from typing import Any, Iterator, Tuple


def iter_pages_w(op: Any) -> Iterator[Any]:
    """`for book in op.pages('w'):` — 촉매 L1707."""
    if op is None:
        raise TypeError("op must not be None")
    pages_fn = op.pages
    if not callable(pages_fn):
        raise TypeError("op.pages must be callable")
    books = pages_fn("w")
    yield from books


def iter_worksheets(op: Any) -> Iterator[Tuple[Any, Any]]:
    """`for book in op.pages('w'): for wks in book:` — 촉매 L1707–1708."""
    for book in iter_pages_w(op):
        for wks in book:
            yield (book, wks)
