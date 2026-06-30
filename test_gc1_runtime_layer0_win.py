# -*- coding: utf-8 -*-
"""T30 — gc1_runtime.layer0_win (L0-WIN) mock 테스트."""
from __future__ import annotations

import unittest
from unittest.mock import MagicMock

from gc1_runtime.layer0_win import (
    WindowRect,
    WinProbe,
    build_title_re,
    count_handles,
    find_handles,
    is_foreground,
    pick_best_window,
    read_window_rect,
    score_autochro_window,
)


class _FakeRect:
    def __init__(self, left: int, top: int, right: int, bottom: int) -> None:
        self.left = left
        self.top = top
        self.right = right
        self.bottom = bottom

    def width(self) -> int:
        return self.right - self.left

    def height(self) -> int:
        return self.bottom - self.top


def _make_win(
    *,
    visible: bool = True,
    w: int = 1200,
    h: int = 800,
    tree: bool = True,
    listview: bool = True,
    handle: int = 1,
) -> MagicMock:
    win = MagicMock()
    win.handle = handle
    win.is_visible.return_value = visible
    win.rectangle.return_value = _FakeRect(0, 0, w, h)

    def _descendants(class_name: str = "") -> list:
        if class_name == "SysTreeView32":
            return [object()] if tree else []
        if class_name == "SysListView32":
            return [object()] if listview else []
        return []

    win.descendants.side_effect = _descendants
    return win


class TestWinScore(unittest.TestCase):
    def test_full_score(self):
        # 100 + min(1200*800//1000,500)=500 + 200 + 100 = 900
        sc = score_autochro_window(_make_win())
        self.assertEqual(sc, 900)

    def test_minimal_invisible_no_ctrls(self):
        sc = score_autochro_window(
            _make_win(visible=False, w=100, h=100, tree=False, listview=False),
        )
        self.assertEqual(sc, 10)  # area only: 100*100//1000=10


class TestWinFindPick(unittest.TestCase):
    def test_build_title_re_escapes(self):
        self.assertEqual(build_title_re("Autochro-3000"), r".*Autochro\-3000.*")

    def test_find_handles(self):
        found = find_handles(
            "Autochro",
            find_windows=lambda title_re: [101, 102] if "Autochro" in title_re else [],
        )
        self.assertEqual(found, (101, 102))
        self.assertEqual(count_handles(found), 2)

    def test_pick_best_among_two(self):
        wins = {
            1: _make_win(handle=1, tree=False, listview=False, w=400, h=300),
            2: _make_win(handle=2, tree=True, listview=True, w=1200, h=800),
        }
        result = pick_best_window(
            (1, 2),
            connect=lambda h: wins[h],
        )
        self.assertEqual(result.best_handle, 2)
        self.assertGreater(result.best_score, 400)

    def test_single_handle_skips_scoring_loop(self):
        win = _make_win(handle=99)
        result = pick_best_window((99,), connect=lambda _h: win)
        self.assertEqual(result.best_handle, 99)
        self.assertIs(result.best_window, win)

    def test_win_probe_chain(self):
        wins = {5: _make_win(handle=5)}
        probe = WinProbe(
            find_windows=lambda title_re: [5],
            connect=lambda h: wins[h],
        )
        out = probe.probe("X")
        self.assertEqual(out.best_handle, 5)


class TestWinRectForeground(unittest.TestCase):
    def test_read_window_rect(self):
        r = read_window_rect(_make_win(w=100, h=50))
        self.assertEqual(r.width, 100)
        self.assertEqual(r.height, 50)

    def test_window_rect_from_obj(self):
        r = WindowRect.from_obj(_FakeRect(1, 2, 11, 22))
        self.assertEqual((r.left, r.top, r.width, r.height), (1, 2, 10, 20))

    def test_is_foreground_injected(self):
        self.assertTrue(is_foreground(42, foreground_hwnd=42))
        self.assertFalse(is_foreground(42, foreground_hwnd=7))


if __name__ == "__main__":
    unittest.main()
