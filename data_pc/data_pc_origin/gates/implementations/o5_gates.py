# -*- coding: utf-8 -*-
"""O5-I L4 gate bodies — mock originpro."""

from __future__ import annotations

from types import SimpleNamespace

from data_pc_origin.gates.registry import O5_DEPS, register_gate
from data_pc_origin.o5_fixtures import MockBook, fx_opju_two_books, make_mock_op
from data_pc_origin.o5_iterate import iter_pages_w, iter_worksheets


def _assert(condition: bool, msg: str = "") -> None:
    if not condition:
        raise AssertionError(msg or "assertion failed")


def _gate_o5_i_01_a_1() -> None:
    op, _ = fx_opju_two_books()
    _assert(hasattr(op, "pages"))
    gen = iter_pages_w(op)
    _assert(next(gen).name == "Book1")


def _gate_o5_i_01_b_1() -> None:
    op, _ = fx_opju_two_books()
    _assert(callable(op.pages))


def _gate_o5_i_01_c_1() -> None:
    calls: list[str] = []
    books = [MockBook("B", "", ("S",))]
    op = make_mock_op(books, pages_calls=calls)
    list(iter_pages_w(op))
    _assert(calls == ["w"])


def _gate_o5_i_01_d_1() -> None:
    calls: list[str] = []
    op = make_mock_op([], pages_calls=calls)
    list(iter_pages_w(op))
    _assert(len(calls) == 1)


def _gate_o5_i_01_e_1() -> None:
    op, _ = fx_opju_two_books()
    gen = iter_pages_w(op)
    _assert(not isinstance(gen, list))


def _gate_o5_i_01_f_1() -> None:
    op = make_mock_op([])
    _assert(list(iter_pages_w(op)) == [])


def _gate_o5_i_01_g_1() -> None:
    op = make_mock_op([])
    try:
        list(iter_pages_w(op))
    except Exception as exc:
        raise AssertionError(f"empty pages must not raise: {exc}") from exc


def _gate_o5_i_01_h_1() -> None:
    calls: list[str] = []
    books = [MockBook("B1", "", ()), MockBook("B2", "", ())]
    op = make_mock_op(books, pages_calls=calls)
    gen = iter_pages_w(op)
    next(gen)
    _assert(len(calls) == 1)
    next(gen)
    _assert(len(calls) == 1)


def _gate_o5_i_01_i_1() -> None:
    try:
        list(iter_pages_w(None))  # type: ignore[arg-type]
        raise AssertionError("expected TypeError")
    except TypeError:
        pass


def _gate_o5_i_01_j_1() -> None:
    try:
        list(iter_pages_w(SimpleNamespace()))
        raise AssertionError("expected AttributeError")
    except AttributeError:
        pass


def _gate_o5_i_01_k_1() -> None:
    op, books = fx_opju_two_books()
    out = list(iter_pages_w(op))
    _assert(len(out) == 2)
    _assert(out is not books)


def _gate_o5_i_01_l_1() -> None:
    op, _ = fx_opju_two_books()
    names = [b.name for b in iter_pages_w(op)]
    _assert(names == ["Book1", "BookEmpty"])


def _gate_o5_i_02_a_1() -> None:
    calls: list[str] = []
    op, _ = fx_opju_two_books()
    real_pages = op.pages

    def tracked_pages(k: str):  # type: ignore[no-untyped-def]
        calls.append(k)
        return real_pages(k)

    op.pages = tracked_pages  # type: ignore[method-assign]
    list(iter_worksheets(op))
    _assert(calls == ["w"])


def _gate_o5_i_02_b_1() -> None:
    op, _ = fx_opju_two_books()
    for pair in iter_worksheets(op):
        _assert(isinstance(pair, tuple))
        _assert(len(pair) == 2)
        return
    raise AssertionError("expected at least one pair")


def _gate_o5_i_02_c_1() -> None:
    op, books = fx_opju_two_books()
    book_ref = books[0]
    for book, _wks in iter_worksheets(op):
        if book.name == "Book1":
            _assert(book is book_ref)
            return
    raise AssertionError("Book1 not found")


