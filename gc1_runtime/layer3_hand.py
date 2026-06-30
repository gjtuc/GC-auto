# -*- coding: utf-8 -*-
"""
L3 Hand 채널 (Ω.A.L3.H.*) — W32/pywinauto **의미 1회** 래퍼.

설계 §L3 H.02, H.05~H.08, H.10 — ``gc_autochro`` 의 set_focus / click / send_keys /
``_click_popup_menu_item`` 분리 (T40). WAIT(sleep) 은 호출부·L4 atom.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any, Callable, Iterable, Sequence

MenuMatcher = Callable[[str], bool]
ClockFn = Callable[[], float]
SleepFn = Callable[[float], None]
SendKeysFn = Callable[..., None]
MenuWrapperProvider = Callable[[], Sequence[Any]]


@dataclass
class MenuPopupResult:
    """menu_popup_pick 성공 결과."""

    matched_text: str
    seen_items: tuple[str, ...] = ()


@dataclass
class HandActionRecord:
    """단위 테스트·dry-run 용 마지막 동작 기록."""

    op: str
    detail: str = ""


@dataclass
class HandActuator:
    """
    Hand leaf 묶음 — target 은 pywinauto wrapper mock 가능.

    ``log`` 에 op 기록 시 dry-run·테스트에서 호출 추적.
    """

    log: list[HandActionRecord] = field(default_factory=list)
    send_keys_fn: SendKeysFn | None = None

    def _record(self, op: str, detail: str = "") -> None:
        self.log.append(HandActionRecord(op=op, detail=detail))

    def set_focus(self, target: Any) -> None:
        """H.02 — ``set_focus()`` 1회."""
        target.set_focus()
        self._record("set_focus", getattr(target, "name", repr(target)))

    def click(
        self,
        target: Any,
        *,
        button: str = "left",
        coords: tuple[int, int] | None = None,
    ) -> None:
        """H.05(left) / H.06(right) — ``click_input`` 1회."""
        if coords is not None:
            target.click_input(button=button, coords=coords)
        else:
            target.click_input(button=button)
        self._record("click", f"{button} coords={coords}")

    def double_click(self, target: Any, *, coords: tuple[int, int]) -> None:
        """H.07 — ``double_click_input`` 1회."""
        target.double_click_input(coords=coords)
        self._record("double_click", f"coords={coords}")

    def send_keys(self, keys: str, **kwargs: Any) -> None:
        """H.08 — 키보드 입력 1회 (기본 pywinauto.keyboard.send_keys)."""
        sender = self.send_keys_fn or _default_send_keys
        sender(keys, **kwargs)
        self._record("send_keys", keys)

    def type_keys(self, target: Any, keys: str) -> None:
        """H.12 — 대상에 ``type_keys`` 1회."""
        target.type_keys(keys)
        self._record("type_keys", keys)

    def menu_item_click(self, menu_wrapper: Any, text: str) -> None:
        """H.10 — popup ``menu_item(text).click_input()`` 1회."""
        menu_wrapper.menu_item(text).click_input()
        self._record("menu_item_click", text)


def hand_set_focus(target: Any) -> None:
    """모듈 수준 H.02 — HandActuator 없이 1 leaf."""
    target.set_focus()


def hand_click(
    target: Any,
    *,
    button: str = "left",
    coords: tuple[int, int] | None = None,
) -> None:
    """모듈 수준 H.05/H.06."""
    if coords is not None:
        target.click_input(button=button, coords=coords)
    else:
        target.click_input(button=button)


def hand_send_keys(keys: str, *, sender: SendKeysFn | None = None, **kwargs: Any) -> None:
    """모듈 수준 H.08."""
    fn = sender or _default_send_keys
    fn(keys, **kwargs)


def _iter_menu_texts(wrapper: Any) -> Iterable[str]:
    for item in wrapper.menu().items():
        yield item if isinstance(item, str) else str(item)


def _default_popup_wrappers() -> list[Any]:
    from pywinauto import Desktop  # noqa: PLC0415 — win32 only

    wrappers: list[Any] = []
    for menu_win in Desktop(backend="win32").windows(class_name="#32768"):
        try:
            wrappers.append(menu_win.wrapper_object())
        except Exception:
            continue
    return wrappers


def _default_send_keys(keys: str, **kwargs: Any) -> None:
    from pywinauto.keyboard import send_keys  # noqa: PLC0415

    send_keys(keys, **kwargs)


def menu_popup_pick(
    matcher: MenuMatcher,
    *,
    get_wrappers: MenuWrapperProvider | None = None,
    clock: ClockFn = time.time,
    sleep: SleepFn = time.sleep,
    timeout: float = 5.0,
    poll_interval: float = 0.12,
) -> MenuPopupResult:
    """
    H.10 + Desktop #32768 — ``_click_popup_menu_item`` 와 동일 matcher 계약.

    ``get_wrappers`` 주입으로 pywinauto 없이 단위 테스트.
  """
    provider = get_wrappers or _default_popup_wrappers
    deadline = clock() + timeout
    seen: list[str] = []
    while clock() < deadline:
        for wrapper in provider():
            try:
                for text in _iter_menu_texts(wrapper):
                    seen.append(text)
                    if matcher(text):
                        wrapper.menu_item(text).click_input()
                        return MenuPopupResult(
                            matched_text=text,
                            seen_items=tuple(seen),
                        )
            except Exception:
                continue
        sleep(poll_interval)
    preview = ", ".join(seen[:10])
    raise RuntimeError(f"컨텍스트 메뉴 항목 없음 (seen: {preview})")


def matcher_initialize_only() -> MenuMatcher:
    """P3.04 — 초기화(정량·검량 제외)."""
    return lambda t: "초기화" in t and "정량" not in t and "검량" not in t


def matcher_load_analysis_method() -> MenuMatcher:
    """P4.05 — 분석방법 불러오기."""
    return lambda t: "분석방법" in t and "불러" in t
