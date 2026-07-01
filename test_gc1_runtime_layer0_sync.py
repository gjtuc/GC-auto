# -*- coding: utf-8 -*-
"""T95 — gc1_runtime.layer0_sync 정적·실행 검증."""
from __future__ import annotations

import unittest

from gc1_runtime.layer0_sync import (
    SyncPostStatus,
    evaluate_sync_post_check,
    sync_double_click_coords,
    verify_analysis_list_populated,
)


class TestSyncDoubleClickCoords(unittest.TestCase):
    def test_matches_legacy_autochro_formula(self):
        """gc_autochro / P1.05~06 과 동일 좌표."""
        rel_x, rel_y = sync_double_click_coords(400, 200)
        self.assertEqual(rel_x, 248)
        self.assertEqual(rel_y, 33)

    def test_small_list_clamps_y(self):
        rel_x, rel_y = sync_double_click_coords(100, 20)
        self.assertGreaterEqual(rel_y, 12)
        self.assertGreaterEqual(rel_x, 20)


class TestSyncPostCheck(unittest.TestCase):
    def test_ok_after_sync_with_partial_run(self):
        """제어 4행(1~3 완료 + 4 진행) → 분석 4행."""
        result = evaluate_sync_post_check(4, 4)
        self.assertTrue(result.ok)
        self.assertEqual(result.status, SyncPostStatus.OK)

    def test_analysis_empty_when_not_synced(self):
        """수동 더블클릭 안 함 - 제어만 있고 분석 비어 있음."""
        result = evaluate_sync_post_check(4, 0)
        self.assertFalse(result.ok)
        self.assertEqual(result.status, SyncPostStatus.ANALYSIS_EMPTY)

    def test_control_empty(self):
        result = evaluate_sync_post_check(0, 0)
        self.assertEqual(result.status, SyncPostStatus.BOTH_EMPTY)

    def test_verify_populated_minimum(self):
        self.assertTrue(verify_analysis_list_populated(1))
        self.assertFalse(verify_analysis_list_populated(0))


if __name__ == "__main__":
    unittest.main()
