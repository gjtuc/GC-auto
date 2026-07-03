# -*- coding: utf-8 -*-
"""
L4 원자 — P2 select_all + P3 context_initialize (T51).

설계 ``deploy/GC1_RUNTIME_DESIGN_PART2_L4_P0_P4.md`` §P2.01~P2.05, §P3.01~P3.06.
``gc_autochro.step_select_all_samples`` / ``step_context_initialize_samples`` leaf 분리.

P0/P1 공통 shell·StateStore 는 ``layer4_atoms_p0_p1`` 재사용.
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
from gc1_runtime.layer1_state import AtomRecord, AtomStatus, JobState, StateStore
from gc1_runtime.layer2_gates import GateEvaluator
from gc1_runtime.layer3_hand import matcher_initialize_only, menu_popup_pick
from gc1_runtime.layer3_eye import evaluate_peak_table_task
from gc1_runtime.layer4_atoms_p0_p1 import (
    AtomContext,
    AtomOutcome,
    AtomSpec,
    P0P1Deps,
    P0_P1_ATOM_IDS,
    PhaseOutcome,
    _spec,
    run_atom_shell,
)

# ---------------------------------------------------------------------------
# Atom IDs · registry (P2 + P3)
# ---------------------------------------------------------------------------

P2_ATOM_IDS: tuple[str, ...] = (
    "Ω.A.L4.P2.01",
    "Ω.A.L4.P2.02",
    "Ω.A.L4.P2.03",
    "Ω.A.L4.P2.04",
    "Ω.A.L4.P2.05",
)

P3_ATOM_IDS: tuple[str, ...] = (
    "Ω.A.L4.P3.01",
    "Ω.A.L4.P3.02",
    "Ω.A.L4.P3.03",
    "Ω.A.L4.P3.04",
    "Ω.A.L4.P3.05",
    "Ω.A.L4.P3.06",
)

P2_P3_ATOM_IDS: tuple[str, ...] = P2_ATOM_IDS + P3_ATOM_IDS
P0_P3_ATOM_IDS: tuple[str, ...] = P0_P1_ATOM_IDS + P2_P3_ATOM_IDS

P2_P3_ATOM_SPECS: dict[str, AtomSpec] = {
    "Ω.A.L4.P2.01": _spec("Ω.A.L4.P2.01", "H", timeout_ms=10000),
    "Ω.A.L4.P2.02": _spec("Ω.A.L4.P2.02", "H", timeout_ms=10000),
    "Ω.A.L4.P2.03": _spec(
        "Ω.A.L4.P2.03", "H", code="E_P2_FOCUS", max_attempt=3, retry_delay_ms=500,
        fallback_channel="H re-click neutral", timeout_ms=15000,
    ),
    "Ω.A.L4.P2.04": _spec(
        "Ω.A.L4.P2.04", "H", code="E_P2_SELECT", max_attempt=2, retry_delay_ms=300,
        fallback_channel="H resend ^a", timeout_ms=5000,
    ),
    "Ω.A.L4.P2.05": _spec("Ω.A.L4.P2.05", "W", timeout_ms=1000),
    "Ω.A.L4.P3.01": _spec("Ω.A.L4.P3.01", "H", timeout_ms=10000),
    "Ω.A.L4.P3.02": _spec("Ω.A.L4.P3.02", "H", timeout_ms=10000),
    "Ω.A.L4.P3.03": _spec("Ω.A.L4.P3.03", "H", timeout_ms=10000),
    "Ω.A.L4.P3.04": _spec(
        "Ω.A.L4.P3.04", "H", code="E_P3_MENU", max_attempt=3, retry_delay_ms=120,
        fallback_channel="E eye click 초기화", timeout_ms=20000,
    ),
    "Ω.A.L4.P3.05": _spec("Ω.A.L4.P3.05", "W", timeout_ms=2000),
    "Ω.A.L4.P3.06": _spec("Ω.A.L4.P3.06", "E", code="E_VERIFY_PEAK", timeout_ms=30000),
}


@dataclass
class P2P3Deps(P0P1Deps):
    """
    P2/P3 dry-run·live 주입 필드.

    ``list_neutral_x_frac`` — ``gc_autochro._neutral_list_coords`` (수집 일시 열 쪽).
    ``peak_table_text`` — P3.06 TASK verify (초기화 후 0 위주 OCR 텍스트).
    ``menu_popup_items`` — P3.04 컨텍스트 메뉴 mock.
    """

    list_neutral_x_frac: float = 0.88
    peak_table_text: str = "0 0 0 0 0"
    menu_popup_items: list[str] = field(default_factory=lambda: ["초기화", "초기화+정량"])
    sample_list_focused: bool = False
    ctrl_a_sent: bool = False
    context_menu_clicked: bool = False


# ---------------------------------------------------------------------------
# PURE — Ctrl+A 전 클릭 좌표 (gc_autochro._neutral_list_coords)
# ---------------------------------------------------------------------------


def neutral_list_coords(
    width: int,
    height: int,
    *,
    x_frac: float = 0.88,
) -> tuple[int, int]:
    """P2.03~04 — 소유자 ID 드롭다운 회피용 rel_x/rel_y."""
    frac = min(max(x_frac, 0.45), 0.92)
    w = max(width, 400)
    h = max(height, 80)
    rel_x = int(w * frac)
    rel_y = max(16, min(32, h // 10))
    return rel_x, rel_y


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


class _FakePopupMenu:
    """``menu_popup_pick`` dry-run 용 #32768 mock."""

    def __init__(self, items: Sequence[str]) -> None:
        self._items = list(items)
        self.clicked: str | None = None

    def menu(self) -> _FakePopupMenu:
        return self

    def items(self) -> list[str]:
        return self._items

    def menu_item(self, text: str) -> _FakePopupMenu:
        self.clicked = text
        return self

    def click_input(self) -> None:
        pass


