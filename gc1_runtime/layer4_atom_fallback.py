# -*- coding: utf-8 -*-
"""
gc1_runtime.layer4_atom_fallback — L4 atom retry ``fallback_channel`` 실행 (T92)

``run_atom_shell`` 재시도 직전 호출 — PART6 표 H/E/F 채널 보조 동작.
"""
from __future__ import annotations

from typing import Any, TYPE_CHECKING

from gc1_runtime.layer0_ctl import ListViewGeom, pick_analysis_sample_table
from gc1_runtime.layer0_fallback import parse_fallback_channel
from gc1_runtime.layer4_atoms_p2_p3 import neutral_list_coords

if TYPE_CHECKING:
    from gc1_runtime.layer4_atoms_p0_p1 import AtomContext


def _sample_geom(ctx: "AtomContext") -> ListViewGeom:
    if ctx.deps.listview_geoms:
        return pick_analysis_sample_table(ctx.deps.listview_geoms, ctx.deps.win_rect)
    return ListViewGeom(top=100, bottom=280, left=20, right=420, item_count=8)


def apply_atom_fallback(
    ctx: "AtomContext",
    fallback_channel: str,
    *,
    atom_id: str = "",
) -> dict[str, Any]:
    """
    재시도 전 fallback 1회 — probe_snapshot 에 ``fallback_*`` 기록.

    ``atom_id`` — P6 vs P3 메뉴 초기화 분기용.
    """
    kind = parse_fallback_channel(fallback_channel)
    if kind is None:
        return {"fallback_skipped": True, "fallback_channel": fallback_channel}

    hand = ctx.deps.hand
    snap: dict[str, Any] = {"fallback_kind": kind, "fallback_channel": fallback_channel}

    if kind == "h_reclick_neutral":
        geom = _sample_geom(ctx)
        x_frac = getattr(ctx.deps, "list_neutral_x_frac", 0.78)
        rel_x, rel_y = neutral_list_coords(geom.width, geom.height, x_frac=x_frac)
        hand._record("set_focus", "analysis_sample")
        hand._record("click", f"{rel_x},{rel_y}")
        if hasattr(ctx.deps, "sample_list_focused"):
            ctx.deps.sample_list_focused = True  # type: ignore[attr-defined]
        snap.update({"rel_x": rel_x, "rel_y": rel_y})

    elif kind == "h_resend_ctrl_a":
        hand.send_keys("^a")
        if hasattr(ctx.deps, "ctrl_a_sent"):
            ctx.deps.ctrl_a_sent = True  # type: ignore[attr-defined]
        snap["keys"] = "^a"

    elif kind == "e_eye_menu_init":
        if "P6" in atom_id:
            from gc1_runtime.layer4_atoms_p5_p7 import gpost_retry_p6_04

            snap.update(gpost_retry_p6_04(ctx))
        else:
            from gc1_runtime.layer4_atoms_p2_p3 import gpost_retry_p3_04

            snap.update(gpost_retry_p3_04(ctx))

    elif kind == "f_send_keys_open":
        hand.send_keys("%o")
        snap["keys"] = "%o"

    elif kind == "send_keys_enter":
        hand.send_keys("{ENTER}")
        snap["keys"] = "{ENTER}"

    elif kind == "send_keys_alt_s":
        hand.send_keys("%s")
        snap["keys"] = "%s"

    else:
        snap["fallback_unknown"] = kind

    return snap
