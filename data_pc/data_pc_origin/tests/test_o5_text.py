# -*- coding: utf-8 -*-
import unittest

from data_pc_origin.o5_fixtures import MockBook, fx_opju_two_books
from data_pc_origin.o5_text import book_name, compose_search_text, wks_name


class TestO5Text(unittest.TestCase):
    def test_compose_golden_h2yield(self) -> None:
        _op, books = fx_opju_two_books()
        book = books[0]
        wks = book._sheets[0]
        self.assertEqual(compose_search_text(book, wks), "Book1 H2yield DRM Data")

    def test_compose_matches_catalyst_fstring(self) -> None:
        _op, books = fx_opju_two_books()
        book = books[0]
        wks = book._sheets[1]
        manual = f"{book.name} {wks.name} {book.lname}"
        self.assertEqual(compose_search_text(book, wks), manual)

    def test_book_name_none_empty(self) -> None:
        from types import SimpleNamespace

        self.assertEqual(book_name(SimpleNamespace(name=None)), "")

    def test_empty_lname_trailing_space(self) -> None:
        book = MockBook("Book1", "", ("H2yield",))
        wks = book._sheets[0]
        self.assertEqual(compose_search_text(book, wks), "Book1 H2yield ")

    def test_wks_name_no_strip(self) -> None:
        from types import SimpleNamespace

        self.assertEqual(wks_name(SimpleNamespace(name=" H2yield ")), " H2yield ")


if __name__ == "__main__":
    unittest.main()
