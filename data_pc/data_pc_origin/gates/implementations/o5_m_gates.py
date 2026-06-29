# -*- coding: utf-8 -*-
"""O5-M L4 gate bodies."""

from __future__ import annotations

import inspect
from types import SimpleNamespace
from unittest import mock

from data_pc_origin.gates.registry import O5_DEPS, register_gate
from data_pc_origin.o0_mapping import DEFAULT_ORIGIN_MAPPING, MappingValidationError, validate_mapping
from data_pc_origin.o0_types import OriginWarning
from data_pc_origin.o5_fixtures import (
    MISS_MATRIX,
    fx_default_mapping_op,
    fx_dup_wks_name_op,
    fx_opju_two_books,
    make_mock_op,
)
from data_pc_origin.o5_match import (
    find_worksheet_for_keyword,
    keyword_in_text,
    report_missing,
    resolve_worksheets,
)


def _assert(condition: bool, msg: str = "") -> None:
    if not condition:
        raise AssertionError(msg or "assertion failed")


class _FakeDf:
    def __init__(self, columns: list[str]) -> None:
        self.columns = columns


# --- O5-M-01 (14) ---


def _gate_o5_m_01_a_1() -> None:
    _assert(keyword_in_text("Book1 H2yield", "") is False)


def _gate_o5_m_01_b_1() -> None:
    _assert(keyword_in_text("Book1 H2yield", "   ") is False)


def _gate_o5_m_01_c_1() -> None:
    with mock.patch(
        "data_pc_origin.o5_match.normalize_origin_key",
        wraps=__import__("data_pc_origin.o0_keys", fromlist=["normalize_origin_key"]).normalize_origin_key,
    ) as spy:
        keyword_in_text("Book1 H2yield Sheet1", "H2 yield")
        _assert(spy.call_count >= 1)


def _gate_o5_m_01_d_1() -> None:
    with mock.patch(
        "data_pc_origin.o5_match.normalize_origin_key",
        wraps=__import__("data_pc_origin.o0_keys", fromlist=["normalize_origin_key"]).normalize_origin_key,
    ) as spy:
        keyword_in_text("Book1 H2yield Sheet1", "H2 yield")
        _assert(spy.call_count >= 2)


def _gate_o5_m_01_e_1() -> None:
    _assert(keyword_in_text("Book1 H2yield Sheet1", "H2 yield") is True)


def _gate_o5_m_01_f_1() -> None:
    _assert(keyword_in_text("h2yield", "co2conversion") is False)


def _gate_o5_m_01_g_1() -> None:
    c = MISS_MATRIX["C1"]
    _assert(keyword_in_text(str(c["search"]), str(c["kw"])) is bool(c["expect"]))


def _gate_o5_m_01_h_1() -> None:
    c = MISS_MATRIX["C2"]
    _assert(keyword_in_text(str(c["search"]), str(c["kw"])) is bool(c["expect"]))


def _gate_o5_m_01_i_1() -> None:
    c = MISS_MATRIX["C3"]
    _assert(keyword_in_text(str(c["search"]), str(c["kw"])) is bool(c["expect"]))


def _gate_o5_m_01_j_1() -> None:
    c = MISS_MATRIX["C4"]
    _assert(keyword_in_text(str(c["search"]), str(c["kw"])) is bool(c["expect"]))


def _gate_o5_m_01_k_1() -> None:
    c = MISS_MATRIX["C5"]
    _assert(keyword_in_text(str(c["search"]), str(c["kw"])) is bool(c["expect"]))


def _gate_o5_m_01_l_1() -> None:
    src = inspect.getsource(__import__("data_pc_origin.o5_match", fromlist=["keyword_in_text"]))
    _assert("def normalize_origin_key" not in src)
    _assert("from data_pc_origin.o0_keys import normalize_origin_key" in src)


def _gate_o5_m_01_m_1() -> None:
    _assert(keyword_in_text("", "H2 yield") is False)


def _gate_o5_m_01_n_1() -> None:
    _assert(keyword_in_text("", "") is False)


# --- O5-M-02 (14) ---


def _gate_o5_m_02_a_1() -> None:
    op, _ = fx_opju_two_books()
    with mock.patch("data_pc_origin.o5_match.iter_pages_w", wraps=iter_pages_w_import()) as spy:
        find_worksheet_for_keyword(op, "H2 yield")
        _assert(spy.call_count == 1)


