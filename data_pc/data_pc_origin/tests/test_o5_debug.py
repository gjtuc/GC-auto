# -*- coding: utf-8 -*-
import json
import unittest
from pathlib import Path

from data_pc_origin.o5_debug import find_worksheet_for_keyword_debug
from data_pc_origin.o5_fixtures import fx_opju_two_books


class TestO5Debug(unittest.TestCase):
    def test_debug_hit_h2yield(self) -> None:
        op, _ = fx_opju_two_books()
        wks, dbg = find_worksheet_for_keyword_debug(op, "H2 yield")
        self.assertIsNotNone(wks)
        self.assertIsNotNone(dbg.hit)
        self.assertEqual(dbg.hit["wks"], "H2yield")

    def test_debug_first_miss_c4(self) -> None:
        op, _ = fx_opju_two_books()
        _, dbg = find_worksheet_for_keyword_debug(op, "CO2 conversion")
        self.assertEqual(dbg.first_miss_fx, "C4")

    def test_write_debug_smoke_artifact(self) -> None:
        op, _ = fx_opju_two_books()
        _, dbg = find_worksheet_for_keyword_debug(op, "H2 yield")
        out = dbg.as_dict()
        path = Path(__file__).resolve().parents[1] / "o5_debug_smoke.json"
        path.write_text(json.dumps(out, indent=2, ensure_ascii=False), encoding="utf-8")
        self.assertEqual(out["scanned"], len(out["candidates"]))
        self.assertIsNotNone(out["hit"])
        self.assertEqual(out["hit"]["wks"], "H2yield")


if __name__ == "__main__":
    unittest.main()
