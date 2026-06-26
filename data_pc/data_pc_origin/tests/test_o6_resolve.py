# -*- coding: utf-8 -*-
import json
import unittest
from pathlib import Path

from data_pc_origin.o6_fixtures import SAMPLE_EXACT, SAMPLE_NEW, fx_wks_exact_match, fx_wks_three_dated
from data_pc_origin.o6_insert import build_insert_lt_command
from data_pc_origin.o6_resolve import resolve_target_column


class TestO6Resolve(unittest.TestCase):
    def test_resolve_exact_no_lt(self) -> None:
        calls: list[str] = []
        col = resolve_target_column(
            fx_wks_exact_match(),
            SAMPLE_EXACT,
            lt_execute=calls.append,
        )
        self.assertEqual(col, 2)
        self.assertEqual(calls, [])

    def test_resolve_insert_calls_lt(self) -> None:
        calls: list[str] = []
        col = resolve_target_column(
            fx_wks_three_dated(),
            SAMPLE_NEW,
            lt_execute=calls.append,
        )
        self.assertEqual(col, 2)
        self.assertEqual(len(calls), 1)
        self.assertIn("GCData", calls[0])

    def test_write_resolve_artifact(self) -> None:
        lt_log: list[str] = []
        wks = fx_wks_three_dated()
        out = {
            "exact": resolve_target_column(
                fx_wks_exact_match(),
                SAMPLE_EXACT,
                lt_execute=lt_log.append,
            ),
            "insert": resolve_target_column(wks, SAMPLE_NEW, lt_execute=lt_log.append),
            "lt_cmd": build_insert_lt_command(wks, 2),
            "lt_calls": len(lt_log),
        }
        p = Path(__file__).resolve().parent.parent / "o6_resolve_smoke.json"
        p.write_text(json.dumps(out, indent=2), encoding="utf-8")
        self.assertEqual(out["exact"], 2)
        self.assertEqual(out["insert"], 2)
        self.assertEqual(out["lt_calls"], 1)


if __name__ == "__main__":
    unittest.main()
