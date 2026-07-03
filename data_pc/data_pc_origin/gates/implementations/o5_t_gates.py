# -*- coding: utf-8 -*-
"""O5-T L4 gate bodies."""

from __future__ import annotations

import inspect
from types import SimpleNamespace
from unittest import mock

from data_pc_origin.gates.registry import O5_DEPS, register_gate
from data_pc_origin.o5_fixtures import MockBook, fx_opju_two_books
from data_pc_origin.o5_text import (
    book_lname,
    book_name,
    compose_search_text,
    wks_name,
)


def _assert(condition: bool, msg: str = "") -> None:
    if not condition:
        raise AssertionError(msg or "assertion failed")


def _book1_wks(index: int = 0) -> tuple[MockBook, SimpleNamespace]:
    _op, books = fx_opju_two_books()
    book = books[0]
    return book, book._sheets[index]


# --- O5-T-01 book_name (5) ---


def _gate_o5_t_01_a_1() -> None:
    book, _ = _book1_wks()
    out = book_name(book)
    _assert(isinstance(out, str))
    _assert(out == book.name == "Book1")


def _gate_o5_t_01_b_1() -> None:
    book = SimpleNamespace(name=None, lname="")
    _assert(book_name(book) == "")


def _gate_o5_t_01_c_1() -> None:
    book = SimpleNamespace(name="", lname="")
    _assert(book_name(book) == "")


def _gate_o5_t_01_d_1() -> None:
    book = SimpleNamespace(name="  Book1  ", lname="")
    _assert(book_name(book) == "  Book1  ")


def _gate_o5_t_01_e_1() -> None:
    book = SimpleNamespace(name=None, lname="")
    out = book_name(book)
    _assert("None" not in out)


# --- O5-T-02 book_lname (5) ---


def _gate_o5_t_02_a_1() -> None:
    book, _ = _book1_wks()
    _assert(book_lname(book) == "DRM Data")


def _gate_o5_t_02_b_1() -> None:
    book = SimpleNamespace(name="B", lname="")
    _assert(book_lname(book) == "")


def _gate_o5_t_02_c_1() -> None:
    book = SimpleNamespace(name="B", lname=None)
    _assert(book_lname(book) == "")


def _gate_o5_t_02_d_1() -> None:
    book, _ = _book1_wks()
    _assert(book_lname(book) == "DRM Data")


def _gate_o5_t_02_e_1() -> None:
    book = SimpleNamespace(name="B", lname="反応データ")
    _assert(book_lname(book) == "反応データ")


# --- O5-T-03 wks_name (5) ---


def _gate_o5_t_03_a_1() -> None:
    _book, wks = _book1_wks()
    out = wks_name(wks)
    _assert(isinstance(out, str))
    _assert(out == wks.name)


def _gate_o5_t_03_b_1() -> None:
    wks = SimpleNamespace(name="")
    _assert(wks_name(wks) == "")


def _gate_o5_t_03_c_1() -> None:
    _book, wks = _book1_wks(0)
    _assert(wks_name(wks) == "H2yield")


def _gate_o5_t_03_d_1() -> None:
    _book, wks = _book1_wks(1)
    _assert(wks_name(wks) == "CO2conversion")


def _gate_o5_t_03_e_1() -> None:
    wks = SimpleNamespace(name=" H2yield ")
    _assert(wks_name(wks) == " H2yield ")


# --- O5-T-04 compose (12) ---


def _gate_o5_t_04_a_1() -> None:
    book, wks = _book1_wks()
    with mock.patch("data_pc_origin.o5_text.book_name", wraps=book_name) as spy:
        compose_search_text(book, wks)
        spy.assert_called_once_with(book)


def _gate_o5_t_04_b_1() -> None:
    book, wks = _book1_wks()
    with mock.patch("data_pc_origin.o5_text.wks_name", wraps=wks_name) as spy:
        compose_search_text(book, wks)
        spy.assert_called_once_with(wks)


def _gate_o5_t_04_c_1() -> None:
    book, wks = _book1_wks()
    with mock.patch("data_pc_origin.o5_text.book_lname", wraps=book_lname) as spy:
        compose_search_text(book, wks)
        spy.assert_called_once_with(book)


