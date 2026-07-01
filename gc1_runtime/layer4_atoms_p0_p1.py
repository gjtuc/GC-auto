# -*- coding: utf-8 -*-
"""
L4 원자 — P0 JOB_PRELUDE + P1 sync_control_to_analysis (T50).

설계 ``deploy/GC1_RUNTIME_DESIGN_PART2_L4_P0_P4.md`` §P0.01~P0.06, §P1.01~P1.11.
각 atom: pre_probe (G-ATOM) → action → post_probe → StateStore STW 7필드.

``dry_run=True`` 이면 W32 조작 없이 플래그·geometry·StateStore 만 검증 (unittest).
실 UI 연동은 T55 ``layer4_job`` / T61 ``GC1_USE_RUNTIME`` 에서 deps 주입.
"""

from __future__ import annotations

import os
import time
from dataclasses import dataclass, field
from typing import Any, Callable, Mapping, Sequence, Union

PostProbes = Union[Sequence[bool], Callable[[dict[str, Any]], Sequence[bool]]]

from gc1_runtime.layer0_ctl import (
    ListViewGeom,
    menu_texts_include_analysis,
    menu_texts_include_control,
    pick_analysis_sample_table,
    pick_control_sync_list,
    tab_index_for_analysis,
    tab_index_for_control,
)
from gc1_runtime.layer0_data import is_valid_data_name
from gc1_runtime.layer0_win import WindowRect
from gc1_runtime.layer1_state import (
    AtomChannel,
    AtomRecord,
    AtomStatus,
    JobState,
    StateStore,
)
from gc1_runtime.layer2_gates import GateAction, GateEvaluator
from gc1_runtime.layer3_file import close_all_hancom_windows
from gc1_runtime.layer3_hand import HandActuator

ClockFn = Callable[[], float]
SleepFn = Callable[[float], None]
HancomProvider = Callable[[], Sequence[Any]]
MenuTextsFn = Callable[[], Sequence[str]]
ListViewProvider = Callable[[], Sequence[ListViewGeom]]

# ---------------------------------------------------------------------------
# Atom ID registry (설계 PART2a P0~P1)
# ---------------------------------------------------------------------------

P0_ATOM_IDS: tuple[str, ...] = (
    "Ω.A.L4.P0.01",
    "Ω.A.L4.P0.02",
    "Ω.A.L4.P0.03",
    "Ω.A.L4.P0.04",
    "Ω.A.L4.P0.05",
    "Ω.A.L4.P0.06",
)

P1_ATOM_IDS: tuple[str, ...] = (
    "Ω.A.L4.P1.01",
    "Ω.A.L4.P1.02",
    "Ω.A.L4.P1.03",
    "Ω.A.L4.P1.04",
    "Ω.A.L4.P1.05",
    "Ω.A.L4.P1.06",
    "Ω.A.L4.P1.07",
    "Ω.A.L4.P1.08",
    "Ω.A.L4.P1.09",
    "Ω.A.L4.P1.10",
    "Ω.A.L4.P1.11",
)

P0_P1_ATOM_IDS: tuple[str, ...] = P0_ATOM_IDS + P1_ATOM_IDS


@dataclass(frozen=True)
class AtomOnFail:
    """설계 on_fail JSON — {code, max_attempt, retry_delay_ms, fallback_channel}."""

    code: str | None = None
    max_attempt: int = 1
    retry_delay_ms: int = 0
    fallback_channel: str | None = None


@dataclass(frozen=True)
class AtomSpec:
    """7필드 중 실행 메타 — status 등은 StateStore 가 보관."""

    atom_id: str
    channel: AtomChannel
    on_fail: AtomOnFail
    timeout_ms: int


def _spec(
    atom_id: str,
    channel: AtomChannel,
    *,
    code: str | None = None,
    max_attempt: int = 1,
    retry_delay_ms: int = 0,
    fallback_channel: str | None = None,
    timeout_ms: int = 5000,
) -> AtomSpec:
    return AtomSpec(
        atom_id=atom_id,
        channel=channel,
        on_fail=AtomOnFail(
            code=code,
            max_attempt=max_attempt,
            retry_delay_ms=retry_delay_ms,
            fallback_channel=fallback_channel,
        ),
        timeout_ms=timeout_ms,
    )