def iter_pages_w_import():  # noqa: N802
    from data_pc_origin.o5_iterate import iter_pages_w

    return iter_pages_w


def _gate_o5_m_02_b_1() -> None:
    op, _ = fx_opju_two_books()
    from data_pc_origin.o5_text import compose_search_text

    with mock.patch(
        "data_pc_origin.o5_match.compose_search_text",
        wraps=compose_search_text,
    ) as spy:
        find_worksheet_for_keyword(op, "H2 yield")
        _assert(spy.call_count >= 1)


def _gate_o5_m_02_c_1() -> None:
    op, _ = fx_opju_two_books()
    with mock.patch(
        "data_pc_origin.o5_match.keyword_in_text",
        wraps=keyword_in_text,
    ) as spy:
        find_worksheet_for_keyword(op, "H2 yield")
        _assert(spy.call_count >= 1)


def _gate_o5_m_02_d_1() -> None:
    op, _ = fx_opju_two_books()
    wks = find_worksheet_for_keyword(op, "H2 yield")
    _assert(wks is not None)
    _assert(wks.name == "H2yield")


def _gate_o5_m_02_e_1() -> None:
    op, _ = fx_opju_two_books()
    _assert(find_worksheet_for_keyword(op, "__no_such_kw__") is None)


def _gate_o5_m_02_f_1() -> None:
    op, _ = fx_opju_two_books()
    from data_pc_origin.o5_text import compose_search_text

    n = {"c": 0}

    def counting_compose(book, wks):  # type: ignore[no-untyped-def]
        n["c"] += 1
        return compose_search_text(book, wks)

    with mock.patch("data_pc_origin.o5_match.compose_search_text", side_effect=counting_compose):
        wks = find_worksheet_for_keyword(op, "H2 yield")
    _assert(wks is not None)
    _assert(n["c"] == 1)


def _gate_o5_m_02_g_1() -> None:
    op, _ = fx_dup_wks_name_op()
    seen: list[str] = []
    from data_pc_origin.o5_iterate import iter_pages_w as real_iter

    def spy_pages(op_arg):  # type: ignore[no-untyped-def]
        for book in real_iter(op_arg):
            seen.append(book.name)
            yield book

    with mock.patch("data_pc_origin.o5_match.iter_pages_w", side_effect=spy_pages):
        wks = find_worksheet_for_keyword(op, "H2 yield")
    _assert(wks is not None)
    _assert(seen == ["BookFirst"])


def _gate_o5_m_02_h_1() -> None:
    op, _ = fx_opju_two_books()
    from data_pc_origin.o5_text import compose_search_text

    n = {"c": 0}

    def counting_compose(book, wks):  # type: ignore[no-untyped-def]
        n["c"] += 1
        return compose_search_text(book, wks)

    with mock.patch("data_pc_origin.o5_match.compose_search_text", side_effect=counting_compose):
        find_worksheet_for_keyword(op, "H2 yield")
    _assert(n["c"] == 1)


def _gate_o5_m_02_i_1() -> None:
    op, books = fx_dup_wks_name_op()
    wks = find_worksheet_for_keyword(op, "H2 yield")
    _assert(wks is books[0]._sheets[0])


def _gate_o5_m_02_j_1() -> None:
    op, _ = fx_opju_two_books()
    kw = "H2 yield"
    sent: list[str] = []

    def capture(text, keyword):  # type: ignore[no-untyped-def]
        sent.append(keyword)
        return keyword_in_text(text, keyword)

    with mock.patch("data_pc_origin.o5_match.keyword_in_text", side_effect=capture):
        find_worksheet_for_keyword(op, kw)
    _assert(sent and sent[0] == kw)


def _gate_o5_m_02_k_1() -> None:
    op, _ = fx_opju_two_books()
    try:
        result = find_worksheet_for_keyword(op, "__missing__")
    except Exception as exc:
        raise AssertionError(f"expected None not raise: {exc}") from exc
    _assert(result is None)


def _gate_o5_m_02_l_1() -> None:
    op, _ = fx_opju_two_books()
    wks = find_worksheet_for_keyword(op, "H2 yield")
    _assert(wks is not None and wks.name == "H2yield")