def _popup_wrappers(deps: P2P3Deps) -> list[_FakePopupMenu]:
    return [_FakePopupMenu(deps.menu_popup_items)]


# ---------------------------------------------------------------------------
# P2 atoms — select_all
# ---------------------------------------------------------------------------


def _run_p2_01(ctx: AtomContext) -> AtomOutcome:
    def act() -> dict[str, Any]:
        _select_analysis_tab_deps(ctx)
        ctx.deps.sleep(0.8)
        return {"tab": "analysis"}

    def post(_snapshot: dict[str, Any]) -> tuple[bool, ...]:
        return (menu_texts_include_analysis(_menu_texts(ctx)),)

    return run_atom_shell(
        ctx,
        P2_P3_ATOM_SPECS["Ω.A.L4.P2.01"],
        pre_probes=(ctx.prior_ok("Ω.A.L4.P1.10"),),
        act=act,
        post_probes=post,
    )


def _run_p2_02(ctx: AtomContext) -> AtomOutcome:
    def act() -> dict[str, Any]:
        geom = _analysis_sample_geom(ctx)
        return {"items": geom.item_count, "_geom_ok": geom.item_count > 0}

    def post(snapshot: dict[str, Any]) -> tuple[bool, ...]:
        return (bool(snapshot.get("_geom_ok")),)

    return run_atom_shell(
        ctx,
        P2_P3_ATOM_SPECS["Ω.A.L4.P2.02"],
        pre_probes=(menu_texts_include_analysis(_menu_texts(ctx)),),
        act=act,
        post_probes=post,
    )


def _run_p2_03(ctx: AtomContext) -> AtomOutcome:
    deps: P2P3Deps = ctx.deps  # type: ignore[assignment]

    def act() -> dict[str, Any]:
        geom = _analysis_sample_geom(ctx)
        rel_x, rel_y = neutral_list_coords(
            geom.width, geom.height, x_frac=deps.list_neutral_x_frac,
        )
        deps.sample_list_focused = True
        ctx.deps.hand._record("set_focus", "analysis_sample")
        ctx.deps.hand._record("click", f"{rel_x},{rel_y}")
        return {"rel_x": rel_x, "rel_y": rel_y, "focused": True}

    def post(snapshot: dict[str, Any]) -> tuple[bool, ...]:
        return (snapshot.get("focused") is True,)

    return run_atom_shell(
        ctx,
        P2_P3_ATOM_SPECS["Ω.A.L4.P2.03"],
        pre_probes=(ctx.prior_ok("Ω.A.L4.P2.02"),),
        act=act,
        post_probes=post,
    )


