# -*- coding: utf-8 -*-
"""
L4 원자 — P4 load_analysis_method (MTD dialog) (T52).

설계 ``deploy/GC1_RUNTIME_DESIGN_PART2_L4_P0_P4.md`` §P4.01~P4.08.
``gc_autochro.step_load_analysis_method`` leaf 분리 — MTD 경로·트리 선택·파일 대화상자.

P0~P3 shell 은 ``layer4_atoms_p0_p1`` / ``layer4_atoms_p2_p3`` 재사용.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import Any, Callable, Sequence

from gc1_runtime.layer0_ctl import (
    TreeGeom,
    menu_texts_include_analysis,
    pick_analysis_tree,
    tab_index_for_analysis,
)
from gc1_runtime.layer0_data import (
    mtd_file_exists,
    resolve_analysis_method_mtd_path,
    tree_label_matches_data_name,
)
from gc1_runtime.layer0_config import read_analysis_method_dir
from gc1_runtime.layer1_state import AtomRecord, AtomStatus, JobState, StateStore
from gc1_runtime.layer2_gates import GateEvaluator
from gc1_runtime.layer3_eye import evaluate_peak_table_task
from gc1_runtime.layer3_hand import matcher_load_analysis_method, menu_popup_pick
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
    P0_P3_ATOM_IDS,
    _FakePopupMenu,
    _phase_blocked_early_ok,
)

# ---------------------------------------------------------------------------
# Atom registry
# ---------------------------------------------------------------------------

P4_ATOM_IDS: tuple[str, ...] = (
    "Ω.A.L4.P4.01",
    "Ω.A.L4.P4.02",
    "Ω.A.L4.P4.03",
    "Ω.A.L4.P4.04",
    "Ω.A.L4.P4.05",
    "Ω.A.L4.P4.06",
    "Ω.A.L4.P4.07",
    "Ω.A.L4.P4.08",
)

P0_P4_ATOM_IDS: tuple[str, ...] = P0_P3_ATOM_IDS + P4_ATOM_IDS

P4_ATOM_SPECS: dict[str, AtomSpec] = {
    "Ω.A.L4.P4.01": _spec("Ω.A.L4.P4.01", "F", code="E_MTD_MISSING", timeout_ms=10000),
    "Ω.A.L4.P4.02": _spec("Ω.A.L4.P4.02", "H", timeout_ms=10000),
    "Ω.A.L4.P4.03": _spec(
        "Ω.A.L4.P4.03", "H", code="E_P4_TREE", max_attempt=3, retry_delay_ms=250, timeout_ms=30000,
    ),
    "Ω.A.L4.P4.04": _spec("Ω.A.L4.P4.04", "H", timeout_ms=10000),
    "Ω.A.L4.P4.05": _spec("Ω.A.L4.P4.05", "H", timeout_ms=15000),
    "Ω.A.L4.P4.06": _spec(
        "Ω.A.L4.P4.06", "F", code="E_P4_MTD_DLG", max_attempt=2, retry_delay_ms=400,
        fallback_channel="F send_keys path", timeout_ms=30000,
    ),
    "Ω.A.L4.P4.07": _spec("Ω.A.L4.P4.07", "W", timeout_ms=3000),
    "Ω.A.L4.P4.08": _spec("Ω.A.L4.P4.08", "E", code="E_VERIFY_PEAK", timeout_ms=30000),
}


@dataclass
class P4Deps(P2P3Deps):
    """
    P4 dry-run·live 주입.

    ``mtd_dir`` — MTD 검색 폴더 (테스트: tempfile).
    ``tree_lines`` — 분석목록 SysTreeView32 텍스트 mock.
    ``peak_table_after_mtd`` — P4.08 TASK verify (MTD 로드 후 피크 숫자).
    """

    mtd_dir: str = ""
    mtd_path_resolved: str = ""
    tree_lines: list[str] = field(default_factory=list)
    tree_line_chosen: str = ""
    tree_geom: TreeGeom = field(
        default_factory=lambda: TreeGeom(top=120, bottom=520, left=10, right=250),
    )
    mtd_dialog_ok: bool = False
    peak_table_after_mtd: str = "0.12 3.45 5.6"
    load_menu_items: list[str] = field(
        default_factory=lambda: ["분석방법 불러오기", "초기화"],
    )


# ---------------------------------------------------------------------------
# PURE — 트리 선택·우클릭 좌표 (gc_autochro 동일)
# ---------------------------------------------------------------------------


def choose_tree_line_for_data_name(
    lines: Sequence[str],
    data_name: str,
) -> str | None:
    """P4.03 — ``_select_tree_data_name`` 순수 부분."""
    for line in lines:
        text = (line or "").strip()
        if text and tree_label_matches_data_name(text, data_name):
            return text.split(".")[0].strip()
    return None


def tree_right_click_coords(width: int, height: int) -> tuple[int, int]:
    """P4.04 — ``_right_click_tree_data_name`` rel_x/rel_y."""
    rel_x = max(24, min(width // 3, 80))
    rel_y = max(16, min(height // 6, 28))
    return rel_x, rel_y


def _mtd_directory(deps: P4Deps) -> str:
    if deps.mtd_dir:
        return deps.mtd_dir
    return read_analysis_method_dir()


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


def _popup_wrappers(deps: P4Deps) -> list[_FakePopupMenu]:
    return [_FakePopupMenu(deps.load_menu_items)]


def _atom_id_from_runner(runner: Callable[[AtomContext], AtomOutcome]) -> str:
    parts = runner.__name__.split("_")
    return f"Ω.A.L4.{parts[2].upper()}.{parts[3]}"


# ---------------------------------------------------------------------------
# P4 atoms
# ---------------------------------------------------------------------------


def _run_p4_01(ctx: AtomContext) -> AtomOutcome:
    deps: P4Deps = ctx.deps  # type: ignore[assignment]

    def act() -> dict[str, Any]:
        path = resolve_analysis_method_mtd_path(
            ctx.state.data_name,
            mtd_dir=_mtd_directory(deps),
        )
        deps.mtd_path_resolved = path
        return {"mtd_path": path, "basename": os.path.basename(path)}

    def post(snapshot: dict[str, Any]) -> tuple[bool, ...]:
        path = str(snapshot.get("mtd_path") or deps.mtd_path_resolved)
        return (mtd_file_exists(path),)

    return run_atom_shell(
        ctx,
        P4_ATOM_SPECS["Ω.A.L4.P4.01"],
        pre_probes=(ctx.prior_ok("Ω.A.L4.P3.06"),),
        act=act,
        post_probes=post,
    )


def _run_p4_02(ctx: AtomContext) -> AtomOutcome:
    def act() -> dict[str, Any]:
        _select_analysis_tab_deps(ctx)
        return {"tab": "analysis"}

    def post(_snapshot: dict[str, Any]) -> tuple[bool, ...]:
        return (menu_texts_include_analysis(_menu_texts(ctx)),)

    return run_atom_shell(
        ctx,
        P4_ATOM_SPECS["Ω.A.L4.P4.02"],
        pre_probes=(ctx.prior_ok("Ω.A.L4.P4.01"),),
        act=act,
        post_probes=post,
    )


def _run_p4_03(ctx: AtomContext) -> AtomOutcome:
    deps: P4Deps = ctx.deps  # type: ignore[assignment]

    def act() -> dict[str, Any]:
        if not deps.tree_lines:
            deps.tree_lines = [ctx.state.data_name]
        chosen = choose_tree_line_for_data_name(deps.tree_lines, ctx.state.data_name)
        if not chosen:
            raise RuntimeError(f"트리에 데이터명 없음: {ctx.state.data_name!r}")
        deps.tree_line_chosen = chosen
        ctx.deps.hand._record("tree.select", chosen)
        return {"tree_line": chosen, "candidates": len(deps.tree_lines)}

    def post(snapshot: dict[str, Any]) -> tuple[bool, ...]:
        line = str(snapshot.get("tree_line") or "")
        return (
            bool(line),
            tree_label_matches_data_name(line, ctx.state.data_name),
        )

    return run_atom_shell(
        ctx,
        P4_ATOM_SPECS["Ω.A.L4.P4.03"],
        pre_probes=(
            menu_texts_include_analysis(_menu_texts(ctx)),
            bool(ctx.state.data_name),
        ),
        act=act,
        post_probes=post,
    )


def _run_p4_04(ctx: AtomContext) -> AtomOutcome:
    deps: P4Deps = ctx.deps  # type: ignore[assignment]

    def act() -> dict[str, Any]:
        geom = deps.tree_geom
        if ctx.deps.win_rect is not None and deps.tree_lines:
            geom = pick_analysis_tree([deps.tree_geom], ctx.deps.win_rect)
        w = geom.right - geom.left
        h = geom.bottom - geom.top
        rel_x, rel_y = tree_right_click_coords(w, h)
        ctx.deps.hand._record("click", f"tree_right:{rel_x},{rel_y}")
        return {"rclick": True, "rel_x": rel_x, "rel_y": rel_y}

    def post(snapshot: dict[str, Any]) -> tuple[bool, ...]:
        return (snapshot.get("rclick") is True,)

    return run_atom_shell(
        ctx,
        P4_ATOM_SPECS["Ω.A.L4.P4.04"],
        pre_probes=(ctx.prior_ok("Ω.A.L4.P4.03"),),
        act=act,
        post_probes=post,
    )


def _run_p4_05(ctx: AtomContext) -> AtomOutcome:
    deps: P4Deps = ctx.deps  # type: ignore[assignment]

    def act() -> dict[str, Any]:
        result = menu_popup_pick(
            matcher_load_analysis_method(),
            get_wrappers=lambda: _popup_wrappers(deps),
            clock=deps.clock,
            sleep=deps.sleep,
            timeout=2.0,
        )
        return {"menu": result.matched_text}

    def post(snapshot: dict[str, Any]) -> tuple[bool, ...]:
        menu = str(snapshot.get("menu") or "")
        return (bool(menu), "분석방법" in menu and "불러" in menu)

    return run_atom_shell(
        ctx,
        P4_ATOM_SPECS["Ω.A.L4.P4.05"],
        pre_probes=(ctx.prior_ok("Ω.A.L4.P4.04"),),
        act=act,
        post_probes=post,
    )


def _run_p4_06(ctx: AtomContext) -> AtomOutcome:
    deps: P4Deps = ctx.deps  # type: ignore[assignment]

    def act() -> dict[str, Any]:
        path = deps.mtd_path_resolved
        if not path:
            raise RuntimeError("mtd_path_resolved not set — P4.01 선행 필요")
        if deps.dry_run:
            ctx.deps.hand._record("file_dialog", path)
            deps.mtd_dialog_ok = True
            return {"dialog": "closed", "path": path}
        if deps.find_windows is None or deps.connect_window is None:
            raise RuntimeError("find_windows/connect_window not configured")
        from gc1_runtime.layer3_file import (
            click_dialog_button,
            find_dialog_by_title_re,
            set_filename_in_dialog,
        )

        dlg = find_dialog_by_title_re(
            r"분석방법 불러오기",
            find_windows=deps.find_windows,
            connect_window=deps.connect_window,
            timeout=30.0,
            clock=deps.clock,
            sleep=deps.sleep,
        )
        if dlg is None:
            raise RuntimeError("분석방법 불러오기 대화상자 없음")
        set_filename_in_dialog(
            dlg,
            os.path.basename(path),
            send_keys_fn=deps.hand.send_keys_fn,
            sleep=deps.sleep,
        )
        norm = os.path.normpath(os.path.abspath(path))
        # stem 만 넣은 경우 full path 재시도는 live Autochro 에서 edit 전체 경로 사용
        try:
            edit = dlg.descendants(class_name="Edit")[0]
            edit.set_edit_text(norm)
        except Exception:
            pass
        opened = click_dialog_button(
            dlg,
            ("열기(&O)", "열기(O)", "열기", "Open", "&Open"),
        )
        if not opened and deps.hand.send_keys_fn:
            deps.hand.send_keys_fn("%o")
        deps.mtd_dialog_ok = True
        return {"dialog": "closed", "path": norm}

    def post(_snapshot: dict[str, Any]) -> tuple[bool, ...]:
        return (deps.mtd_dialog_ok,)

    return run_atom_shell(
        ctx,
        P4_ATOM_SPECS["Ω.A.L4.P4.06"],
        pre_probes=(ctx.prior_ok("Ω.A.L4.P4.05"),),
        act=act,
        post_probes=post,
    )


def _run_p4_07(ctx: AtomContext) -> AtomOutcome:
    start = ctx.deps.clock()

    def act() -> dict[str, Any]:
        ctx.deps.sleep(2.0)
        elapsed = ctx.deps.clock() - start
        return {"elapsed_sec": elapsed}

    def post(snapshot: dict[str, Any]) -> tuple[bool, ...]:
        return (float(snapshot.get("elapsed_sec", 0)) >= 1.999,)

    return run_atom_shell(
        ctx,
        P4_ATOM_SPECS["Ω.A.L4.P4.07"],
        pre_probes=(ctx.prior_ok("Ω.A.L4.P4.06"),),
        act=act,
        post_probes=post,
    )


def _run_p4_08(ctx: AtomContext) -> AtomOutcome:
    deps: P4Deps = ctx.deps  # type: ignore[assignment]
    from gc1_runtime.layer0_gpost import run_gpost_eye_verify

    def evaluate() -> tuple[bool, dict[str, Any]]:
        verdict = evaluate_peak_table_task(
            verify_eye=deps.verify_eye,
            dry_run=deps.dry_run,
            task_id="verify_peak_table_has_data",
            fallback_text=deps.peak_table_after_mtd,
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
        ctx,
        P4_ATOM_SPECS["Ω.A.L4.P4.08"],
        pre_probes=(ctx.prior_ok("Ω.A.L4.P4.07"),),
        act=act,
        post_probes=post,
    )


_P4_RUNNERS: tuple[Callable[[AtomContext], AtomOutcome], ...] = (
    _run_p4_01,
    _run_p4_02,
    _run_p4_03,
    _run_p4_04,
    _run_p4_05,
    _run_p4_06,
    _run_p4_07,
    _run_p4_08,
)


def run_phase_p4(ctx: AtomContext) -> PhaseOutcome:
    """P4 load_analysis_method — P3.06 완료 후."""
    if _phase_blocked_early_ok(ctx):
        return PhaseOutcome(phase="P4", ok=True, skipped=True, message="skipped: EARLY_OK")
    for runner in _P4_RUNNERS:
        atom_id = _atom_id_from_runner(runner)
        outcome = runner(ctx)
        if not outcome.ok and not outcome.skipped:
            ctx.store.save(ctx.state)
            return PhaseOutcome(
                phase="P4",
                ok=False,
                message=outcome.fail_code or "atom failed",
                last_atom=atom_id,
            )
    ctx.state.phase_current = "P5"
    ctx.store.save(ctx.state)
    return PhaseOutcome(phase="P4", ok=True, last_atom=P4_ATOM_IDS[-1])


def run_p4_dry(
    store: StateStore,
    deps: P4Deps,
    *,
    gates: GateEvaluator | None = None,
) -> PhaseOutcome:
    """P4 dry-run — P0~P3 atom ok state 에서 이어 실행."""
    state = store.load()
    if not state.atoms:
        state = JobState.new_job(atom_ids=P0_P4_ATOM_IDS)
    for aid in P4_ATOM_IDS:
        if aid not in state.atoms:
            state.atoms[aid] = AtomRecord()
    ctx = AtomContext(
        state=state,
        store=store,
        gates=gates or GateEvaluator(),
        deps=deps,
    )
    return run_phase_p4(ctx)


def run_p0_p4_dry(
    store: StateStore,
    deps: P4Deps,
    *,
    gates: GateEvaluator | None = None,
) -> tuple[PhaseOutcome, ...]:
    """P0→P4 전체 dry-run (T52·T63 체인)."""
    from gc1_runtime.layer4_atoms_p2_p3 import run_p0_p3_dry

    prior = run_p0_p3_dry(store, deps, gates=gates)
    if len(prior) < 4 or not all(o.ok for o in prior):
        return prior
    p4 = run_p4_dry(store, deps, gates=gates)
    return (*prior, p4)


__all__ = [
    "P0_P4_ATOM_IDS",
    "P4Deps",
    "P4_ATOM_IDS",
    "P4_ATOM_SPECS",
    "choose_tree_line_for_data_name",
    "run_p0_p4_dry",
    "run_p4_dry",
    "run_phase_p4",
    "tree_right_click_coords",
]