def _gate_o5_t_04_d_1() -> None:
    book, wks = _book1_wks()
    out = compose_search_text(book, wks)
    _assert(out == f"{book.name} {wks.name} {book.lname}")


def _gate_o5_t_04_e_1() -> None:
    book, wks = _book1_wks()
    manual = f"{book.name} {wks.name} {book.lname}"
    _assert(compose_search_text(book, wks) == manual)


def _gate_o5_t_04_f_1() -> None:
    book, wks = _book1_wks(0)
    _assert(compose_search_text(book, wks) == "Book1 H2yield DRM Data")


def _gate_o5_t_04_g_1() -> None:
    book, wks = _book1_wks(1)
    _assert(compose_search_text(book, wks) == "Book1 CO2conversion DRM Data")


def _gate_o5_t_04_h_1() -> None:
    src = inspect.getsource(
        __import__("data_pc_origin.o5_text", fromlist=["compose_search_text"])
    )
    _assert("o0_keys" not in src)
    _assert("normalize_origin_key" not in src)


def _gate_o5_t_04_i_1() -> None:
    book = MockBook("Book1", "", ("H2yield",))
    wks = book._sheets[0]
    out = compose_search_text(book, wks)
    _assert(out == "Book1 H2yield ")


def _gate_o5_t_04_j_1() -> None:
    book, wks = _book1_wks()
    manual = f"{book_name(book)} {wks_name(wks)} {book_lname(book)}"
    _assert(compose_search_text(book, wks) == manual)


def _gate_o5_t_04_k_1() -> None:
    book, wks = _book1_wks()
    _assert(len(compose_search_text(book, wks)) > 0)


def _gate_o5_t_04_l_1() -> None:
    book, wks = _book1_wks()
    out = compose_search_text(book, wks)
    _assert("Book1" in out)
    _assert(out != out.lower())


_O5_T_GATES = [
    ("O5-T-01-a-1", _gate_o5_t_01_a_1),
    ("O5-T-01-b-1", _gate_o5_t_01_b_1),
    ("O5-T-01-c-1", _gate_o5_t_01_c_1),
    ("O5-T-01-d-1", _gate_o5_t_01_d_1),
    ("O5-T-01-e-1", _gate_o5_t_01_e_1),
    ("O5-T-02-a-1", _gate_o5_t_02_a_1),
    ("O5-T-02-b-1", _gate_o5_t_02_b_1),
    ("O5-T-02-c-1", _gate_o5_t_02_c_1),
    ("O5-T-02-d-1", _gate_o5_t_02_d_1),
    ("O5-T-02-e-1", _gate_o5_t_02_e_1),
    ("O5-T-03-a-1", _gate_o5_t_03_a_1),
    ("O5-T-03-b-1", _gate_o5_t_03_b_1),
    ("O5-T-03-c-1", _gate_o5_t_03_c_1),
    ("O5-T-03-d-1", _gate_o5_t_03_d_1),
    ("O5-T-03-e-1", _gate_o5_t_03_e_1),
    ("O5-T-04-a-1", _gate_o5_t_04_a_1),
    ("O5-T-04-b-1", _gate_o5_t_04_b_1),
    ("O5-T-04-c-1", _gate_o5_t_04_c_1),
    ("O5-T-04-d-1", _gate_o5_t_04_d_1),
    ("O5-T-04-e-1", _gate_o5_t_04_e_1),
    ("O5-T-04-f-1", _gate_o5_t_04_f_1),
    ("O5-T-04-g-1", _gate_o5_t_04_g_1),
    ("O5-T-04-h-1", _gate_o5_t_04_h_1),
    ("O5-T-04-i-1", _gate_o5_t_04_i_1),
    ("O5-T-04-j-1", _gate_o5_t_04_j_1),
    ("O5-T-04-k-1", _gate_o5_t_04_k_1),
    ("O5-T-04-l-1", _gate_o5_t_04_l_1),
]


def register_o5_t_gates() -> None:
    for gate_id, fn in _O5_T_GATES:
        register_gate(gate_id, fn, depends=O5_DEPS[gate_id], layer="O5")