def _gate_o5_i_02_d_1() -> None:
    op, books = fx_opju_two_books()
    book1 = books[0]
    wks_ref = book1._sheets[0]
    for book, wks in iter_worksheets(op):
        if book is book1 and wks.name == "H2yield":
            _assert(wks is wks_ref)
            return
    raise AssertionError("H2yield wks not found")


def _gate_o5_i_02_e_1() -> None:
    op, _ = fx_opju_two_books()
    pairs = [(b.name, w.name) for b, w in iter_worksheets(op)]
    _assert(len(pairs) == 8)
    _assert(pairs[0] == ("Book1", "H2yield"))
    _assert(pairs[1] == ("Book1", "CO2conversion"))
    _assert(pairs[7] == ("Book1", "CO2sel"))


def _gate_o5_i_02_f_1() -> None:
    op, _ = fx_opju_two_books()
    empty_pairs = [(b.name, w.name) for b, w in iter_worksheets(op) if b.name == "BookEmpty"]
    _assert(empty_pairs == [])


def _gate_o5_i_02_g_1() -> None:
    op = make_mock_op([])
    _assert(list(iter_worksheets(op)) == [])


def _gate_o5_i_02_h_1() -> None:
    op, _ = fx_opju_two_books()
    book1_pairs = [(b.name, w.name) for b, w in iter_worksheets(op) if b.name == "Book1"]
    _assert(len(book1_pairs) == 8)


def _gate_o5_i_02_i_1() -> None:
    op, books = fx_opju_two_books()
    expected = sum(len(list(b)) for b in books)
    pairs = list(iter_worksheets(op))
    _assert(len(pairs) == expected)


def _gate_o5_i_02_j_1() -> None:
    op, _ = fx_opju_two_books()
    pairs = list(iter_worksheets(op))
    _assert(len(pairs) == len(set((id(b), id(w)) for b, w in pairs)))


def _gate_o5_i_02_k_1() -> None:
    op, _ = fx_opju_two_books()
    for _book, wks in iter_worksheets(op):
        _assert(isinstance(wks.name, str))
        return


def _gate_o5_i_02_l_1() -> None:
    op, _ = fx_opju_two_books()
    for book, _wks in iter_worksheets(op):
        _assert(isinstance(book.name, str))
        _assert(isinstance(book.lname, str))
        return


_O5_I_GATES = [
    ("O5-I-01-a-1", _gate_o5_i_01_a_1),
    ("O5-I-01-b-1", _gate_o5_i_01_b_1),
    ("O5-I-01-c-1", _gate_o5_i_01_c_1),
    ("O5-I-01-d-1", _gate_o5_i_01_d_1),
    ("O5-I-01-e-1", _gate_o5_i_01_e_1),
    ("O5-I-01-f-1", _gate_o5_i_01_f_1),
    ("O5-I-01-g-1", _gate_o5_i_01_g_1),
    ("O5-I-01-h-1", _gate_o5_i_01_h_1),
    ("O5-I-01-i-1", _gate_o5_i_01_i_1),
    ("O5-I-01-j-1", _gate_o5_i_01_j_1),
    ("O5-I-01-k-1", _gate_o5_i_01_k_1),
    ("O5-I-01-l-1", _gate_o5_i_01_l_1),
    ("O5-I-02-a-1", _gate_o5_i_02_a_1),
    ("O5-I-02-b-1", _gate_o5_i_02_b_1),
    ("O5-I-02-c-1", _gate_o5_i_02_c_1),
    ("O5-I-02-d-1", _gate_o5_i_02_d_1),
    ("O5-I-02-e-1", _gate_o5_i_02_e_1),
    ("O5-I-02-f-1", _gate_o5_i_02_f_1),
    ("O5-I-02-g-1", _gate_o5_i_02_g_1),
    ("O5-I-02-h-1", _gate_o5_i_02_h_1),
    ("O5-I-02-i-1", _gate_o5_i_02_i_1),
    ("O5-I-02-j-1", _gate_o5_i_02_j_1),
    ("O5-I-02-k-1", _gate_o5_i_02_k_1),
    ("O5-I-02-l-1", _gate_o5_i_02_l_1),
]


def register_o5_gates() -> None:
    for gate_id, fn in _O5_I_GATES:
        register_gate(gate_id, fn, depends=O5_DEPS[gate_id], layer="O5")