def _run_p2_04(ctx: AtomContext) -> AtomOutcome:
    deps: P2P3Deps = ctx.deps  # type: ignore[assignment]

    def act() -> dict[str, Any]:
        ctx.deps.hand.send_keys("^a")
        deps.ctrl_a_sent = True
        return {"keys": "^a"}

    def post(_snapshot: dict[str, Any]) -> tuple[bool, ...]:
        return (deps.ctrl_a_sent,)

    return run_atom_shell(
        ctx,
        P2_P3_ATOM_SPECS["Ω.A.L4.P2.04"],
        pre_probes=(ctx.prior_ok("Ω.A.L4.P2.03"),),
        act=act,
        post_probes=post,
    )


def _run_p2_05(ctx: AtomContext) -> AtomOutcome:
    start = ctx.deps.clock()

    def act() -> dict[str, Any]:
        ctx.deps.sleep(0.5)
        elapsed = ctx.deps.clock() - start
        return {"elapsed_sec": elapsed}

    def post(snapshot: dict[str, Any]) -> tuple[bool, ...]:
        # float 누적 오차 (0.5+0.5≠1.0) — ms 임계보다 초 비교+여유
        return (float(snapshot.get("elapsed_sec", 0)) >= 0.499,)

    return run_atom_shell(
        ctx,
        P2_P3_ATOM_SPECS["Ω.A.L4.P2.05"],
        pre_probes=(ctx.prior_ok("Ω.A.L4.P2.04"),),
        act=act,
        post_probes=post,
    )


# ---------------------------------------------------------------------------
# P3 atoms — context_initialize
# ---------------------------------------------------------------------------


def _run_p3_01(ctx: AtomContext) -> AtomOutcome:
    def act() -> dict[str, Any]:
        _select_analysis_tab_deps(ctx)
        return {"tab": "analysis"}

    def post(_snapshot: dict[str, Any]) -> tuple[bool, ...]:
        return (menu_texts_include_analysis(_menu_texts(ctx)),)

    return run_atom_shell(
        ctx,
        P2_P3_ATOM_SPECS["Ω.A.L4.P3.01"],
        pre_probes=(ctx.prior_ok("Ω.A.L4.P2.05"),),
        act=act,
        post_probes=post,
    )


def _run_p3_02(ctx: AtomContext) -> AtomOutcome:
    def act() -> dict[str, Any]:
        geom = _analysis_sample_geom(ctx)
        return {"items": geom.item_count, "_geom_ok": geom.item_count > 0}

    def post(snapshot: dict[str, Any]) -> tuple[bool, ...]:
        return (bool(snapshot.get("_geom_ok")),)

    return run_atom_shell(
        ctx,
        P2_P3_ATOM_SPECS["Ω.A.L4.P3.02"],
        pre_probes=(menu_texts_include_analysis(_menu_texts(ctx)),),
        act=act,
        post_probes=post,
    )


def _run_p3_03(ctx: AtomContext) -> AtomOutcome:
    def act() -> dict[str, Any]:
        geom = _analysis_sample_geom(ctx)
        rel_x, rel_y = neutral_list_coords(geom.width, geom.height)
        ctx.deps.hand._record("click", f"right:{rel_x},{rel_y}")
        return {"rclick": True}

    def post(snapshot: dict[str, Any]) -> tuple[bool, ...]:
        return (snapshot.get("rclick") is True,)

    return run_atom_shell(
        ctx,
        P2_P3_ATOM_SPECS["Ω.A.L4.P3.03"],
        pre_probes=(ctx.prior_ok("Ω.A.L4.P3.02"),),
        act=act,
        post_probes=post,
    )


def gpost_retry_p3_04(ctx: AtomContext) -> dict[str, Any]:
    """G-POST (T91) — P3.04 초기화 메뉴 재클릭. ``verify_peak_table_cleared`` 실패 시 1회."""
    deps: P2P3Deps = ctx.deps  # type: ignore[assignment]
    result = menu_popup_pick(
        matcher_initialize_only(),
        get_wrappers=lambda: _popup_wrappers(deps),
        clock=deps.clock,
        sleep=deps.sleep,
        timeout=2.0,
    )
    deps.context_menu_clicked = True
    return {"menu": result.matched_text, "gpost_retry": "P3.04"}


