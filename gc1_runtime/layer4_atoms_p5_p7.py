# -*- coding: utf-8 -*-
"""
L4 원자 — P5~P6 (P2/P3 재사용) + P7 initialize_quantify (T53).

설계 ``deploy/GC1_RUNTIME_DESIGN_PART2_L4_P5_P9.md`` §P5.01~P7.05.
P5≈P2 select_all, P6≈P3 context_initialize, P7=``step_initialize_quantify`` leaf 분리.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable, Sequence

from gc1_runtime.layer0_ctl import (
    ListViewGeom,
    menu_texts_include_analysis,
    pick_analysis_sample_table,
    tab_index_for_analysis,
)
from gc1_runtime.layer0_config import read_quantify_wait_sec
from gc1_runtime.layer1_state import AtomRecord, AtomStatus, JobState, StateStore
from gc1_runtime.layer2_gates import GateEvaluator
from gc1_runtime.layer3_eye import evaluate_peak_table_task
from gc1_runtime.layer3_hand import matcher_initialize_only, menu_popup_pick
from gc1_runtime.layer4_atoms_p0_p1 import (
    AtomContext,
    AtomOutcome,
    AtomSpec,
    PhaseOutcome,
    _spec,
    run_atom_shell,
)
from gc1_runtime.layer4_atoms_p2_p3 import (
    P2P3Deps,
    _FakePopupMenu,
    neutral_list_coords,
)
from gc1_runtime.layer4_atoms_p4 import P4Deps, P0_P4_ATOM_IDS, _phase_blocked_early_ok

ClockFn = Callable[[], float]
SleepFn = Callable[[float], None]
ProgressVisibleFn = Callable[[], bool]

# ---------------------------------------------------------------------------
# Atom registry
# ---------------------------------------------------------------------------

P5_ATOM_IDS: tuple[str, ...] = (
    "Ω.A.L4.P5.01",
    "Ω.A.L4.P5.02",
    "Ω.A.L4.P5.03",
    "Ω.A.L4.P5.04",
    "Ω.A.L4.P5.05",
)

P6_ATOM_IDS: tuple[str, ...] = (
    "Ω.A.L4.P6.01",
    "Ω.A.L4.P6.02",
    "Ω.A.L4.P6.03",
    "Ω.A.L4.P6.04",
    "Ω.A.L4.P6.05",
    "Ω.A.L4.P6.06",
)

P7_ATOM_IDS: tuple[str, ...] = (
    "Ω.A.L4.P7.01",
    "Ω.A.L4.P7.02",
    "Ω.A.L4.P7.03",
    "Ω.A.L4.P7.04",
    "Ω.A.L4.P7.05",
)

P5_P7_ATOM_IDS: tuple[str, ...] = P5_ATOM_IDS + P6_ATOM_IDS + P7_ATOM_IDS
P0_P7_ATOM_IDS: tuple[str, ...] = P0_P4_ATOM_IDS + P5_P7_ATOM_IDS

P5_P7_ATOM_SPECS: dict[str, AtomSpec] = {
    "Ω.A.L4.P5.01": _spec("Ω.A.L4.P5.01", "H", timeout_ms=10000),
    "Ω.A.L4.P5.02": _spec("Ω.A.L4.P5.02", "H", timeout_ms=10000),
    "Ω.A.L4.P5.03": _spec(
        "Ω.A.L4.P5.03", "H", code="E_P2_FOCUS", max_attempt=3, retry_delay_ms=500,
        fallback_channel="H re-click neutral", timeout_ms=15000,
    ),
    "Ω.A.L4.P5.04": _spec(
        "Ω.A.L4.P5.04", "H", code="E_P2_SELECT", max_attempt=2, retry_delay_ms=300,
        fallback_channel="H resend ^a", timeout_ms=5000,
    ),
    "Ω.A.L4.P5.05": _spec("Ω.A.L4.P5.05", "W", timeout_ms=1000),
    "Ω.A.L4.P6.01": _spec("Ω.A.L4.P6.01", "H", timeout_ms=10000),
    "Ω.A.L4.P6.02": _spec("Ω.A.L4.P6.02", "H", timeout_ms=10000),
    "Ω.A.L4.P6.03": _spec("Ω.A.L4.P6.03", "H", timeout_ms=10000),
    "Ω.A.L4.P6.04": _spec(
        "Ω.A.L4.P6.04", "H", code="E_P3_MENU", max_attempt=3, retry_delay_ms=120,
        fallback_channel="E eye click 초기화", timeout_ms=20000,
    ),
    "Ω.A.L4.P6.05": _spec("Ω.A.L4.P6.05", "W", timeout_ms=2000),
    "Ω.A.L4.P6.06": _spec("Ω.A.L4.P6.06", "E", code="E_VERIFY_PEAK", timeout_ms=30000),
    "Ω.A.L4.P7.01": _spec("Ω.A.L4.P7.01", "H", timeout_ms=30000),
    "Ω.A.L4.P7.02": _spec(
        "Ω.A.L4.P7.02", "H", code="E_P7_MENU", max_attempt=2, retry_delay_ms=500, timeout_ms=20000,
    ),
    "Ω.A.L4.P7.03": _spec("Ω.A.L4.P7.03", "W", timeout_ms=4000),
    "Ω.A.L4.P7.04": _spec("Ω.A.L4.P7.04", "W", timeout_ms=120000),
    "Ω.A.L4.P7.05": _spec("Ω.A.L4.P7.05", "E", code="E_VERIFY_PEAK", timeout_ms=30000),
}

@dataclass
class P57Deps(P4Deps):
    """
    P5~P7 dry-run·live 주입.

    ``peak_table_after_quantify`` — P7.05 TASK verify.
    ``progress_visible`` — P7.04 폴링 mock (False = 적분 완료).
    ``top_menu_items`` — P7.02 시료목록→초기화+정량 mock.
    """

    peak_table_after_quantify: str = "0.12 3.45 5.6"
    peak_table_after_p6: str = "0 0 0 0 0"
    quantify_wait_sec: int = 180
    quantify_menu_selected: bool = False
    progress_visible: ProgressVisibleFn = field(default=lambda: False)
    top_menu_items: list[dict[str, Any]] = field(
        default_factory=lambda: [
            {
                "text": "시료목록(T)",
                "menu_items": {"menu_items": [{"text": "초기화+정량"}]},
            },
        ],
    )


# ---------------------------------------------------------------------------
# PURE — 상단 메뉴·정량 progress (gc_autochro)
# ---------------------------------------------------------------------------


def top_menu_has_item(
    menu_items: Sequence[dict[str, Any]],
    top_suffix: str,
    item_text: str,
) -> bool:
    """P7.02 — ``_menu_select_by_suffix`` 탐색 (dict mock)."""
    for top in menu_items:
        if not isinstance(top, dict):
            continue
        top_text = str(top.get("text", ""))
        if top_suffix not in top_text:
            continue
        subs = top.get("menu_items") or {}
        if isinstance(subs, dict):
            sub_list = subs.get("menu_items") or []
        else:
            sub_list = subs
        for sub in sub_list:
            if not isinstance(sub, dict):
                continue
            sub_text = str(sub.get("text", ""))
            if sub_text == item_text or sub_text.startswith(item_text):
                return True
    return False


def poll_quantify_progress_done(
    *,
    is_progress_visible: ProgressVisibleFn,
    clock: ClockFn,
    sleep: SleepFn,
    max_wait_sec: float,
    poll_sec: float = 1.0,
    initial_sleep_sec: float = 3.0,
) -> tuple[bool, int]:
    """
    P7.04 — ``step_initialize_quantify`` progress 루프.

    progress 창이 사라지고 시작 후 5초 경과 시 완료.
  """
    sleep(initial_sleep_sec)
    loop_start = clock()
    deadline = loop_start + max_wait_sec
    polls = 0
    while clock() < deadline:
        polls += 1
        if not is_progress_visible():
            if clock() > loop_start + 5.0:
                return True, polls
        sleep(poll_sec)
    return not is_progress_visible(), polls


# ---------------------------------------------------------------------------
# Shared UI helpers (P2/P3/P5/P6/P7.01)
# ---------------------------------------------------------------------------


def _menu_texts(ctx: AtomContext) -> Sequence[str]:
    if ctx.deps.on_analysis_tab:
        return ("분석목록", "제어목록")
    if ctx.deps.on_control_tab:
        return ("제어목록", "분석목록")
    return ("제어목록", "분석목록")


def _select_analysis_tab_deps(ctx: AtomContext) -> None:
    if not menu_texts_include_analysis(_menu_texts(ctx)):
        ctx.deps.on_analysis_tab = True
        ctx.deps.on_control_tab = False
    if not ctx.deps.dry_run and ctx.deps.live_win is not None:
        tabs = ctx.deps.live_win.child_window(class_name="SysTabControl32", title="Tab1")
        tabs.select(tab_index_for_analysis())
    ctx.deps.hand._record("tabs.select", str(tab_index_for_analysis()))


def _analysis_sample_geom(ctx: AtomContext) -> ListViewGeom:
    if ctx.deps.listview_geoms:
        return pick_analysis_sample_table(ctx.deps.listview_geoms, ctx.deps.win_rect)
    return ListViewGeom(top=100, bottom=280, left=20, right=420, item_count=8)


def _popup_wrappers(deps: P2P3Deps) -> list[_FakePopupMenu]:
    return [_FakePopupMenu(deps.menu_popup_items)]


def _atom_id_from_runner(runner: Callable[[AtomContext], AtomOutcome]) -> str:
    parts = runner.__name__.split("_")
    return f"Ω.A.L4.{parts[2].upper()}.{parts[3]}"


def _execute_select_all_leaves(ctx: AtomContext, deps: P57Deps) -> dict[str, Any]:
    """P2.01~05 / P7.01 action leaf 묶음."""
    block_start = ctx.deps.clock()
    _select_analysis_tab_deps(ctx)
    ctx.deps.sleep(0.8)
    geom = _analysis_sample_geom(ctx)
    rel_x, rel_y = neutral_list_coords(
        geom.width, geom.height, x_frac=deps.list_neutral_x_frac,
    )
    deps.sample_list_focused = True
    ctx.deps.hand._record("set_focus", "analysis_sample")
    ctx.deps.hand._record("click", f"{rel_x},{rel_y}")
    ctx.deps.hand.send_keys("^a")
    deps.ctrl_a_sent = True
    ctx.deps.sleep(0.5)
    return {
        "ctrl_a_sent": deps.ctrl_a_sent,
        "elapsed_sec": ctx.deps.clock() - block_start,
        "items": geom.item_count,
    }


# ---------------------------------------------------------------------------
# P5 — select_all (2차, P2 재사용)
# ---------------------------------------------------------------------------


def _run_p5_01(ctx: AtomContext) -> AtomOutcome:
    def act() -> dict[str, Any]:
        _select_analysis_tab_deps(ctx)
        ctx.deps.sleep(0.8)
        return {"tab": "analysis"}

    def post(_snapshot: dict[str, Any]) -> tuple[bool, ...]:
        return (menu_texts_include_analysis(_menu_texts(ctx)),)

    return run_atom_shell(
        ctx, P5_P7_ATOM_SPECS["Ω.A.L4.P5.01"],
        pre_probes=(ctx.prior_ok("Ω.A.L4.P4.08"),),
        act=act, post_probes=post,
    )


def _run_p5_02(ctx: AtomContext) -> AtomOutcome:
    def act() -> dict[str, Any]:
        geom = _analysis_sample_geom(ctx)
        return {"items": geom.item_count, "_geom_ok": geom.item_count > 0}

    def post(snapshot: dict[str, Any]) -> tuple[bool, ...]:
        return (bool(snapshot.get("_geom_ok")),)

    return run_atom_shell(
        ctx, P5_P7_ATOM_SPECS["Ω.A.L4.P5.02"],
        pre_probes=(menu_texts_include_analysis(_menu_texts(ctx)),),
        act=act, post_probes=post,
    )


def _run_p5_03(ctx: AtomContext) -> AtomOutcome:
    deps: P57Deps = ctx.deps  # type: ignore[assignment]

    def act() -> dict[str, Any]:
        geom = _analysis_sample_geom(ctx)
        rel_x, rel_y = neutral_list_coords(
            geom.width, geom.height, x_frac=deps.list_neutral_x_frac,
        )
        deps.sample_list_focused = True
        ctx.deps.hand._record("set_focus", "analysis_sample")
        ctx.deps.hand._record("click", f"{rel_x},{rel_y}")
        return {"focused": True, "rel_x": rel_x, "rel_y": rel_y}

    def post(snapshot: dict[str, Any]) -> tuple[bool, ...]:
        return (snapshot.get("focused") is True,)

    return run_atom_shell(
        ctx, P5_P7_ATOM_SPECS["Ω.A.L4.P5.03"],
        pre_probes=(ctx.prior_ok("Ω.A.L4.P5.02"),),
        act=act, post_probes=post,
    )


def _run_p5_04(ctx: AtomContext) -> AtomOutcome:
    deps: P57Deps = ctx.deps  # type: ignore[assignment]

    def act() -> dict[str, Any]:
        ctx.deps.hand.send_keys("^a")
        deps.ctrl_a_sent = True
        return {"keys": "^a"}

    def post(_snapshot: dict[str, Any]) -> tuple[bool, ...]:
        return (deps.ctrl_a_sent,)

    return run_atom_shell(
        ctx, P5_P7_ATOM_SPECS["Ω.A.L4.P5.04"],
        pre_probes=(ctx.prior_ok("Ω.A.L4.P5.03"),),
        act=act, post_probes=post,
    )


def _run_p5_05(ctx: AtomContext) -> AtomOutcome:
    start = ctx.deps.clock()

    def act() -> dict[str, Any]:
        ctx.deps.sleep(0.5)
        return {"elapsed_sec": ctx.deps.clock() - start}

    def post(snapshot: dict[str, Any]) -> tuple[bool, ...]:
        return (float(snapshot.get("elapsed_sec", 0)) >= 0.499,)

    return run_atom_shell(
        ctx, P5_P7_ATOM_SPECS["Ω.A.L4.P5.05"],
        pre_probes=(ctx.prior_ok("Ω.A.L4.P5.04"),),
        act=act, post_probes=post,
    )


# ---------------------------------------------------------------------------
# P6 — context_initialize (2차, P3 재사용)
# ---------------------------------------------------------------------------


def _run_p6_01(ctx: AtomContext) -> AtomOutcome:
    def act() -> dict[str, Any]:
        _select_analysis_tab_deps(ctx)
        return {"tab": "analysis"}

    def post(_snapshot: dict[str, Any]) -> tuple[bool, ...]:
        return (menu_texts_include_analysis(_menu_texts(ctx)),)

    return run_atom_shell(
        ctx, P5_P7_ATOM_SPECS["Ω.A.L4.P6.01"],
        pre_probes=(ctx.prior_ok("Ω.A.L4.P5.05"),),
        act=act, post_probes=post,
    )


def _run_p6_02(ctx: AtomContext) -> AtomOutcome:
    def act() -> dict[str, Any]:
        geom = _analysis_sample_geom(ctx)
        return {"items": geom.item_count, "_geom_ok": geom.item_count > 0}

    def post(snapshot: dict[str, Any]) -> tuple[bool, ...]:
        return (bool(snapshot.get("_geom_ok")),)

    return run_atom_shell(
        ctx, P5_P7_ATOM_SPECS["Ω.A.L4.P6.02"],
        pre_probes=(menu_texts_include_analysis(_menu_texts(ctx)),),
        act=act, post_probes=post,
    )


def _run_p6_03(ctx: AtomContext) -> AtomOutcome:
    def act() -> dict[str, Any]:
        geom = _analysis_sample_geom(ctx)
        rel_x, rel_y = neutral_list_coords(geom.width, geom.height)
        ctx.deps.hand._record("click", f"right:{rel_x},{rel_y}")
        return {"rclick": True}

    def post(snapshot: dict[str, Any]) -> tuple[bool, ...]:
        return (snapshot.get("rclick") is True,)

    return run_atom_shell(
        ctx, P5_P7_ATOM_SPECS["Ω.A.L4.P6.03"],
        pre_probes=(ctx.prior_ok("Ω.A.L4.P6.02"),),
        act=act, post_probes=post,
    )


def gpost_retry_p6_04(ctx: AtomContext) -> dict[str, Any]:
    """G-POST (T91) — P6.04 초기화 메뉴 재클릭 (P6.06 cleared TASK)."""
    deps: P57Deps = ctx.deps  # type: ignore[assignment]
    result = menu_popup_pick(
        matcher_initialize_only(),
        get_wrappers=lambda: _popup_wrappers(deps),
        clock=deps.clock,
        sleep=deps.sleep,
        timeout=2.0,
    )
    deps.context_menu_clicked = True
    return {"menu": result.matched_text, "gpost_retry": "P6.04"}


def _run_p6_04(ctx: AtomContext) -> AtomOutcome:
    deps: P57Deps = ctx.deps  # type: ignore[assignment]

    def act() -> dict[str, Any]:
        result = menu_popup_pick(
            matcher_initialize_only(),
            get_wrappers=lambda: _popup_wrappers(deps),
            clock=deps.clock,
            sleep=deps.sleep,
            timeout=2.0,
        )
        deps.context_menu_clicked = True
        return {"menu": result.matched_text}

    def post(snapshot: dict[str, Any]) -> tuple[bool, ...]:
        return (bool(snapshot.get("menu")), deps.context_menu_clicked)

    return run_atom_shell(
        ctx, P5_P7_ATOM_SPECS["Ω.A.L4.P6.04"],
        pre_probes=(ctx.prior_ok("Ω.A.L4.P6.03"),),
        act=act, post_probes=post,
    )


def _run_p6_05(ctx: AtomContext) -> AtomOutcome:
    start = ctx.deps.clock()

    def act() -> dict[str, Any]:
        ctx.deps.sleep(0.8)
        return {"elapsed_sec": ctx.deps.clock() - start}

    def post(snapshot: dict[str, Any]) -> tuple[bool, ...]:
        return (float(snapshot.get("elapsed_sec", 0)) >= 0.799,)

    return run_atom_shell(
        ctx, P5_P7_ATOM_SPECS["Ω.A.L4.P6.05"],
        pre_probes=(ctx.prior_ok("Ω.A.L4.P6.04"),),
        act=act, post_probes=post,
    )


def _run_p6_06(ctx: AtomContext) -> AtomOutcome:
    deps: P57Deps = ctx.deps  # type: ignore[assignment]
    from gc1_runtime.layer0_gpost import GPostRetryPlan, run_gpost_eye_verify

    p6_plan = GPostRetryPlan(
        task_id="verify_peak_table_cleared",
        retry_atom_id="Ω.A.L4.P6.04",
        fail_code="E_VERIFY_PEAK",
    )

    def evaluate() -> tuple[bool, dict[str, Any]]:
        verdict = evaluate_peak_table_task(
            verify_eye=deps.verify_eye,
            dry_run=deps.dry_run,
            task_id="verify_peak_table_cleared",
            fallback_text=deps.peak_table_after_p6,
            eye=deps.eye,
            text_provider=deps.peak_table_text_provider,
        )
        return verdict.passed, {"verify_eye": deps.verify_eye, "task_detail": verdict.detail}

    def act() -> dict[str, Any]:
        gpost = run_gpost_eye_verify(
            task_id="verify_peak_table_cleared",
            evaluate=evaluate,
            retry_fn=lambda: gpost_retry_p6_04(ctx),
            sleep_fn=deps.sleep,
            plan=p6_plan,
        )
        return {**gpost.probe_snapshot, "peak_cleared": gpost.passed}

    def post(snapshot: dict[str, Any]) -> tuple[bool, ...]:
        return (snapshot.get("peak_cleared") is True,)

    return run_atom_shell(
        ctx, P5_P7_ATOM_SPECS["Ω.A.L4.P6.06"],
        pre_probes=(ctx.prior_ok("Ω.A.L4.P6.05"),),
        act=act, post_probes=post,
    )


# ---------------------------------------------------------------------------
# P7 — initialize_quantify
# ---------------------------------------------------------------------------


def _run_p7_01(ctx: AtomContext) -> AtomOutcome:
    deps: P57Deps = ctx.deps  # type: ignore[assignment]

    def act() -> dict[str, Any]:
        snap = _execute_select_all_leaves(ctx, deps)
        return snap

    def post(snapshot: dict[str, Any]) -> tuple[bool, ...]:
        return (
            snapshot.get("ctrl_a_sent") is True,
            float(snapshot.get("elapsed_sec", 0)) >= 0.499,
        )

    return run_atom_shell(
        ctx, P5_P7_ATOM_SPECS["Ω.A.L4.P7.01"],
        pre_probes=(ctx.prior_ok("Ω.A.L4.P6.06"),),
        act=act, post_probes=post,
    )


def _run_p7_02(ctx: AtomContext) -> AtomOutcome:
    deps: P57Deps = ctx.deps  # type: ignore[assignment]

    def act() -> dict[str, Any]:
        if deps.dry_run:
            if not top_menu_has_item(deps.top_menu_items, "시료목록", "초기화+정량"):
                raise RuntimeError("메뉴 없음: 시료목록 -> 초기화+정량")
            ctx.deps.hand._record("menu_select", "시료목록(T)->초기화+정량")
            deps.quantify_menu_selected = True
            return {"menu": "초기화+정량"}
        if deps.live_win is None:
            raise RuntimeError("live_win not set")
        from gc_autochro import _menu_select_by_suffix  # noqa: PLC2701

        _select_analysis_tab_deps(ctx)
        _menu_select_by_suffix(deps.live_win, "시료목록", "초기화+정량")
        deps.quantify_menu_selected = True
        return {"menu": "초기화+정량"}

    def post(_snapshot: dict[str, Any]) -> tuple[bool, ...]:
        return (deps.quantify_menu_selected,)

    return run_atom_shell(
        ctx, P5_P7_ATOM_SPECS["Ω.A.L4.P7.02"],
        pre_probes=(ctx.prior_ok("Ω.A.L4.P7.01"),),
        act=act, post_probes=post,
    )


def _run_p7_03(ctx: AtomContext) -> AtomOutcome:
    start = ctx.deps.clock()

    def act() -> dict[str, Any]:
        ctx.deps.sleep(3.0)
        return {"elapsed_sec": ctx.deps.clock() - start}

    def post(snapshot: dict[str, Any]) -> tuple[bool, ...]:
        return (float(snapshot.get("elapsed_sec", 0)) >= 2.999,)

    return run_atom_shell(
        ctx, P5_P7_ATOM_SPECS["Ω.A.L4.P7.03"],
        pre_probes=(ctx.prior_ok("Ω.A.L4.P7.02"),),
        act=act, post_probes=post,
    )


def _run_p7_04(ctx: AtomContext) -> AtomOutcome:
    deps: P57Deps = ctx.deps  # type: ignore[assignment]

    def act() -> dict[str, Any]:
        wait_sec = float(deps.quantify_wait_sec or read_quantify_wait_sec())
        done, polls = poll_quantify_progress_done(
            is_progress_visible=deps.progress_visible,
            clock=deps.clock,
            sleep=deps.sleep,
            max_wait_sec=wait_sec,
            initial_sleep_sec=0.0,
        )
        return {"progress_done": done, "polls": polls}

    def post(snapshot: dict[str, Any]) -> tuple[bool, ...]:
        return (snapshot.get("progress_done") is True,)

    return run_atom_shell(
        ctx, P5_P7_ATOM_SPECS["Ω.A.L4.P7.04"],
        pre_probes=(ctx.prior_ok("Ω.A.L4.P7.03"),),
        act=act, post_probes=post,
    )


def _run_p7_05(ctx: AtomContext) -> AtomOutcome:
    deps: P57Deps = ctx.deps  # type: ignore[assignment]
    from gc1_runtime.layer0_gpost import run_gpost_eye_verify

    def evaluate() -> tuple[bool, dict[str, Any]]:
        verdict = evaluate_peak_table_task(
            verify_eye=deps.verify_eye,
            dry_run=deps.dry_run,
            task_id="verify_peak_table_has_data",
            fallback_text=deps.peak_table_after_quantify,
            eye=deps.eye,
            text_provider=deps.peak_table_text_provider,
        )
        return verdict.passed, {"verify_eye": deps.verify_eye, "task_detail": verdict.detail}

    def act() -> dict[str, Any]:
        gpost = run_gpost_eye_verify(
            task_id="verify_peak_table_has_data",
            evaluate=evaluate,
            retry_fn=lambda: None,
            sleep_fn=deps.sleep,
        )
        return {**gpost.probe_snapshot, "peak_has_data": gpost.passed}

    def post(snapshot: dict[str, Any]) -> tuple[bool, ...]:
        return (snapshot.get("peak_has_data") is True,)

    return run_atom_shell(
        ctx, P5_P7_ATOM_SPECS["Ω.A.L4.P7.05"],
        pre_probes=(ctx.prior_ok("Ω.A.L4.P7.04"),),
        act=act, post_probes=post,
    )


_P5_RUNNERS = (_run_p5_01, _run_p5_02, _run_p5_03, _run_p5_04, _run_p5_05)
_P6_RUNNERS = (_run_p6_01, _run_p6_02, _run_p6_03, _run_p6_04, _run_p6_05, _run_p6_06)
_P7_RUNNERS = (_run_p7_01, _run_p7_02, _run_p7_03, _run_p7_04, _run_p7_05)


def _run_phase_atoms(
    ctx: AtomContext,
    runners: Sequence[Callable[[AtomContext], AtomOutcome]],
    *,
    phase: str,
    next_phase: str,
    last_ids: Sequence[str],
) -> PhaseOutcome:
    if _phase_blocked_early_ok(ctx):
        return PhaseOutcome(phase=phase, ok=True, skipped=True, message="skipped: EARLY_OK")
    for runner in runners:
        atom_id = _atom_id_from_runner(runner)
        outcome = runner(ctx)
        if not outcome.ok and not outcome.skipped:
            ctx.store.save(ctx.state)
            return PhaseOutcome(
                phase=phase,
                ok=False,
                message=outcome.fail_code or "atom failed",
                last_atom=atom_id,
            )
    ctx.state.phase_current = next_phase
    ctx.store.save(ctx.state)
    return PhaseOutcome(phase=phase, ok=True, last_atom=last_ids[-1])


def run_phase_p5(ctx: AtomContext) -> PhaseOutcome:
    return _run_phase_atoms(ctx, _P5_RUNNERS, phase="P5", next_phase="P6", last_ids=P5_ATOM_IDS)


def run_phase_p6(ctx: AtomContext) -> PhaseOutcome:
    return _run_phase_atoms(ctx, _P6_RUNNERS, phase="P6", next_phase="P7", last_ids=P6_ATOM_IDS)


def run_phase_p7(ctx: AtomContext) -> PhaseOutcome:
    return _run_phase_atoms(ctx, _P7_RUNNERS, phase="P7", next_phase="P8", last_ids=P7_ATOM_IDS)


def run_p5_p7_dry(
    store: StateStore,
    deps: P57Deps,
    *,
    gates: GateEvaluator | None = None,
) -> tuple[PhaseOutcome, PhaseOutcome, PhaseOutcome]:
    """P5~P7 dry-run — P0~P4 완료 state 에서 이어 실행."""
    state = store.load()
    if not state.atoms:
        state = JobState.new_job(atom_ids=P0_P7_ATOM_IDS)
    for aid in P5_P7_ATOM_IDS:
        if aid not in state.atoms:
            state.atoms[aid] = AtomRecord()
    ctx = AtomContext(
        state=state,
        store=store,
        gates=gates or GateEvaluator(),
        deps=deps,
    )
    p5 = run_phase_p5(ctx)
    if not p5.ok:
        return p5, PhaseOutcome(phase="P6", ok=False, message="P5 failed"), PhaseOutcome(
            phase="P7", ok=False, message="P5 failed",
        )
    if p5.skipped:
        skip = PhaseOutcome(phase="P6", ok=True, skipped=True, message="skipped: EARLY_OK")
        return p5, skip, PhaseOutcome(phase="P7", ok=True, skipped=True, message="skipped: EARLY_OK")
    p6 = run_phase_p6(ctx)
    if not p6.ok:
        return p5, p6, PhaseOutcome(phase="P7", ok=False, message="P6 failed")
    p7 = run_phase_p7(ctx)
    return p5, p6, p7


def run_p0_p7_dry(
    store: StateStore,
    deps: P57Deps,
    *,
    gates: GateEvaluator | None = None,
) -> tuple[PhaseOutcome, ...]:
    """P0→P7 전체 dry-run."""
    from gc1_runtime.layer4_atoms_p4 import run_p0_p4_dry

    prior = run_p0_p4_dry(store, deps, gates=gates)
    if len(prior) < 5 or not all(o.ok for o in prior):
        return prior
    p5, p6, p7 = run_p5_p7_dry(store, deps, gates=gates)
    return (*prior, p5, p6, p7)


__all__ = [
    "P0_P7_ATOM_IDS",
    "P57Deps",
    "P5_ATOM_IDS",
    "P5_P7_ATOM_IDS",
    "P5_P7_ATOM_SPECS",
    "P6_ATOM_IDS",
    "P7_ATOM_IDS",
    "poll_quantify_progress_done",
    "run_p0_p7_dry",
    "run_p5_p7_dry",
    "run_phase_p5",
    "run_phase_p6",
    "run_phase_p7",
    "top_menu_has_item",
]