ATOM_SPECS: dict[str, AtomSpec] = {
    "Ω.A.L4.P0.01": _spec("Ω.A.L4.P0.01", "H", timeout_ms=30000),
    "Ω.A.L4.P0.02": _spec(
        "Ω.A.L4.P0.02", "H", code="E_WIN_NONE", max_attempt=2, retry_delay_ms=1000, timeout_ms=60000,
    ),
    "Ω.A.L4.P0.03": _spec("Ω.A.L4.P0.03", "H", code="E_DATA_NAME", timeout_ms=20000),
    "Ω.A.L4.P0.04": _spec("Ω.A.L4.P0.04", "H", timeout_ms=5000),
    "Ω.A.L4.P0.05": _spec("Ω.A.L4.P0.05", "H", code="EARLY_OK", timeout_ms=5000),
    "Ω.A.L4.P0.06": _spec("Ω.A.L4.P0.06", "H", timeout_ms=5000),
    "Ω.A.L4.P1.01": _spec(
        "Ω.A.L4.P1.01", "H", code="E_P1_TAB", max_attempt=2, retry_delay_ms=800, timeout_ms=15000,
    ),
    "Ω.A.L4.P1.02": _spec("Ω.A.L4.P1.02", "H", timeout_ms=10000),
    "Ω.A.L4.P1.03": _spec("Ω.A.L4.P1.03", "H", timeout_ms=5000),
    "Ω.A.L4.P1.04": _spec("Ω.A.L4.P1.04", "H", timeout_ms=5000),
    "Ω.A.L4.P1.05": _spec("Ω.A.L4.P1.05", "H", timeout_ms=1000),
    "Ω.A.L4.P1.06": _spec("Ω.A.L4.P1.06", "H", timeout_ms=1000),
    "Ω.A.L4.P1.07": _spec("Ω.A.L4.P1.07", "H", timeout_ms=5000),
    "Ω.A.L4.P1.08": _spec("Ω.A.L4.P1.08", "W", timeout_ms=2000),
    "Ω.A.L4.P1.09": _spec(
        "Ω.A.L4.P1.09", "H", code="E_P1_TAB", max_attempt=2, retry_delay_ms=800, timeout_ms=15000,
    ),
    "Ω.A.L4.P1.10": _spec("Ω.A.L4.P1.10", "H", code="E_P1_TAB", timeout_ms=3000),
    "Ω.A.L4.P1.11": _spec("Ω.A.L4.P1.11", "E", code="E_VERIFY_TAB", timeout_ms=30000),
}

# P1.08 은 위 dict 에 포함됨 — 중복 등록 제거


# ---------------------------------------------------------------------------
# 실행 컨텍스트·결과
# ---------------------------------------------------------------------------


@dataclass
class P0P1Deps:
    """
    atom action 주입 — dry-run unittest 에서 mock, live 에서 pywinauto wrapper.

    ``on_*_tab`` / ``menu_texts`` 는 P1 탭 전환 시뮬레이션용.
    """

    dry_run: bool = True
    force: bool = False
    verify_eye: bool = False
    pdf_output_dir: str = ""
    data_name: str = ""
    hancom_windows: list[Any] = field(default_factory=list)
    on_control_tab: bool = False
    on_analysis_tab: bool = False
    win_rect: WindowRect | None = None
    listview_geoms: list[ListViewGeom] = field(default_factory=list)
    hand: HandActuator = field(default_factory=HandActuator)
    clock: ClockFn = field(default_factory=time.time)
    sleep: SleepFn = field(default_factory=time.sleep)
    # E 채널 — ``GC1_RUNTIME_VERIFY_EYE=1`` 시 P3/P4/P7 TASK (T62)
    eye: Any | None = None
    peak_table_text_provider: Callable[[str], str] | None = None
  # live 전용 (None 이면 dry_run 경로)
    live_win: Any | None = None
    read_data_name_fn: Callable[[Any], str] | None = None


@dataclass
class AtomContext:
    """단일 atom 실행 시 공유 상태."""

    state: JobState
    store: StateStore
    gates: GateEvaluator
    deps: P0P1Deps
    logs: list[str] = field(default_factory=list)

    def prior_ok(self, atom_id: str) -> bool:
        rec = self.state.atoms.get(atom_id)
        return rec is not None and rec.status == AtomStatus.OK

    def _iso_now(self) -> str:
        from gc1_runtime.layer1_state import _iso_now  # noqa: PLC2701

        return _iso_now()


