# -*- coding: utf-8 -*-
"""
L0 컨트롤 프로브 — LV / LV-PICK / TR / TAB (Ω.A.L0.LV.*, LVP.*, TR.*, TAB.*).

``gc_autochro`` 의 ``_sample_table_candidates``, ``_pick_listview``,
``_analysis_tree_view``, ``_on_*_tab`` geometry·판별 로직 이전 (T31).
W32 조작(click/select) 은 L3 — 여기서는 **읽기·geometry·선택** 만.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal, Sequence

from gc1_runtime.layer0_win import WindowRect

Prefer = Literal["lower", "upper", "any"]
Purpose = Literal["control", "analysis", "제어목록", "분석목록"]

_MIN_LIST_H = 60
_MIN_LIST_W = 180
_MIN_WIN_H = 200
_LOWER_FRAC_MIN = 0.30
_UPPER_FRAC_MAX = 0.72


@dataclass(frozen=True)
class ListViewGeom:
    """ListView 후보 — mock·실제 ctrl 대신 geometry 단위 테스트용."""

    top: int
    bottom: int
    left: int
    right: int
    item_count: int
    ctrl_id: int = 0

    @property
    def height(self) -> int:
        return self.bottom - self.top

    @property
    def width(self) -> int:
        return self.right - self.left


@dataclass(frozen=True)
class TreeGeom:
    """SysTreeView32 후보 geometry."""

    top: int
    bottom: int
    left: int
    right: int
    ctrl_id: int = 0


def relative_mid_y(geom_top: int, geom_bottom: int, win_rect: WindowRect | None) -> float:
    """Ω.A.L0.LV.02f — 창 기준 세로 중앙 비율."""
    win_h = max(win_rect.height, _MIN_WIN_H) if win_rect else _MIN_WIN_H
    if win_rect is None:
        return 0.5
    mid = (geom_top + geom_bottom) / 2.0
    return (mid - win_rect.top) / win_h


def listview_passes_size(geom: ListViewGeom) -> bool:
    """Ω.A.L0.LV.02c~02e — n>0, h>=60, w>=180."""
    return (
        geom.item_count > 0
        and geom.height >= _MIN_LIST_H
        and geom.width >= _MIN_LIST_W
    )


def listview_matches_prefer(frac: float, prefer: Prefer) -> bool:
    """Ω.A.L0.LV.02g~02h — lower/upper 영역 필터."""
    if prefer == "lower" and frac < _LOWER_FRAC_MIN:
        return False
    if prefer == "upper" and frac > _UPPER_FRAC_MAX:
        return False
    return True


def filter_listview_candidates(
    items: Sequence[ListViewGeom],
    win_rect: WindowRect | None,
    *,
    prefer: Prefer = "any",
) -> list[ListViewGeom]:
    """
    Ω.A.L0.LV.01~03 — ``_sample_table_candidates`` 와 동일.

    prefer 로 후보 없으면 ``any`` 로 재귀 (Ω.A.L0.LV.03).
    """
    out: list[ListViewGeom] = []
    for geom in items:
        if not listview_passes_size(geom):
            continue
        frac = relative_mid_y(geom.top, geom.bottom, win_rect)
        if not listview_matches_prefer(frac, prefer):
            continue
        out.append(geom)
    if not out and prefer != "any":
        return filter_listview_candidates(items, win_rect, prefer="any")
    return out


def listview_pick_score(
    geom: ListViewGeom,
    win_rect: WindowRect | None,
    *,
    purpose: Purpose,
) -> float:
    """
    Ω.A.L0.LVP.01~03 — item_count + vertical bias.

    제어목록: count + frac*50 / 분석목록: count - frac*10 (``gc_autochro`` 동일).
    """
    frac = relative_mid_y(geom.top, geom.bottom, win_rect)
    if purpose in ("control", "제어목록"):
        return geom.item_count + frac * 50.0
    return geom.item_count - frac * 10.0


def pick_best_listview(
    items: Sequence[ListViewGeom],
    win_rect: WindowRect | None,
    *,
    prefer: Prefer,
    purpose: Purpose,
) -> ListViewGeom:
    """Ω.A.L0.LVP.04 — argmax score."""
    candidates = filter_listview_candidates(items, win_rect, prefer=prefer)
    if not candidates:
        label = purpose if isinstance(purpose, str) else "listview"
        raise RuntimeError(f"{label} 시료 표를 찾지 못함")
    scored = [
        (listview_pick_score(g, win_rect, purpose=purpose), g) for g in candidates
    ]
    return max(scored, key=lambda pair: pair[0])[1]


def pick_control_sync_list(
    items: Sequence[ListViewGeom],
    win_rect: WindowRect | None,
) -> ListViewGeom:
    """제어목록 하단 표 — ``_control_sync_list``."""
    return pick_best_listview(items, win_rect, prefer="lower", purpose="제어목록")


def pick_analysis_sample_table(
    items: Sequence[ListViewGeom],
    win_rect: WindowRect | None,
) -> ListViewGeom:
    """분석목록 상단 표 — ``_analysis_sample_table``."""
    return pick_best_listview(items, win_rect, prefer="upper", purpose="분석목록")


def tree_is_left_panel(geom: TreeGeom, win_rect: WindowRect | None) -> bool:
    """Ω.A.L0.TR.02 — 왼쪽 절반 (rel_left <= 50% width)."""
    if win_rect is None:
        return True
    rel_left = geom.left - win_rect.left
    return rel_left <= win_rect.width * 0.5


def pick_analysis_tree(
    trees: Sequence[TreeGeom],
    win_rect: WindowRect | None,
) -> TreeGeom:
    """Ω.A.L0.TR.01~03 — ``_analysis_tree_view`` 첫 왼쪽 트리."""
    for geom in trees:
        if tree_is_left_panel(geom, win_rect):
            return geom
    raise RuntimeError("분석목록 왼쪽 트리 없음")


def menu_texts_include_analysis(menu_texts: Sequence[str]) -> bool:
    """Ω.A.L0.TAB.03 — 메뉴에 「분석목록」."""
    return any("분석목록" in text for text in menu_texts)


def menu_texts_include_control(menu_texts: Sequence[str]) -> bool:
    """Ω.A.L0.TAB.04 — 메뉴에 「제어목록」."""
    return any("제어목록" in text for text in menu_texts)


def tab_index_for_control() -> int:
    """Ω.A.L0.TAB.02 — 제어목록 = bottom tab index 1."""
    return 1


def tab_index_for_analysis() -> int:
    """Ω.A.L0.TAB.01 — 분석목록 = bottom tab index 0."""
    return 0


def needs_tab_select(*, on_tab: bool) -> bool:
    """TAB.01/04 — 이미 해당 탭이면 select 생략."""
    return not on_tab
