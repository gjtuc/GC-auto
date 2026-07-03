# -*- coding: utf-8 -*-
"""O0 장비·날짜 규칙 + O6 열 삽입 가드 unittest."""
from __future__ import annotations

import unittest

from data_pc_origin.o0_equipment_day import evaluate_equipment_day_guard
from data_pc_origin.o6_fixtures import MockWks
from data_pc_origin.o6_guard import OriginColumnGuardError, enforce_equipment_day_guard
from data_pc_origin.o6_resolve import resolve_target_column

_LEFT = "20260620 DRE(1.5%)@600°C Ni5/Ce5/Al2O3_OCM 장비"
_NEW_SAME_DAY = "20260620 DRE(3%)@650°C Ni10/Al2O3_OCM 장비"
_NEW_NEXT_DAY = "20260621 DRE(1.5%)@600°C Ni5/Ce5/Al2O3_OCM 장비"
_NEW_OLDER = "20260619 DRE(1.5%)@600°C Ni5/Ce5/Al2O3_OCM 장비"


class TestO0EquipmentDay(unittest.TestCase):
    def test_same_equipment_same_date_needs_confirm(self):
        r = evaluate_equipment_day_guard(_LEFT, _NEW_SAME_DAY)
        self.assertTrue(r.needs_user_confirm)
        self.assertEqual(r.reason_code, "same_date")
        self.assertIn("20260620", r.question)

    def test_left_date_ahead_needs_confirm(self):
        left = "20260625 DRE(1.5%)@600°C Ni5/Ce5/Al2O3_OCM 장비"
        r = evaluate_equipment_day_guard(left, _NEW_OLDER)
        self.assertTrue(r.needs_user_confirm)
        self.assertEqual(r.reason_code, "left_date_ahead")

    def test_next_day_ok(self):
        r = evaluate_equipment_day_guard(_LEFT, _NEW_NEXT_DAY)
        self.assertFalse(r.needs_user_confirm)

    def test_different_equipment_ok(self):
        left_drm = "20260620 DRE(1.5%)@600°C Ni5/Ce5/Al2O3_DRM 장비"
        r = evaluate_equipment_day_guard(left_drm, _NEW_SAME_DAY)
        self.assertFalse(r.needs_user_confirm)


class TestO6EquipmentGuard(unittest.TestCase):
    def _wks_two_ocm(self) -> MockWks:
        return MockWks(
            {
                1: {"C": _LEFT},
                2: {"C": ""},
            },
            cols=3,
        )

    def test_resolve_blocks_without_confirm(self):
        wks = self._wks_two_ocm()
        with self.assertRaises(OriginColumnGuardError):
            resolve_target_column(wks, _NEW_SAME_DAY, lt_execute=lambda _c: None)

    def test_resolve_allows_with_confirm(self):
        wks = self._wks_two_ocm()
        col = resolve_target_column(
            wks,
            _NEW_SAME_DAY,
            lt_execute=lambda _c: None,
            column_guard_confirm=lambda _g: True,
        )
        self.assertEqual(col, 2)

    def test_enforce_skips_update_path_unchanged(self):
        """exact match — 가드 미호출 (기존 열 갱신)."""
        wks = MockWks({1: {"C": _NEW_SAME_DAY}}, cols=2)
        col = resolve_target_column(wks, _NEW_SAME_DAY)
        self.assertEqual(col, 1)


if __name__ == "__main__":
    unittest.main()
