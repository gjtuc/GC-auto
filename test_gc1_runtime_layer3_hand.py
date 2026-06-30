# -*- coding: utf-8 -*-
"""T40 — gc1_runtime.layer3_hand W32 래퍼·menu matcher 테스트."""
from __future__ import annotations

import unittest
from unittest.mock import MagicMock

from gc1_runtime.layer3_hand import (
    HandActuator,
    hand_click,
    hand_send_keys,
    hand_set_focus,
    matcher_initialize_only,
    matcher_load_analysis_method,
    menu_popup_pick,
)


class TestHandLeafWrappers(unittest.TestCase):
    def test_set_focus(self):
        target = MagicMock()
        hand_set_focus(target)
        target.set_focus.assert_called_once()

    def test_click_with_coords(self):
        target = MagicMock()
        hand_click(target, coords=(10, 20))
        target.click_input.assert_called_once_with(button="left", coords=(10, 20))

    def test_hand_actuator_logs(self):
        hand = HandActuator()
        target = MagicMock(name="list")
        hand.set_focus(target)
        hand.click(target, button="right", coords=(1, 2))
        hand.double_click(target, coords=(3, 4))
        self.assertEqual([r.op for r in hand.log], ["set_focus", "click", "double_click"])

    def test_send_keys_injected(self):
        sent: list[str] = []

        def fake_send(k: str, **_) -> None:
            sent.append(k)

        hand = HandActuator(send_keys_fn=fake_send)
        hand.send_keys("^a")
        hand_send_keys("^p", sender=fake_send)
        self.assertEqual(sent, ["^a", "^p"])


class _FakeMenuWrapper:
    def __init__(self, items: list[str]) -> None:
        self._items = items
        self.clicked: str | None = None

    def menu(self) -> _FakeMenuWrapper:
        return self

    def items(self) -> list[str]:
        return self._items

    def menu_item(self, text: str) -> _FakeMenuWrapper:
        self.clicked = text
        return self

    def click_input(self) -> None:
        pass


class TestMenuPopupPick(unittest.TestCase):
    def test_picks_matching_item(self):
        menu = _FakeMenuWrapper(["취소", "초기화", "초기화+정량"])
        result = menu_popup_pick(
            matcher_initialize_only(),
            get_wrappers=lambda: [menu],
            clock=lambda: 0.0,
            sleep=lambda _s: None,
            timeout=1.0,
        )
        self.assertEqual(result.matched_text, "초기화")
        self.assertEqual(menu.clicked, "초기화")

    def test_raises_when_not_found(self):
        menu = _FakeMenuWrapper(["저장"])
        tick = {"t": 0.0}

        def clock() -> float:
            return tick["t"]

        def sleep(sec: float) -> None:
            tick["t"] += sec

        with self.assertRaises(RuntimeError) as ctx:
            menu_popup_pick(
                matcher_load_analysis_method(),
                get_wrappers=lambda: [menu],
                clock=clock,
                sleep=sleep,
                timeout=0.01,
                poll_interval=0.01,
            )
        self.assertIn("seen:", str(ctx.exception))

    def test_matcher_load_analysis_method(self):
        m = matcher_load_analysis_method()
        self.assertTrue(m("분석방법 불러오기"))
        self.assertFalse(m("초기화"))

    def test_hand_actuator_menu_item_click(self):
        hand = HandActuator()
        wrapper = MagicMock()
        hand.menu_item_click(wrapper, "확인")
        wrapper.menu_item.assert_called_once_with("확인")
        wrapper.menu_item.return_value.click_input.assert_called_once()


if __name__ == "__main__":
    unittest.main()
