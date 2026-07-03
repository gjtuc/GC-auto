# -*- coding: utf-8 -*-
import json
import unittest
from pathlib import Path

from data_pc_origin.o0_mapping import DEFAULT_ORIGIN_MAPPING
from data_pc_origin.o5_fixtures import fx_default_mapping_op, fx_opju_two_books, make_mock_op
from data_pc_origin.o5_match import (
    find_worksheet_for_keyword,
    keyword_in_text,
    report_missing,
    resolve_worksheets,
)


class _FakeDf:
    def __init__(self, columns: list[str]) -> None:
        self.columns = columns


class TestO5Match(unittest.TestCase):
    def test_keyword_h2_yield_match(self) -> None:
        self.assertTrue(keyword_in_text("Book1 H2yield DRM Data", "H2 yield"))

    def test_keyword_empty_kw(self) -> None:
        self.assertFalse(keyword_in_text("Book1 H2yield", ""))

    def test_find_h2yield(self) -> None:
        op, _ = fx_opju_two_books()
        wks = find_worksheet_for_keyword(op, "H2 yield")
        self.assertIsNotNone(wks)
        assert wks is not None
        self.assertEqual(wks.name, "H2yield")

    def test_resolve_8_of_8(self) -> None:
        op, _ = fx_default_mapping_op()
        df = _FakeDf(list(DEFAULT_ORIGIN_MAPPING.keys()))
        hits, misses = resolve_worksheets(op, DEFAULT_ORIGIN_MAPPING, df)
        self.assertEqual(len(hits), 8)
        self.assertEqual(misses, [])

    def test_symptom_empty_op(self) -> None:
        op = make_mock_op([])
        df = _FakeDf(["H2 Yield (%)", "CO2 Conversion (%)"])
        hits, misses = resolve_worksheets(op, DEFAULT_ORIGIN_MAPPING, df)
        self.assertEqual(len(hits), 0)
        self.assertEqual(len(misses), 2)

    def test_report_wks_miss(self) -> None:
        warns = report_missing(["H2 yield"])
        self.assertEqual(warns[0].code, "WKS_MISS")

    def test_write_resolve_artifact(self) -> None:
        """실행 검증용 JSON — hits/misses 의도 확인."""
        op, _ = fx_default_mapping_op()
        df = _FakeDf(["H2 Yield (%)", "CO2 Conversion (%)"])
        hits, misses = resolve_worksheets(op, DEFAULT_ORIGIN_MAPPING, df)
        out = {
            "hits": {k: v.name for k, v in hits.items()},
            "misses": misses,
        }
        path = Path(__file__).resolve().parents[1] / "o5_resolve_smoke.json"
        path.write_text(json.dumps(out, indent=2, ensure_ascii=False), encoding="utf-8")
        self.assertEqual(
            out,
            {"hits": {"H2 yield": "H2yield", "CO2 conversion": "CO2conversion"}, "misses": []},
        )


if __name__ == "__main__":
    unittest.main()
