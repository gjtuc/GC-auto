# -*- coding: utf-8 -*-
"""촉매 O6-F column resolve 위임 — 코드·실행(픽스처) 검증."""
from __future__ import annotations

import importlib.util
import sys
import unittest
from pathlib import Path

_CURSOR = Path(__file__).resolve().parent
if str(_CURSOR) not in sys.path:
    sys.path.insert(0, str(_CURSOR))

from data_pc_origin.catalyst_o6_bridge import catalyst_resolve_target_column
from data_pc_origin.o6_fixtures import (
    IDENTITY_KEY,
    SAMPLE_EXACT,
    SAMPLE_NEW,
    fx_wks_exact_match,
    fx_wks_identity_match,
)
from data_pc_origin.o6_resolve import resolve_target_column

_LIVE_COMMENT = "20260620 DRE(1.5%)@600°C Ni5/Ce5/Al2O3_OCM 장비"
_LIVE_IDENTITY = ("20260620", "dre(1.5) 600c ni5_ce5_al2o3")


def _load_catalyst():
    spec = importlib.util.spec_from_file_location(
        "catalyst_calc",
        _CURSOR / "촉매 반응 계산.py",
    )
    mod = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(mod)
    return mod


class TestCatalystO6Bridge(unittest.TestCase):
    def test_exact_match_fixture(self):
        wks = fx_wks_exact_match()
        self.assertEqual(
            catalyst_resolve_target_column(wks, SAMPLE_EXACT),
            resolve_target_column(wks, SAMPLE_EXACT, skip_equipment_day_guard=True),
        )

    def test_identity_match_fixture(self):
        wks = fx_wks_identity_match()
        self.assertEqual(
            catalyst_resolve_target_column(wks, SAMPLE_NEW, IDENTITY_KEY),
            resolve_target_column(
                wks, SAMPLE_NEW, IDENTITY_KEY, skip_equipment_day_guard=True
            ),
        )

    def test_dated_insert_with_mock_lt(self):
        """실행 검증 — 20250610 삽입 시 col 2 occupied → LT insert 호출."""
        wks = fx_wks_exact_match()
        cmds: list[str] = []

        def mock_lt(cmd: str) -> None:
            cmds.append(cmd)

        col = resolve_target_column(
            wks,
            SAMPLE_NEW,
            lt_execute=mock_lt,
            skip_equipment_day_guard=True,
        )
        self.assertEqual(col, 2)
        self.assertEqual(len(cmds), 1)
        self.assertIn("insert(GCData)", cmds[0])

    def test_live_identity_column_on_fixture(self):
        """GC Comments 형식 — identity 열 매칭(장비 접미사 포함)."""
        wks = fx_wks_identity_match()
        col = catalyst_resolve_target_column(
            wks,
            _LIVE_COMMENT,
            _LIVE_IDENTITY,
        )
        self.assertEqual(col, 2)


class TestCatalystModuleO6Delegate(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.catalyst = _load_catalyst()

    def test_find_column_delegates_to_o6(self):
        wks = fx_wks_exact_match()
        self.assertEqual(
            self.catalyst._find_worksheet_column_for_sample(wks, SAMPLE_EXACT),
            2,
        )

    def test_dated_columns_delegates(self):
        from data_pc_origin.o6_scan import dated_columns

        wks = fx_wks_exact_match()
        self.assertEqual(
            self.catalyst._worksheet_dated_columns(wks),
            dated_columns(wks),
        )


if __name__ == "__main__":
    unittest.main()
