# -*- coding: utf-8 -*-
"""T31 — gc1_runtime.layer0_ctl geometry·TAB 판별 테스트."""
from __future__ import annotations

import unittest

from gc1_runtime.layer0_ctl import (
    ListViewGeom,
    TreeGeom,
    filter_listview_candidates,
    listview_passes_size,
    listview_pick_score,
    menu_texts_include_analysis,
    menu_texts_include_control,
    needs_tab_select,
    pick_analysis_sample_table,
    pick_analysis_tree,
    pick_best_listview,
    pick_control_sync_list,
    relative_mid_y,
    tab_index_for_analysis,
    tab_index_for_control,
    tree_is_left_panel,
)
from gc1_runtime.layer0_win import WindowRect


WIN = WindowRect(left=0, top=0, right=1200, bottom=800)


def _lv(
    top: int,
    height: int,
    *,
    left: int = 10,
    width: int = 400,
    count: int = 10,
    ctrl_id: int = 0,
) -> ListViewGeom:
    return ListViewGeom(
        top=top,
        bottom=top + height,
        left=left,
        right=left + width,
        item_count=count,
        ctrl_id=ctrl_id,
    )


class TestListViewFilter(unittest.TestCase):
    def test_size_gate(self):
        small = _lv(100, 40, count=5)
        self.assertFalse(listview_passes_size(small))
        ok = _lv(100, 80, count=5)
        self.assertTrue(listview_passes_size(ok))

    def test_relative_mid_y(self):
        frac = relative_mid_y(300, 500, WIN)
        self.assertAlmostEqual(frac, 0.5)

    def test_lower_prefer_filters_top_table(self):
        upper = _lv(50, 100, count=20, ctrl_id=1)
        lower = _lv(550, 100, count=8, ctrl_id=2)
        got = filter_listview_candidates([upper, lower], WIN, prefer="lower")
        self.assertEqual([g.ctrl_id for g in got], [2])

    def test_fallback_to_any_when_lower_empty(self):
        only_upper = _lv(50, 100, count=5, ctrl_id=1)
        got = filter_listview_candidates([only_upper], WIN, prefer="lower")
        self.assertEqual(len(got), 1)


class TestListViewPick(unittest.TestCase):
    def test_control_vs_analysis_scoring(self):
        # 같은 count — control 은 frac 클수록 유리, analysis 는 frac 작을수록 유리
        low = _lv(550, 100, count=10, ctrl_id=1)
        high = _lv(50, 100, count=10, ctrl_id=2)
        s_ctrl_low = listview_pick_score(low, WIN, purpose="제어목록")
        s_ctrl_high = listview_pick_score(high, WIN, purpose="제어목록")
        self.assertGreater(s_ctrl_low, s_ctrl_high)
        s_ana_low = listview_pick_score(low, WIN, purpose="분석목록")
        s_ana_high = listview_pick_score(high, WIN, purpose="분석목록")
        self.assertGreater(s_ana_high, s_ana_low)

    def test_pick_control_sync_list(self):
        lower = _lv(600, 120, count=15, ctrl_id=9)
        upper = _lv(80, 120, count=30, ctrl_id=8)
        picked = pick_control_sync_list([upper, lower], WIN)
        self.assertEqual(picked.ctrl_id, 9)

    def test_pick_analysis_sample_table(self):
        lower = _lv(600, 120, count=15, ctrl_id=9)
        upper = _lv(80, 120, count=12, ctrl_id=8)
        picked = pick_analysis_sample_table([upper, lower], WIN)
        self.assertEqual(picked.ctrl_id, 8)

    def test_pick_raises_when_none(self):
        with self.assertRaises(RuntimeError):
            pick_best_listview([], WIN, prefer="any", purpose="analysis")


class TestTreeTab(unittest.TestCase):
    def test_tree_left_panel_only(self):
        left = TreeGeom(0, 400, 10, 200, ctrl_id=1)
        right = TreeGeom(0, 400, 700, 900, ctrl_id=2)
        self.assertTrue(tree_is_left_panel(left, WIN))
        self.assertFalse(tree_is_left_panel(right, WIN))
        picked = pick_analysis_tree([right, left], WIN)
        self.assertEqual(picked.ctrl_id, 1)

    def test_tree_missing_raises(self):
        right = TreeGeom(0, 400, 700, 900)
        with self.assertRaises(RuntimeError):
            pick_analysis_tree([right], WIN)

    def test_tab_menu_detection(self):
        self.assertTrue(menu_texts_include_analysis(["파일", "분석목록", "도움말"]))
        self.assertTrue(menu_texts_include_control(["제어목록"]))
        self.assertFalse(menu_texts_include_analysis(["제어목록"]))

    def test_tab_indices_and_needs_select(self):
        self.assertEqual(tab_index_for_analysis(), 0)
        self.assertEqual(tab_index_for_control(), 1)
        self.assertFalse(needs_tab_select(on_tab=True))
        self.assertTrue(needs_tab_select(on_tab=False))


if __name__ == "__main__":
    unittest.main()