@dataclass(frozen=True)
class AtomOutcome:
    """atom 1회 실행 결과."""

    atom_id: str
    ok: bool
    early_exit: bool = False
    fail_code: str | None = None
    skipped: bool = False
    probe_snapshot: Mapping[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class PhaseOutcome:
    """P0 또는 P1 페이즈 전체 결과."""

    phase: str
    ok: bool
    early_exit: bool = False
    skipped: bool = False
    message: str = ""
    last_atom: str | None = None


# ---------------------------------------------------------------------------
# PURE helpers (P1.05~06 — gc_autochro step_sync_control_to_analysis 동일)
# ---------------------------------------------------------------------------


from gc1_runtime.layer0_sync import sync_double_click_coords


def plan_pdf_path(pdf_output_dir: str, data_name: str) -> str:
    """P0.04 — ``gc_autochro.build_export_pdf_path`` thin wrapper."""
    from gc_autochro import AutochroConfig, build_export_pdf_path

    cfg = AutochroConfig(
        enabled=True,
        window_title_pattern="Autochro-3000",
        crm_path="",
        pdf_output_dir=os.path.normpath(os.path.expanduser(pdf_output_dir)),
        pdf_name_template="",
        quantify_wait_sec=180,
        print_wait_sec=600,
        dialog_wait_sec=30,
        hancom_wait_sec=180,
        dry_run=True,
    )
    return build_export_pdf_path(cfg, data_name_raw=data_name)


def pdf_fresh_should_skip(pdf_path: str, *, force: bool) -> bool:
    """P0.05 — 방금보낸 PDF 재실행 생략."""
    if force:
        return False
    from gc_autochro import is_pdf_recently_exported

    return is_pdf_recently_exported(pdf_path)


# ---------------------------------------------------------------------------
# Atom shell — pre / act / post + retry + STW
# ---------------------------------------------------------------------------


def _atom_status_ok(state: JobState, atom_id: str) -> bool:
    rec = state.atoms.get(atom_id)
    return rec is not None and rec.status == AtomStatus.OK


def _stw_running(ctx: AtomContext, atom_id: str, channel: AtomChannel, attempt: int) -> None:
    ctx.store.stw_atom(
        ctx.state,
        atom_id,
        status=AtomStatus.RUNNING,
        attempt=attempt,
        channel_used=channel,
        fail_code=None,
        started_at=ctx._iso_now(),
        ended_at=None,
    )


def _stw_terminal(
    ctx: AtomContext,
    atom_id: str,
    *,
    status: AtomStatus,
    channel: AtomChannel,
    attempt: int,
    fail_code: str | None,
    probe_snapshot: dict[str, Any],
) -> None:
    ctx.store.stw_atom(
        ctx.state,
        atom_id,
        status=status,
        attempt=attempt,
        channel_used=channel,
        fail_code=fail_code,
        probe_snapshot=probe_snapshot,
        ended_at=ctx._iso_now(),
    )


def run_atom_shell(
    ctx: AtomContext,
    spec: AtomSpec,
    *,
    pre_probes: Sequence[bool],
    act: Callable[[], dict[str, Any]],
    post_probes: PostProbes,
) -> AtomOutcome:
    """
    Ω.A.L2.GAT.PRE/POST + atom action + retry.

    pre/post 가 빈 시퀀스면 True 로 간주.
    """
    if _atom_status_ok(ctx.state, spec.atom_id):
        return AtomOutcome(atom_id=spec.atom_id, ok=True, skipped=True)

    pre_verdict = ctx.gates.evaluate_atom_pre(pre_probes)
    if pre_verdict.action != GateAction.RUN:
        _stw_terminal(
            ctx,
            spec.atom_id,
            status=AtomStatus.FAIL,
            channel=spec.channel,
            attempt=1,
            fail_code=pre_verdict.fail_code or "E_PRE_PROBE",
            probe_snapshot={"pre": list(pre_probes)},
        )
        return AtomOutcome(
            atom_id=spec.atom_id,
            ok=False,
            fail_code=pre_verdict.fail_code,
            probe_snapshot={"pre": list(pre_probes)},
        )

    on_fail = spec.on_fail
    snapshot: dict[str, Any] = {}

    def _before_retry(attempt: int) -> None:
        """Ω.A.L2.GAT.FB.01 + RTY.02 — fallback 후 delay sleep."""
        if on_fail.fallback_channel:
            from gc1_runtime.layer4_atom_fallback import apply_atom_fallback

            fb = apply_atom_fallback(ctx, on_fail.fallback_channel, atom_id=spec.atom_id)
            snapshot.update(fb)
        if on_fail.retry_delay_ms > 0:
            ctx.deps.sleep(on_fail.retry_delay_ms / 1000.0)

    for attempt in range(1, on_fail.max_attempt + 1):
        _stw_running(ctx, spec.atom_id, spec.channel, attempt)
        try:
            snapshot.update(dict(act()))
        except Exception as exc:
            snapshot = {"error": str(exc)}
            if attempt < on_fail.max_attempt and ctx.gates.should_retry(attempt, on_fail.max_attempt):
                _before_retry(attempt)
                continue
            _stw_terminal(
                ctx,
                spec.atom_id,
                status=AtomStatus.FAIL,
                channel=spec.channel,
                attempt=attempt,
                fail_code=on_fail.code or "E_ATOM_ACT",
                probe_snapshot=snapshot,
            )
            return AtomOutcome(atom_id=spec.atom_id, ok=False, fail_code=on_fail.code, probe_snapshot=snapshot)

        post_flags = post_probes(snapshot) if callable(post_probes) else post_probes
        post_verdict = ctx.gates.evaluate_atom_post(post_flags)
        if post_verdict.action == GateAction.RUN:
            _stw_terminal(
                ctx,
                spec.atom_id,
                status=AtomStatus.OK,
                channel=spec.channel,
                attempt=attempt,
                fail_code=None,
                probe_snapshot=snapshot,
            )
            return AtomOutcome(atom_id=spec.atom_id, ok=True, probe_snapshot=snapshot)

        if attempt < on_fail.max_attempt and ctx.gates.should_retry(attempt, on_fail.max_attempt):
            _before_retry(attempt)
            continue

        _stw_terminal(
            ctx,
            spec.atom_id,
            status=AtomStatus.FAIL,
            channel=spec.channel,
            attempt=attempt,
            fail_code=on_fail.code or post_verdict.fail_code or "E_POST_PROBE",
            probe_snapshot={**snapshot, "post": list(post_flags)},
        )
        return AtomOutcome(
            atom_id=spec.atom_id,
            ok=False,
            fail_code=on_fail.code or post_verdict.fail_code,
            probe_snapshot=snapshot,
        )

    return AtomOutcome(atom_id=spec.atom_id, ok=False, fail_code=on_fail.code)


# ---------------------------------------------------------------------------
# P0 atoms
# ---------------------------------------------------------------------------


def _run_p0_01(ctx: AtomContext) -> AtomOutcome:
    deps = ctx.deps

    def act() -> dict[str, Any]:
        closed = close_all_hancom_windows(deps.hancom_windows, sleep=deps.sleep)
        deps.hancom_windows.clear()
        return {"hancom_closed": closed}

    def post(_snapshot: dict[str, Any]) -> tuple[bool, ...]:
        return (len(deps.hancom_windows) == 0,)

    return run_atom_shell(
        ctx,
        ATOM_SPECS["Ω.A.L4.P0.01"],
        pre_probes=(True,),
        act=act,
        post_probes=post,
    )


def _run_p0_02(ctx: AtomContext) -> AtomOutcome:
    deps = ctx.deps

    def act() -> dict[str, Any]:
        if deps.dry_run:
            if deps.win_rect is None:
                deps.win_rect = WindowRect(40, 40, 1240, 840)
            return {"dry_run": True, "rect": deps.win_rect.width}
        if deps.live_win is None:
            raise RuntimeError("live_win not set")
        rect = deps.live_win.rectangle()
        deps.win_rect = WindowRect.from_obj(rect)
        return {"hwnd": getattr(deps.live_win, "handle", None), "rect_w": deps.win_rect.width}

    def post(_snapshot: dict[str, Any]) -> tuple[bool, ...]:
        rect = deps.win_rect
        return (
            rect is not None and rect.width > 0,
            rect is not None and rect.height > 0,
        )

    return run_atom_shell(
        ctx,
        ATOM_SPECS["Ω.A.L4.P0.02"],
        pre_probes=(True, True),
        act=act,
        post_probes=post,
    )


def _run_p0_03(ctx: AtomContext) -> AtomOutcome:
    deps = ctx.deps

    def act() -> dict[str, Any]:
        name = (deps.data_name or "").strip()
        if not name and deps.read_data_name_fn and deps.live_win is not None:
            name = deps.read_data_name_fn(deps.live_win)
        if not name and deps.dry_run:
            name = "20260630_DRE-01"
        ctx.state.data_name = name
        return {"data_name": name}

    def post(_snapshot: dict[str, Any]) -> tuple[bool, ...]:
        return (is_valid_data_name(ctx.state.data_name),)

    outcome = run_atom_shell(
        ctx,
        ATOM_SPECS["Ω.A.L4.P0.03"],
        pre_probes=(ctx.prior_ok("Ω.A.L4.P0.02"),),
        act=act,
        post_probes=post,
    )
    if not outcome.ok:
        return outcome
    return outcome


def _run_p0_04(ctx: AtomContext) -> AtomOutcome:
    deps = ctx.deps

    def act() -> dict[str, Any]:
        out_dir = deps.pdf_output_dir or os.path.join(os.path.expanduser("~"), "Desktop", "박은규")
        path = plan_pdf_path(out_dir, ctx.state.data_name)
        ctx.state.pdf_path_planned = path
        return {"pdf_path_planned": path}

    def post(_snapshot: dict[str, Any]) -> tuple[bool, ...]:
        return (bool(ctx.state.pdf_path_planned),)

    return run_atom_shell(
        ctx,
        ATOM_SPECS["Ω.A.L4.P0.04"],
        pre_probes=(ctx.prior_ok("Ω.A.L4.P0.03"), bool(ctx.state.data_name)),
        act=act,
        post_probes=post,
    )


def _run_p0_05(ctx: AtomContext) -> AtomOutcome:
    deps = ctx.deps

    def act() -> dict[str, Any]:
        skip = pdf_fresh_should_skip(ctx.state.pdf_path_planned, force=deps.force)
        return {"skip_export": skip, "force": deps.force}

    outcome = run_atom_shell(
        ctx,
        ATOM_SPECS["Ω.A.L4.P0.05"],
        pre_probes=(ctx.prior_ok("Ω.A.L4.P0.04"),),
        act=act,
        post_probes=(True,),
    )
    if outcome.ok and outcome.probe_snapshot.get("skip_export"):
        _stw_terminal(
            ctx,
            "Ω.A.L4.P0.05",
            status=AtomStatus.OK,
            channel="H",
            attempt=1,
            fail_code="EARLY_OK",
            probe_snapshot=dict(outcome.probe_snapshot),
        )
        return AtomOutcome(
            atom_id="Ω.A.L4.P0.05",
            ok=True,
            early_exit=True,
            fail_code="EARLY_OK",
            probe_snapshot=outcome.probe_snapshot,
        )
    return outcome


def _run_p0_06(ctx: AtomContext) -> AtomOutcome:
    if ctx.state.atoms.get("Ω.A.L4.P0.05", AtomRecord()).fail_code == "EARLY_OK":
        return AtomOutcome(atom_id="Ω.A.L4.P0.06", ok=True, skipped=True)

    def act() -> dict[str, Any]:
        if not ctx.state.job_id:
            fresh = JobState.new_job(
                data_name=ctx.state.data_name,
                pdf_path_planned=ctx.state.pdf_path_planned,
                prep_enabled=ctx.state.prep_enabled,
                atom_ids=P0_P1_ATOM_IDS,
            )
            ctx.state.job_id = fresh.job_id
            ctx.state.started_at = fresh.started_at
            for aid, rec in fresh.atoms.items():
                if aid not in ctx.state.atoms:
                    ctx.state.atoms[aid] = rec
        ctx.state.phase_current = "P0"
        ctx.state.force = ctx.deps.force
        return {"job_id": ctx.state.job_id, "phase": "P0", "atom_count": len(ctx.state.atoms)}

    def post(_snapshot: dict[str, Any]) -> tuple[bool, ...]:
        return (bool(ctx.state.job_id), ctx.state.phase_current == "P0")

    return run_atom_shell(
        ctx,
        ATOM_SPECS["Ω.A.L4.P0.06"],
        pre_probes=(ctx.prior_ok("Ω.A.L4.P0.05"),),
        act=act,
        post_probes=post,
    )


# ---------------------------------------------------------------------------
# P1 atoms — sync_control_to_analysis
# ---------------------------------------------------------------------------


def _menu_texts(ctx: AtomContext) -> Sequence[str]:
    if ctx.deps.on_analysis_tab:
        return ("분석목록", "제어목록")
    if ctx.deps.on_control_tab:
        return ("제어목록", "분석목록")
    return ("제어목록", "분석목록")


def _select_control_tab_deps(ctx: AtomContext) -> None:
    if not menu_texts_include_control(_menu_texts(ctx)):
        ctx.deps.on_control_tab = True
        ctx.deps.on_analysis_tab = False
    if not ctx.deps.dry_run and ctx.deps.live_win is not None:
        tabs = ctx.deps.live_win.child_window(class_name="SysTabControl32", title="Tab1")
        tabs.select(tab_index_for_control())
    ctx.deps.hand._record("tabs.select", str(tab_index_for_control()))


def _select_analysis_tab_deps(ctx: AtomContext) -> None:
    if not menu_texts_include_analysis(_menu_texts(ctx)):
        ctx.deps.on_analysis_tab = True
        ctx.deps.on_control_tab = False
    if not ctx.deps.dry_run and ctx.deps.live_win is not None:
        tabs = ctx.deps.live_win.child_window(class_name="SysTabControl32", title="Tab1")
        tabs.select(tab_index_for_analysis())
    ctx.deps.hand._record("tabs.select", str(tab_index_for_analysis()))


def _control_list_geom(ctx: AtomContext) -> ListViewGeom:
    if ctx.deps.listview_geoms:
        return pick_control_sync_list(ctx.deps.listview_geoms, ctx.deps.win_rect)
    return ListViewGeom(top=400, bottom=600, left=20, right=420, item_count=3)


def _run_p1_01(ctx: AtomContext) -> AtomOutcome:
    def act() -> dict[str, Any]:
        _select_control_tab_deps(ctx)
        ctx.deps.sleep(0.8)
        return {"tab": "control"}

    def post(_snapshot: dict[str, Any]) -> tuple[bool, ...]:
        return (menu_texts_include_control(_menu_texts(ctx)),)

    return run_atom_shell(
        ctx,
        ATOM_SPECS["Ω.A.L4.P1.01"],
        pre_probes=(ctx.prior_ok("Ω.A.L4.P0.06"), True),
        act=act,
        post_probes=post,
    )


def _run_p1_02(ctx: AtomContext) -> AtomOutcome:
    def act() -> dict[str, Any]:
        geom = _control_list_geom(ctx)
        return {"list_h": geom.height, "items": geom.item_count, "_geom_ok": geom.item_count > 0}

    def post(snapshot: dict[str, Any]) -> tuple[bool, ...]:
        return (bool(snapshot.get("_geom_ok")),)

    return run_atom_shell(
        ctx,
        ATOM_SPECS["Ω.A.L4.P1.02"],
        pre_probes=(menu_texts_include_control(_menu_texts(ctx)),),
        act=act,
        post_probes=post,
    )


def _run_p1_03(ctx: AtomContext) -> AtomOutcome:
    def act() -> dict[str, Any]:
        ctx.deps.hand._record("set_focus", "control_list")
        return {"focused": True}

    return run_atom_shell(
        ctx,
        ATOM_SPECS["Ω.A.L4.P1.03"],
        pre_probes=(ctx.prior_ok("Ω.A.L4.P1.02"),),
        act=act,
        post_probes=(True,),
    )


def _run_p1_04(ctx: AtomContext) -> AtomOutcome:
    def act() -> dict[str, Any]:
        ctx.deps.hand._record("click", "neutral")
        return {"click": True}

    return run_atom_shell(
        ctx,
        ATOM_SPECS["Ω.A.L4.P1.04"],
        pre_probes=(ctx.prior_ok("Ω.A.L4.P1.03"),),
        act=act,
        post_probes=(True,),
    )


def _run_p1_05(ctx: AtomContext) -> AtomOutcome:
    def act() -> dict[str, Any]:
        geom = _control_list_geom(ctx)
        rel_x, rel_y = sync_double_click_coords(geom.width, geom.height)
        return {"rel_x": rel_x, "rel_y": rel_y}

    def post(snapshot: dict[str, Any]) -> tuple[bool, ...]:
        return (int(snapshot.get("rel_x", 0)) > 0,)

    return run_atom_shell(
        ctx,
        ATOM_SPECS["Ω.A.L4.P1.05"],
        pre_probes=(ctx.prior_ok("Ω.A.L4.P1.04"),),
        act=act,
        post_probes=post,
    )


def _run_p1_06(ctx: AtomContext) -> AtomOutcome:
    def act() -> dict[str, Any]:
        geom = _control_list_geom(ctx)
        rel_x, rel_y = sync_double_click_coords(geom.width, geom.height)
        return {"rel_x": rel_x, "rel_y": rel_y}

    def post(snapshot: dict[str, Any]) -> tuple[bool, ...]:
        return (int(snapshot.get("rel_y", 0)) > 0,)

    return run_atom_shell(
        ctx,
        ATOM_SPECS["Ω.A.L4.P1.06"],
        pre_probes=(ctx.prior_ok("Ω.A.L4.P1.05"),),
        act=act,
        post_probes=post,
    )


def _run_p1_07(ctx: AtomContext) -> AtomOutcome:
    def act() -> dict[str, Any]:
        geom = _control_list_geom(ctx)
        rel_x, rel_y = sync_double_click_coords(geom.width, geom.height)
        ctx.deps.hand._record("double_click", f"{rel_x},{rel_y}")
        return {"dblclick": True, "rel_x": rel_x, "rel_y": rel_y}

    return run_atom_shell(
        ctx,
        ATOM_SPECS["Ω.A.L4.P1.07"],
        pre_probes=(
            ctx.prior_ok("Ω.A.L4.P1.05"),
            ctx.prior_ok("Ω.A.L4.P1.06"),
        ),
        act=act,
        post_probes=(True,),
    )


def _run_p1_08(ctx: AtomContext) -> AtomOutcome:
    start = ctx.deps.clock()

    def act() -> dict[str, Any]:
        ctx.deps.sleep(1.5)
        elapsed = ctx.deps.clock() - start
        return {"elapsed_ms": int(elapsed * 1000)}

    def post(snapshot: dict[str, Any]) -> tuple[bool, ...]:
        return (int(snapshot.get("elapsed_ms", 0)) >= 1500,)

    outcome = run_atom_shell(
        ctx,
        ATOM_SPECS["Ω.A.L4.P1.08"],
        pre_probes=(ctx.prior_ok("Ω.A.L4.P1.07"),),
        act=act,
        post_probes=post,
    )
    return outcome


def gpost_retry_p1_09(ctx: AtomContext) -> dict[str, Any]:
    """G-POST (T91) — P1.09 분석목록 탭 재선택. ``verify_active_tab_analysis`` 실패 시 1회."""
    _select_analysis_tab_deps(ctx)
    ctx.deps.sleep(0.8)
    return {"tab": "analysis", "gpost_retry": "P1.09"}


def _run_p1_09(ctx: AtomContext) -> AtomOutcome:
    def act() -> dict[str, Any]:
        _select_analysis_tab_deps(ctx)
        ctx.deps.sleep(0.8)
        return {"tab": "analysis"}

    def post(_snapshot: dict[str, Any]) -> tuple[bool, ...]:
        return (menu_texts_include_analysis(_menu_texts(ctx)),)

    return run_atom_shell(
        ctx,
        ATOM_SPECS["Ω.A.L4.P1.09"],
        pre_probes=(ctx.prior_ok("Ω.A.L4.P1.08"),),
        act=act,
        post_probes=post,
    )


def _sync_list_counts_from_ctx(ctx: AtomContext) -> tuple[int, int]:
    """P1.10 — 제어·분석 ListView 행 수 (mock geometry 또는 0)."""
    geoms = ctx.deps.listview_geoms or []
    if not geoms:
        return 0, 0
    try:
        ctrl = pick_control_sync_list(geoms, ctx.deps.win_rect)
        anal = pick_analysis_sample_table(geoms, ctx.deps.win_rect)
        return ctrl.item_count, anal.item_count
    except RuntimeError:
        return 0, 0


def _run_p1_10(ctx: AtomContext) -> AtomOutcome:
    from gc1_runtime.layer0_sync import evaluate_sync_post_check

    def act() -> dict[str, Any]:
        ctrl, anal = _sync_list_counts_from_ctx(ctx)
        post = evaluate_sync_post_check(ctrl, anal)
        return {
            **post.to_dict(),
            "analysis_tab": menu_texts_include_analysis(_menu_texts(ctx)),
        }

    def post(snapshot: dict[str, Any]) -> tuple[bool, ...]:
        if snapshot.get("analysis_tab") is not True:
            return (False, False)
        # dry_run mock: control/analysis geoms 있으면 sync OK 검증
        if ctx.deps.listview_geoms:
            return (True, snapshot.get("ok") is True)
        return (True, True)

    return run_atom_shell(
        ctx,
        ATOM_SPECS["Ω.A.L4.P1.10"],
        pre_probes=(True,),
        act=act,
        post_probes=post,
    )


def _run_p1_11(ctx: AtomContext) -> AtomOutcome:
    if not ctx.deps.verify_eye:
        return AtomOutcome(atom_id="Ω.A.L4.P1.11", ok=True, skipped=True)

    from gc1_runtime.layer0_gpost import run_gpost_eye_verify
    from gc1_runtime.layer3_eye import verify_active_tab_analysis

    def evaluate() -> tuple[bool, dict[str, Any]]:
        menu_blob = " ".join(_menu_texts(ctx))
        passed = verify_active_tab_analysis(menu_blob)
        return passed, {"verify_active_tab": passed, "menu": menu_blob}

    def act() -> dict[str, Any]:
        gpost = run_gpost_eye_verify(
            task_id="verify_active_tab_analysis",
            evaluate=evaluate,
            retry_fn=lambda: gpost_retry_p1_09(ctx),
            sleep_fn=ctx.deps.sleep,
        )
        return {**gpost.probe_snapshot, "verify_active_tab": gpost.passed, "task_detail": gpost.detail}

    def post(snapshot: dict[str, Any]) -> tuple[bool, ...]:
        return (snapshot.get("verify_active_tab") is True,)

    return run_atom_shell(
        ctx,
        ATOM_SPECS["Ω.A.L4.P1.11"],
        pre_probes=(ctx.deps.verify_eye, ctx.prior_ok("Ω.A.L4.P1.10")),
        act=act,
        post_probes=post,
    )


_P0_RUNNERS: tuple[Callable[[AtomContext], AtomOutcome], ...] = (
    _run_p0_01,
    _run_p0_02,
    _run_p0_03,
    _run_p0_04,
    _run_p0_05,
    _run_p0_06,
)

_P1_RUNNERS: tuple[Callable[[AtomContext], AtomOutcome], ...] = (
    _run_p1_01,
    _run_p1_02,
    _run_p1_03,
    _run_p1_04,
    _run_p1_05,
    _run_p1_06,
    _run_p1_07,
    _run_p1_08,
    _run_p1_09,
    _run_p1_10,
    _run_p1_11,
)


def run_phase_p0(ctx: AtomContext) -> PhaseOutcome:
    """P0 JOB_PRELUDE — EARLY_OK 시 P0.06·P1 생략."""
    for runner in _P0_RUNNERS:
        atom_id = runner.__name__.replace("_run_", "").replace("_", ".")
        # map _run_p0_01 -> Ω.A.L4.P0.01
        parts = runner.__name__.split("_")
        atom_id = f"Ω.A.L4.{parts[2].upper()}.{parts[3]}"
        outcome = runner(ctx)
        if outcome.early_exit:
            ctx.store.save(ctx.state)
            return PhaseOutcome(
                phase="P0",
                ok=True,
                early_exit=True,
                message="EARLY_OK — PDF fresh skip",
                last_atom=atom_id,
            )
        if not outcome.ok and not outcome.skipped:
            ctx.store.save(ctx.state)
            return PhaseOutcome(
                phase="P0",
                ok=False,
                message=outcome.fail_code or "atom failed",
                last_atom=atom_id,
            )
    ctx.state.phase_current = "P1"
    ctx.store.save(ctx.state)
    return PhaseOutcome(phase="P0", ok=True, last_atom=P0_ATOM_IDS[-1])


def run_phase_p1(ctx: AtomContext) -> PhaseOutcome:
    """P1 sync — P0 EARLY_OK 면 호출하지 않음."""
    if ctx.state.atoms.get("Ω.A.L4.P0.05", AtomRecord()).fail_code == "EARLY_OK":
        return PhaseOutcome(phase="P1", ok=True, skipped=True, message="skipped: EARLY_OK")

    for runner in _P1_RUNNERS:
        parts = runner.__name__.split("_")
        atom_id = f"Ω.A.L4.{parts[2].upper()}.{parts[3]}"
        outcome = runner(ctx)
        if not outcome.ok and not outcome.skipped:
            ctx.store.save(ctx.state)
            return PhaseOutcome(
                phase="P1",
                ok=False,
                message=outcome.fail_code or "atom failed",
                last_atom=atom_id,
            )
    ctx.state.phase_current = "P2"
    ctx.store.save(ctx.state)
    return PhaseOutcome(phase="P1", ok=True, last_atom=P1_ATOM_IDS[-1])


def run_p0_p1_dry(
    store: StateStore,
    deps: P0P1Deps,
    *,
    gates: GateEvaluator | None = None,
) -> tuple[PhaseOutcome, PhaseOutcome]:
    """
    dry-run 진입 — P0+P1 순차 실행 (T50 unittest·T63 e2e 기반).

    ``deps.dry_run`` 기본 True; ``store`` 에 atom 7필드 persist.
    """
    state = store.load()
    if not state.atoms:
        state = JobState.new_job(atom_ids=P0_P1_ATOM_IDS)
    ctx = AtomContext(
        state=state,
        store=store,
        gates=gates or GateEvaluator(),
        deps=deps,
    )
    p0 = run_phase_p0(ctx)
    if not p0.ok:
        return p0, PhaseOutcome(phase="P1", ok=False, message="P0 failed")
    if p0.early_exit:
        return p0, PhaseOutcome(phase="P1", ok=True, skipped=True, message="skipped: EARLY_OK")
    p1 = run_phase_p1(ctx)
    return p0, p1


__all__ = [
    "ATOM_SPECS",
    "AtomContext",
    "AtomOnFail",
    "AtomOutcome",
    "AtomSpec",
    "P0P1Deps",
    "P0_ATOM_IDS",
    "P0_P1_ATOM_IDS",
    "P1_ATOM_IDS",
    "PhaseOutcome",
    "plan_pdf_path",
    "pdf_fresh_should_skip",
    "run_atom_shell",
    "run_p0_p1_dry",
    "run_phase_p0",
    "run_phase_p1",
    "sync_double_click_coords",
]