def _run_p3_04(ctx: AtomContext) -> AtomOutcome:
    deps: P2P3Deps = ctx.deps  # type: ignore[assignment]

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
        ctx,
        P2_P3_ATOM_SPECS["Ω.A.L4.P3.04"],
        pre_probes=(ctx.prior_ok("Ω.A.L4.P3.03"),),
        act=act,
        post_probes=post,
    )


def _run_p3_05(ctx: AtomContext) -> AtomOutcome:
    start = ctx.deps.clock()

    def act() -> dict[str, Any]:
        ctx.deps.sleep(0.8)
        elapsed = ctx.deps.clock() - start
        return {"elapsed_sec": elapsed}

    def post(snapshot: dict[str, Any]) -> tuple[bool, ...]:
        return (float(snapshot.get("elapsed_sec", 0)) >= 0.799,)

    return run_atom_shell(
        ctx,
        P2_P3_ATOM_SPECS["Ω.A.L4.P3.05"],
        pre_probes=(ctx.prior_ok("Ω.A.L4.P3.04"),),
        act=act,
        post_probes=post,
    )


def _run_p3_06(ctx: AtomContext) -> AtomOutcome:
    deps: P2P3Deps = ctx.deps  # type: ignore[assignment]
    from gc1_runtime.layer0_gpost import run_gpost_eye_verify

    def evaluate() -> tuple[bool, dict[str, Any]]:
        verdict = evaluate_peak_table_task(
            verify_eye=deps.verify_eye,
            dry_run=deps.dry_run,
            task_id="verify_peak_table_cleared",
            fallback_text=deps.peak_table_text,
            eye=deps.eye,
            text_provider=deps.peak_table_text_provider,
        )
        snap = {
            "text_len": len(deps.peak_table_text),
            "verify_eye": deps.verify_eye,
            "task_detail": verdict.detail,
        }
        return verdict.passed, snap

    def act() -> dict[str, Any]:
        gpost = run_gpost_eye_verify(
            task_id="verify_peak_table_cleared",
            evaluate=evaluate,
            retry_fn=lambda: gpost_retry_p3_04(ctx),
            sleep_fn=deps.sleep,
        )
        return {**gpost.probe_snapshot, "peak_cleared": gpost.passed, "task_detail": gpost.detail}

    def post(snapshot: dict[str, Any]) -> tuple[bool, ...]:
        return (snapshot.get("peak_cleared") is True,)

    return run_atom_shell(
        ctx,
        P2_P3_ATOM_SPECS["Ω.A.L4.P3.06"],
        pre_probes=(ctx.prior_ok("Ω.A.L4.P3.05"),),
        act=act,
        post_probes=post,
    )


_P2_RUNNERS: tuple[Callable[[AtomContext], AtomOutcome], ...] = (
    _run_p2_01,
    _run_p2_02,
    _run_p2_03,
    _run_p2_04,
    _run_p2_05,
)

_P3_RUNNERS: tuple[Callable[[AtomContext], AtomOutcome], ...] = (
    _run_p3_01,
    _run_p3_02,
    _run_p3_03,
    _run_p3_04,
    _run_p3_05,
    _run_p3_06,
)


def _atom_id_from_runner(runner: Callable[[AtomContext], AtomOutcome]) -> str:
    parts = runner.__name__.split("_")
    return f"Ω.A.L4.{parts[2].upper()}.{parts[3]}"


def _phase_blocked_early_ok(ctx: AtomContext) -> bool:
    return ctx.state.atoms.get("Ω.A.L4.P0.05", AtomRecord()).fail_code == "EARLY_OK"