def _gate_o5_m_02_m_1() -> None:
    op, _ = fx_opju_two_books()
    wks = find_worksheet_for_keyword(op, "CO2 conversion")
    _assert(wks is not None and wks.name == "CO2conversion")


def _gate_o5_m_02_n_1() -> None:
    op, _ = fx_opju_two_books()
    from data_pc_origin.o5_text import compose_search_text

    n = {"c": 0}

    def counting_compose(book, wks):  # type: ignore[no-untyped-def]
        n["c"] += 1
        return compose_search_text(book, wks)

    with mock.patch("data_pc_origin.o5_match.compose_search_text", side_effect=counting_compose):
        find_worksheet_for_keyword(op, "H2 yield")
    _assert(n["c"] == 1)


# --- O5-M-03 (18) ---


def _gate_o5_m_03_a_1() -> None:
    op, _ = fx_default_mapping_op()
    df = _FakeDf(list(DEFAULT_ORIGIN_MAPPING.keys()))
    order: list[str] = []
    real_find = find_worksheet_for_keyword

    def track(op_, kw):  # type: ignore[no-untyped-def]
        order.append(kw)
        return real_find(op_, kw)

    with mock.patch("data_pc_origin.o5_match.find_worksheet_for_keyword", side_effect=track):
        resolve_worksheets(op, DEFAULT_ORIGIN_MAPPING, df)
    _assert(order == list(DEFAULT_ORIGIN_MAPPING.values()))


def _gate_o5_m_03_b_1() -> None:
    op, _ = fx_default_mapping_op()
    df = _FakeDf(["H2 Yield (%)"])
    _, misses = resolve_worksheets(op, DEFAULT_ORIGIN_MAPPING, df)
    _assert("CO2 conversion" not in misses)


def _gate_o5_m_03_c_1() -> None:
    op, _ = fx_default_mapping_op()
    df = _FakeDf(["H2 Yield (%)"])
    with mock.patch(
        "data_pc_origin.o5_match.find_worksheet_for_keyword",
        wraps=find_worksheet_for_keyword,
    ) as spy:
        resolve_worksheets(op, DEFAULT_ORIGIN_MAPPING, df)
        _assert(spy.call_count == 1)


def _gate_o5_m_03_d_1() -> None:
    op, _ = fx_default_mapping_op()
    df = _FakeDf(["H2 Yield (%)"])
    hits, _ = resolve_worksheets(op, DEFAULT_ORIGIN_MAPPING, df)
    _assert("H2 yield" in hits)


def _gate_o5_m_03_e_1() -> None:
    op = make_mock_op([])
    df = _FakeDf(["H2 Yield (%)"])
    _, misses = resolve_worksheets(op, DEFAULT_ORIGIN_MAPPING, df)
    _assert("H2 yield" in misses)


def _gate_o5_m_03_f_1() -> None:
    op = make_mock_op([])
    cols = ["H2 Yield (%)", "CO2 Conversion (%)", "CH4 Conversion (%)"]
    df = _FakeDf(cols)
    _, misses = resolve_worksheets(op, DEFAULT_ORIGIN_MAPPING, df)
    expected = [
        DEFAULT_ORIGIN_MAPPING[c] for c in DEFAULT_ORIGIN_MAPPING if c in cols
    ]
    _assert(misses == expected)


def _gate_o5_m_03_g_1() -> None:
    op, _ = fx_default_mapping_op()
    df = _FakeDf(list(DEFAULT_ORIGIN_MAPPING.keys()))
    hits, _ = resolve_worksheets(op, DEFAULT_ORIGIN_MAPPING, df)
    _assert(len(hits) <= 8)


def _gate_o5_m_03_h_1() -> None:
    op, _ = fx_default_mapping_op()
    df = _FakeDf(list(DEFAULT_ORIGIN_MAPPING.keys()))
    hits, misses = resolve_worksheets(op, DEFAULT_ORIGIN_MAPPING, df)
    _assert(len(hits) == 8 and len(misses) == 0)


def _gate_o5_m_03_i_1() -> None:
    op, _ = fx_default_mapping_op()
    df = _FakeDf(["H2 Yield (%)", "CO2 Conversion (%)"])
    hits, _ = resolve_worksheets(op, DEFAULT_ORIGIN_MAPPING, df)
    _assert(len(hits) <= 2)


def _gate_o5_m_03_j_1() -> None:
    op = make_mock_op([])
    df = _FakeDf(["H2 Yield (%)", "CO2 Conversion (%)"])
    _, misses = resolve_worksheets(op, DEFAULT_ORIGIN_MAPPING, df)
    _assert(set(misses) <= {"H2 yield", "CO2 conversion"})


def _gate_o5_m_03_k_1() -> None:
    op, _ = fx_opju_two_books()
    df = _FakeDf(["H2 Yield (%)", "CO2 Conversion (%)", "C2H6 Conversion (%)"])
    hits, misses = resolve_worksheets(op, DEFAULT_ORIGIN_MAPPING, df)
    _assert(len(hits) >= 1 and len(misses) >= 1)


def _gate_o5_m_03_l_1() -> None:
    op = make_mock_op([])
    df = _FakeDf(["H2 Yield (%)", "CO2 Conversion (%)"])
    hits, misses = resolve_worksheets(op, DEFAULT_ORIGIN_MAPPING, df)
    _assert(len(hits) == 0 and len(misses) == 2)


def _gate_o5_m_03_m_1() -> None:
    op = make_mock_op([])
    df = _FakeDf(["H2 Yield (%)"])
    hits, misses = resolve_worksheets(op, DEFAULT_ORIGIN_MAPPING, df)
    _assert(len(hits) == 0 and len(misses) > 0)


def _gate_o5_m_03_n_1() -> None:
    op, _ = fx_opju_two_books()
    df = _FakeDf(["H2 Yield (%)", "CO2 Conversion (%)"])
    hits, _ = resolve_worksheets(op, DEFAULT_ORIGIN_MAPPING, df)
    _assert(hits["H2 yield"].name == "H2yield")
    _assert(hits["CO2 conversion"].name == "CO2conversion")


def _gate_o5_m_03_o_1() -> None:
    bad = {"A": "H2 yield", "B": "h2yield"}
    try:
        validate_mapping(bad)
        raise AssertionError("expected MappingValidationError")
    except MappingValidationError:
        pass


def _gate_o5_m_03_p_1() -> None:
    op, _ = fx_opju_two_books()
    df = _FakeDf(["H2 Yield (%)"])
    result = resolve_worksheets(op, DEFAULT_ORIGIN_MAPPING, df)
    _assert(isinstance(result, tuple) and len(result) == 2)


def _gate_o5_m_03_q_1() -> None:
    op, _ = fx_opju_two_books()
    df = _FakeDf(["H2 Yield (%)"])
    hits, _ = resolve_worksheets(op, DEFAULT_ORIGIN_MAPPING, df)
    _assert(all(isinstance(k, str) for k in hits))


def _gate_o5_m_03_r_1() -> None:
    op = make_mock_op([])
    df = _FakeDf(["H2 Yield (%)"])
    _, misses = resolve_worksheets(op, DEFAULT_ORIGIN_MAPPING, df)
    _assert(isinstance(misses, list))
    _assert(all(isinstance(m, str) for m in misses))


# --- O5-M-04 (8) ---


def _gate_o5_m_04_a_1() -> None:
    warns = report_missing(["H2 yield"])
    _assert(warns[0].code == "WKS_MISS")


def _gate_o5_m_04_b_1() -> None:
    warns = report_missing(["H2 yield", "CO2 conversion"])
    _assert("H2 yield" in warns[0].detail)
    _assert("CO2 conversion" in warns[0].detail)


def _gate_o5_m_04_c_1() -> None:
    _assert(report_missing([]) == [])


def _gate_o5_m_04_d_1() -> None:
    _assert(len(report_missing(["H2 yield"])) == 1)


def _gate_o5_m_04_e_1() -> None:
    misses = [DEFAULT_ORIGIN_MAPPING[k] for k in DEFAULT_ORIGIN_MAPPING]
    _assert(len(report_missing(misses)) == 1)


def _gate_o5_m_04_f_1() -> None:
    w = report_missing(["H2 yield"])[0]
    _assert(isinstance(w, OriginWarning))


def _gate_o5_m_04_g_1() -> None:
    text = str(report_missing(["H2 yield"])[0])
    _assert("WKS_MISS" in text or "H2 yield" in text)


def _gate_o5_m_04_h_1() -> None:
    _assert(report_missing([]) == [])