def run_phase_p2(ctx: AtomContext) -> PhaseOutcome:
    """P2 select_all — P1.10 완료 후."""
    if _phase_blocked_early_ok(ctx):
        return PhaseOutcome(phase="P2", ok=True, skipped=True, message="skipped: EARLY_OK")
    for runner in _P2_RUNNERS:
        atom_id = _atom_id_from_runner(runner)
        outcome = runner(ctx)
        if not outcome.ok and not outcome.skipped:
            ctx.store.save(ctx.state)
            return PhaseOutcome(
                phase="P2",
                ok=False,
                message=outcome.fail_code or "atom failed",
                last_atom=atom_id,
            )
    ctx.state.phase_current = "P3"
    ctx.store.save(ctx.state)
    return PhaseOutcome(phase="P2", ok=True, last_atom=P2_ATOM_IDS[-1])


def run_phase_p3(ctx: AtomContext) -> PhaseOutcome:
    """P3 context_initialize."""
    if _phase_blocked_early_ok(ctx):
        return PhaseOutcome(phase="P3", ok=True, skipped=True, message="skipped: EARLY_OK")
    for runner in _P3_RUNNERS:
        atom_id = _atom_id_from_runner(runner)
        outcome = runner(ctx)
        if not outcome.ok and not outcome.skipped:
            ctx.store.save(ctx.state)
            return PhaseOutcome(
                phase="P3",
                ok=False,
                message=outcome.fail_code or "atom failed",
                last_atom=atom_id,
            )
    ctx.state.phase_current = "P4"
    ctx.store.save(ctx.state)
    return PhaseOutcome(phase="P3", ok=True, last_atom=P3_ATOM_IDS[-1])


def run_p2_p3_dry(
    store: StateStore,
    deps: P2P3Deps,
    *,
    gates: GateEvaluator | None = None,
) -> tuple[PhaseOutcome, PhaseOutcome]:
    """
    P2+P3 dry-run — **P0/P1 atom 이 ok 인 state** 에서 이어 실행.

    P1 미완이면 P2.01 pre_probe 실패. 전체 체인은 ``run_p0_p3_dry``.
    """
    state = store.load()
    if not state.atoms:
        state = JobState.new_job(atom_ids=P0_P3_ATOM_IDS)
    for aid in P2_P3_ATOM_IDS:
        if aid not in state.atoms:
            state.atoms[aid] = AtomRecord()
    ctx = AtomContext(
        state=state,
        store=store,
        gates=gates or GateEvaluator(),
        deps=deps,
    )
    p2 = run_phase_p2(ctx)
    if not p2.ok:
        return p2, PhaseOutcome(phase="P3", ok=False, message="P2 failed")
    if p2.skipped:
        return p2, PhaseOutcome(phase="P3", ok=True, skipped=True, message="skipped: EARLY_OK")
    p3 = run_phase_p3(ctx)
    return p2, p3


def run_p0_p3_dry(
    store: StateStore,
    deps: P2P3Deps,
    *,
    gates: GateEvaluator | None = None,
) -> tuple[PhaseOutcome, ...]:
    """P0→P3 전체 dry-run (T51·T63 체인)."""
    from gc1_runtime.layer4_atoms_p0_p1 import run_phase_p0, run_phase_p1

    state = store.load()
    if not state.atoms:
        state = JobState.new_job(atom_ids=P0_P3_ATOM_IDS)
    else:
        for aid in P0_P3_ATOM_IDS:
            if aid not in state.atoms:
                state.atoms[aid] = AtomRecord()
    ctx = AtomContext(
        state=state,
        store=store,
        gates=gates or GateEvaluator(),
        deps=deps,
    )
    p0 = run_phase_p0(ctx)
    if not p0.ok:
        return (p0,)
    if p0.early_exit:
        return (p0,)
    p1 = run_phase_p1(ctx)
    if not p1.ok:
        return (p0, p1)
    p2, p3 = run_p2_p3_dry(store, deps, gates=gates)
    return (p0, p1, p2, p3)


__all__ = [
    "P0_P3_ATOM_IDS",
    "P2P3Deps",
    "P2_ATOM_IDS",
    "P2_P3_ATOM_IDS",
    "P2_P3_ATOM_SPECS",
    "P3_ATOM_IDS",
    "neutral_list_coords",
    "run_p0_p3_dry",
    "run_p2_p3_dry",
    "run_phase_p2",
    "run_phase_p3",
]