_O5_M_GATE_LIST: list[tuple[str, object]] = [
    ("O5-M-01-a-1", _gate_o5_m_01_a_1),
    ("O5-M-01-b-1", _gate_o5_m_01_b_1),
    ("O5-M-01-c-1", _gate_o5_m_01_c_1),
    ("O5-M-01-d-1", _gate_o5_m_01_d_1),
    ("O5-M-01-e-1", _gate_o5_m_01_e_1),
    ("O5-M-01-f-1", _gate_o5_m_01_f_1),
    ("O5-M-01-g-1", _gate_o5_m_01_g_1),
    ("O5-M-01-h-1", _gate_o5_m_01_h_1),
    ("O5-M-01-i-1", _gate_o5_m_01_i_1),
    ("O5-M-01-j-1", _gate_o5_m_01_j_1),
    ("O5-M-01-k-1", _gate_o5_m_01_k_1),
    ("O5-M-01-l-1", _gate_o5_m_01_l_1),
    ("O5-M-01-m-1", _gate_o5_m_01_m_1),
    ("O5-M-01-n-1", _gate_o5_m_01_n_1),
    ("O5-M-02-a-1", _gate_o5_m_02_a_1),
    ("O5-M-02-b-1", _gate_o5_m_02_b_1),
    ("O5-M-02-c-1", _gate_o5_m_02_c_1),
    ("O5-M-02-d-1", _gate_o5_m_02_d_1),
    ("O5-M-02-e-1", _gate_o5_m_02_e_1),
    ("O5-M-02-f-1", _gate_o5_m_02_f_1),
    ("O5-M-02-g-1", _gate_o5_m_02_g_1),
    ("O5-M-02-h-1", _gate_o5_m_02_h_1),
    ("O5-M-02-i-1", _gate_o5_m_02_i_1),
    ("O5-M-02-j-1", _gate_o5_m_02_j_1),
    ("O5-M-02-k-1", _gate_o5_m_02_k_1),
    ("O5-M-02-l-1", _gate_o5_m_02_l_1),
    ("O5-M-02-m-1", _gate_o5_m_02_m_1),
    ("O5-M-02-n-1", _gate_o5_m_02_n_1),
    ("O5-M-03-a-1", _gate_o5_m_03_a_1),
    ("O5-M-03-b-1", _gate_o5_m_03_b_1),
    ("O5-M-03-c-1", _gate_o5_m_03_c_1),
    ("O5-M-03-d-1", _gate_o5_m_03_d_1),
    ("O5-M-03-e-1", _gate_o5_m_03_e_1),
    ("O5-M-03-f-1", _gate_o5_m_03_f_1),
    ("O5-M-03-g-1", _gate_o5_m_03_g_1),
    ("O5-M-03-h-1", _gate_o5_m_03_h_1),
    ("O5-M-03-i-1", _gate_o5_m_03_i_1),
    ("O5-M-03-j-1", _gate_o5_m_03_j_1),
    ("O5-M-03-k-1", _gate_o5_m_03_k_1),
    ("O5-M-03-l-1", _gate_o5_m_03_l_1),
    ("O5-M-03-m-1", _gate_o5_m_03_m_1),
    ("O5-M-03-n-1", _gate_o5_m_03_n_1),
    ("O5-M-03-o-1", _gate_o5_m_03_o_1),
    ("O5-M-03-p-1", _gate_o5_m_03_p_1),
    ("O5-M-03-q-1", _gate_o5_m_03_q_1),
    ("O5-M-03-r-1", _gate_o5_m_03_r_1),
    ("O5-M-04-a-1", _gate_o5_m_04_a_1),
    ("O5-M-04-b-1", _gate_o5_m_04_b_1),
    ("O5-M-04-c-1", _gate_o5_m_04_c_1),
    ("O5-M-04-d-1", _gate_o5_m_04_d_1),
    ("O5-M-04-e-1", _gate_o5_m_04_e_1),
    ("O5-M-04-f-1", _gate_o5_m_04_f_1),
    ("O5-M-04-g-1", _gate_o5_m_04_g_1),
    ("O5-M-04-h-1", _gate_o5_m_04_h_1),
]


def register_o5_m_gates() -> None:
    for gate_id, fn in _O5_M_GATE_LIST:
        register_gate(gate_id, fn, depends=O5_DEPS[gate_id], layer="O5")  # type: ignore[arg-type]
