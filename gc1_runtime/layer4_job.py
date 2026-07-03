# -*- coding: utf-8 -*-
"""
L4 job 진입 — ``run_autochro_export`` 런타임 대체 (T55).

설계 ``deploy/GC1_RUNTIME_DESIGN_PART6_RETRY.md`` §Resume,
``GC1_AUTOCHRO_PREP_STEPS`` (prep env) → P3~P6·P7.01 생략.

P0~P9 phase runner 를 순차 호출하고 ``StateStore``·G-EX 게이트·CRM 기록을 묶는다.
실 UI deps 주입: ``_build_live_deps`` (T61 ``GC1_USE_RUNTIME=1`` 위임).
"""

from __future__ import annotations

import os
import re
from dataclasses import dataclass, field
from typing import Any, Callable, Sequence

from gc1_runtime.layer0_config import read_gc1_autochro_prep_steps
from gc1_runtime.layer0_ident import detect_data_pc
from gc1_runtime.layer1_state import AtomRecord, AtomStatus, JobPaths, JobState, StateStore
from gc1_runtime.layer2_gates import ExportGateInput, GateAction, GateEvaluator
from gc1_runtime.layer4_atoms_p0_p1 import (
    AtomContext,
    PhaseOutcome,
    plan_pdf_path,
    run_phase_p0,
    run_phase_p1,
)
from gc1_runtime.layer4_atoms_p2_p3 import (
    P3_ATOM_IDS,
    run_phase_p2,
    run_phase_p3,
)
from gc1_runtime.layer4_atoms_p4 import P4_ATOM_IDS, run_phase_p4
from gc1_runtime.layer4_atoms_p5_p7 import (
    P5_ATOM_IDS,
    P6_ATOM_IDS,
    P7_ATOM_IDS,
    run_phase_p5,
    run_phase_p6,
    run_phase_p7,
)
from gc1_runtime.layer4_atoms_p8_p9 import (
    P0_P9_ATOM_IDS,
    P89Deps,
    run_phase_p8,
    run_phase_p9,
)

# P7.01 = prep 모드에서만 Ctrl+A (no-prep 는 P2 에서 이미 선택)
_NO_PREP_SKIP_PHASES: frozenset[str] = frozenset({"P3", "P4", "P5", "P6"})
_NO_PREP_EXTRA_SKIP_ATOMS: tuple[str, ...] = ("Ω.A.L4.P7.01",)

_PHASE_NEXT: dict[str, str] = {
    "P0": "P1",
    "P1": "P2",
    "P2": "P3",
    "P3": "P4",
    "P4": "P5",
    "P5": "P6",
    "P6": "P7",
    "P7": "P8",
    "P8": "P9",
    "P9": "DONE",
}

_NO_PREP_PHASE_ATOMS: dict[str, tuple[str, ...]] = {
    "P3": P3_ATOM_IDS,
    "P4": P4_ATOM_IDS,
    "P5": P5_ATOM_IDS,
    "P6": P6_ATOM_IDS,
}

PhaseRunner = Callable[[AtomContext], PhaseOutcome]

_PHASE_RUNNERS: tuple[tuple[str, PhaseRunner], ...] = (
    ("P0", run_phase_p0),
    ("P1", run_phase_p1),
    ("P2", run_phase_p2),
    ("P3", run_phase_p3),
    ("P4", run_phase_p4),
    ("P5", run_phase_p5),
    ("P6", run_phase_p6),
    ("P7", run_phase_p7),
    ("P8", run_phase_p8),
    ("P9", run_phase_p9),
)

LogFn = Callable[[str], None]


@dataclass(frozen=True)
class JobResult:
    """export 잡 1회 실행 결과 — ``gc_autochro.run_autochro_export`` 튜플과 동일 의미."""

    ok: bool
    pdf_path: str | None
    message: str
    outcomes: tuple[PhaseOutcome, ...] = ()


@dataclass
class ExportJobContext:
    """내부 오케스트레이션 컨텍스트 — unittest 에서 deps·gate 주입."""

    excel_output_dir: str
    send_state_path: str
    force: bool = False
    deps: P89Deps | None = None
    gates: GateEvaluator | None = None
    log_fn: LogFn = field(default=lambda msg: None)
    window_handles: int = 1
    mtd_path_exists: bool = True
    pipeline_locked: bool = False


def _default_log(msg: str) -> None:
    print(f"[Autochro/runtime] {msg}")


def _mark_atoms_ok_skip(
    store: StateStore,
    state: JobState,
    atom_ids: Sequence[str],
    *,
    reason: str,
    save: bool = False,
) -> None:
    """
    run_atom_shell 은 status=ok 인 atom 을 재실행하지 않음.

    resume·prep 생략 atom 은 probe_snapshot 에 reason 만 남긴다 (설계 skip 과 호환).
    """
    for aid in atom_ids:
        rec = state.atoms.get(aid, AtomRecord())
        if rec.status == AtomStatus.OK:
            continue
        rec.status = AtomStatus.OK
        rec.probe_snapshot = {**rec.probe_snapshot, "skipped_reason": reason}
        state.atoms[aid] = rec
    if save:
        store.save(state)


def apply_resume_from(store: StateStore, state: JobState) -> None:
    """
    PART6 §Resume — ``resume_from`` 이전 atom 을 ok 로 고정 (재실행 skip).

    예: ``Ω.A.L4.P4.03`` → P0~P3·P4.01~02 ok, P4.03 부터 실행.
    """
    rf = (state.resume_from or "").strip()
    if not rf or rf not in P0_P9_ATOM_IDS:
        return
    idx = P0_P9_ATOM_IDS.index(rf)
    _mark_atoms_ok_skip(store, state, P0_P9_ATOM_IDS[:idx], reason="resume", save=True)


def apply_no_prep_skips(store: StateStore, state: JobState) -> None:
    """
    ``GC1_AUTOCHRO_PREP_STEPS=0`` — gc_autochro 3~5단계 생략 (P2→P7 정량만).

    P3~P6 전 atom + P7.01(select) 을 ok 로 표시해 phase runner 가 UI 를 건너뛴다.
    """
    if state.prep_enabled:
        return
    for atom_ids in _NO_PREP_PHASE_ATOMS.values():
        _mark_atoms_ok_skip(store, state, atom_ids, reason="prep_disabled")
    _mark_atoms_ok_skip(store, state, _NO_PREP_EXTRA_SKIP_ATOMS, reason="prep_disabled")
    store.save(state)


def _skip_phase_prep_disabled(
    ctx: AtomContext,
    phase: str,
    atom_ids: Sequence[str],
) -> PhaseOutcome:
    """prep 비활성 — phase 전체를 실행하지 않고 STW 만 갱신."""
    _mark_atoms_ok_skip(ctx.store, ctx.state, atom_ids, reason="prep_disabled")
    ctx.state.phase_current = _PHASE_NEXT.get(phase, "DONE")
    ctx.store.save(ctx.state)
    return PhaseOutcome(phase=phase, ok=True, skipped=True, message="skipped: prep_disabled")


def ensure_job_state(
    store: StateStore,
    *,
    prep_enabled: bool,
    force: bool,
    data_name: str = "",
    pdf_path_planned: str = "",
) -> JobState:
    """job JSON 없으면 P0.06 과 동일하게 pending 초기화."""
    state = store.load()
    if not state.job_id:
        state = JobState.new_job(
            data_name=data_name,
            pdf_path_planned=pdf_path_planned,
            prep_enabled=prep_enabled,
            atom_ids=P0_P9_ATOM_IDS,
        )
    else:
        for aid in P0_P9_ATOM_IDS:
            if aid not in state.atoms:
                state.atoms[aid] = AtomRecord()
    state.prep_enabled = prep_enabled
    state.force = force
    if data_name:
        state.data_name = data_name
    if pdf_path_planned:
        state.pdf_path_planned = pdf_path_planned
    store.save(state)
    return state


def build_export_gate_input(
    *,
    cfg: Any,
    force: bool,
    prep_enabled: bool,
    crm_export_needed: bool,
    window_handles: int,
    mtd_path_exists: bool,
    pipeline_locked: bool = False,
) -> ExportGateInput:
    return ExportGateInput(
        autochro_enabled=bool(cfg.enabled),
        force=force,
        is_data_pc=detect_data_pc(),
        prep_enabled=prep_enabled,
        autochro_window_handles=window_handles,
        mtd_path_exists=mtd_path_exists,
        crm_export_needed=crm_export_needed,
        pipeline_locked=pipeline_locked,
    )


def run_export_phases(
    store: StateStore,
    deps: P89Deps,
    *,
    gates: GateEvaluator | None = None,
    log_fn: LogFn | None = None,
) -> JobResult:
    """
    P0→P9 순차 실행 — resume·prep·EARLY_OK 는 각 phase runner·사전 STW 로 처리.

    ``deps.dry_run=True`` 이면 unittest/mock 경로 (W32 미호출).
    """
    log = log_fn or _default_log
    state = store.load()
    apply_resume_from(store, state)
    state = store.load()
    apply_no_prep_skips(store, state)
    state = store.load()

    ctx = AtomContext(
        state=state,
        store=store,
        gates=gates or GateEvaluator(),
        deps=deps,
    )
    outcomes: list[PhaseOutcome] = []

    for phase_name, runner in _PHASE_RUNNERS:
        if not state.prep_enabled and phase_name in _NO_PREP_SKIP_PHASES:
            atom_ids = _NO_PREP_PHASE_ATOMS[phase_name]
            outcome = _skip_phase_prep_disabled(ctx, phase_name, atom_ids)
        else:
            if phase_name == "P7" and not state.prep_enabled:
                _mark_atoms_ok_skip(ctx.store, ctx.state, _NO_PREP_EXTRA_SKIP_ATOMS, reason="prep_disabled")
            outcome = runner(ctx)
        outcomes.append(outcome)
        log(f"phase {phase_name}: ok={outcome.ok} skipped={outcome.skipped} msg={outcome.message}")
        if not outcome.ok:
            return JobResult(
                ok=False,
                pdf_path=None,
                message=outcome.message or "phase failed",
                outcomes=tuple(outcomes),
            )
        if outcome.skipped and "EARLY_OK" in (outcome.message or ""):
            pdf = ctx.state.pdf_path_planned or None
            return JobResult(ok=True, pdf_path=pdf, message="EARLY_OK — PDF fresh skip", outcomes=tuple(outcomes))
        state = store.load()

    final = store.load()
    pdf_path = final.pdf_path_planned or getattr(deps, "pdf_path_final", "") or None
    return JobResult(ok=True, pdf_path=pdf_path, message=os.path.basename(pdf_path) if pdf_path else "ok", outcomes=tuple(outcomes))


def _resolve_mtd_exists(data_name: str, mtd_dir: str | None) -> bool:
    """G-EX.04 — prep 시 바탕화면 {YYYYMMDD} 분석방법.MTD 존재 여부."""
    if not data_name:
        return True
    try:
        from gc_autochro import resolve_analysis_method_mtd_path  # noqa: PLC2701

        path = resolve_analysis_method_mtd_path(data_name)
        return os.path.isfile(path)
    except (FileNotFoundError, ValueError, OSError):
        if mtd_dir:
            compact = re.sub(r"\s+", "", data_name.strip())
            match = re.match(r"^(\d{8})", compact)
            if match:
                fn = f"{match.group(1)} 분석방법.MTD"
                return os.path.isfile(os.path.join(mtd_dir, fn))
        return False


def run_autochro_export(
    excel_output_dir: str,
    state_path: str,
    force: bool = False,
    *,
    job_ctx: ExportJobContext | None = None,
) -> tuple[bool, str | None, str]:
    """
    ``gc_autochro.run_autochro_export`` 호환 시그니처.

    Returns:
        (ok, pdf_path, message)
    """
    from gc_autochro import (  # noqa: PLC2701
        load_autochro_config,
        record_autochro_export,
        should_export_crm,
    )

    ctx = job_ctx or ExportJobContext(
        excel_output_dir=excel_output_dir,
        send_state_path=state_path,
        force=force,
    )
    log = ctx.log_fn or _default_log
    cfg = load_autochro_config(excel_output_dir)

    if not cfg.enabled and not force:
        return False, None, "AUTOCHRO_ENABLED=0"
    if not cfg.crm_path:
        return False, None, "AUTOCHRO_CRM_PATH / AUTOCHRO_DATA_NAME 미설정"

    need_export, crm_reason = should_export_crm(state_path, cfg.crm_path, force=force)
    if not need_export and not force:
        return True, None, crm_reason

    prep_enabled = read_gc1_autochro_prep_steps()
    if ctx.deps is not None and hasattr(ctx.deps, "dry_run"):
        pass  # unittest deps — prep from env still drives state.prep_enabled

    gates = ctx.gates or GateEvaluator()
    if not cfg.dry_run and ctx.deps is None:
        ctx.window_handles = _autochro_window_handle_count(cfg)
    handles = max(ctx.window_handles, 1) if cfg.dry_run else ctx.window_handles
    data_name_guess = os.path.splitext(os.path.basename(cfg.crm_path))[0] if cfg.crm_path else ""
    mtd_dir = getattr(ctx.deps, "mtd_dir", "") if ctx.deps else ""
    if prep_enabled:
        mtd_ok = _resolve_mtd_exists(data_name_guess, mtd_dir or None)
    else:
        mtd_ok = True

    gate_in = build_export_gate_input(
        cfg=cfg,
        force=force,
        prep_enabled=prep_enabled,
        crm_export_needed=need_export,
        window_handles=handles,
        mtd_path_exists=mtd_ok,
        pipeline_locked=ctx.pipeline_locked,
    )
    verdict = gates.evaluate_export(gate_in)
    if verdict.action == GateAction.SKIP:
        return True, None, verdict.message
    if verdict.action == GateAction.BLOCK:
        return False, None, verdict.message or verdict.fail_code or "gate blocked"

    log(f"시작 - {crm_reason}")

    job_store = StateStore(JobPaths(cfg.pdf_output_dir))
    pdf_planned = ""
    if data_name_guess:
        try:
            pdf_planned = plan_pdf_path(cfg.pdf_output_dir, data_name_guess)
        except ValueError:
            pdf_planned = ""

    state = ensure_job_state(
        job_store,
        prep_enabled=prep_enabled,
        force=force,
        data_name=data_name_guess,
        pdf_path_planned=pdf_planned,
    )

    if ctx.deps is not None:
        deps = ctx.deps
        deps.force = force
        deps.dry_run = cfg.dry_run
        if not deps.pdf_output_dir:
            deps.pdf_output_dir = cfg.pdf_output_dir
        if not deps.data_name and data_name_guess:
            deps.data_name = data_name_guess
    elif cfg.dry_run:
        deps = _build_minimal_dry_deps(cfg, data_name_guess, force=force)
    else:
        try:
            deps, data_name_live, pdf_planned_live, _handle_count = _prepare_live_export(
                cfg, force=force, log=log,
            )
        except Exception as exc:
            return False, None, str(exc)
        if data_name_live:
            state.data_name = data_name_live
        if pdf_planned_live:
            state.pdf_path_planned = pdf_planned_live
            job_store.save(state)

    result = run_export_phases(job_store, deps, gates=gates, log_fn=log)
    if not result.ok:
        return False, None, result.message

    if result.message.startswith("EARLY_OK"):
        return True, result.pdf_path, result.message

    pdf_path = result.pdf_path or state.pdf_path_planned
    if pdf_path and not cfg.dry_run:
        try:
            from gc_gc1 import cleanup_superseded_gc1_files  # noqa: PLC2701

            removed, pdf_path = cleanup_superseded_gc1_files(cfg.pdf_output_dir, pdf_path, log_fn=log)
            if removed:
                log(f"잘못된 출력 파일 {removed}개 정리")
        except Exception:
            pass

    if pdf_path and cfg.crm_path:
        record_autochro_export(state_path, cfg.crm_path, pdf_path)

    msg = os.path.basename(pdf_path) if pdf_path else result.message
    return True, pdf_path, msg


def _pywinauto_find_connect():
    """live dialog·Hancom leaf — pywinauto win32 backend."""
    from pywinauto import Application, findwindows

    def find_windows(**kwargs: Any) -> list[int]:
        return findwindows.find_windows(**kwargs)

    def connect_window(handle: int) -> Any:
        app = Application(backend="win32").connect(handle=handle)
        return app.window(handle=handle)

    return find_windows, connect_window


def _autochro_window_handle_count(cfg: Any) -> int:
    """G-EX.03 — Autochro 메인 창 개수."""
    import re

    find_windows, _ = _pywinauto_find_connect()
    pattern = re.escape(cfg.window_title_pattern)
    return len(find_windows(title_re=f".*{pattern}.*"))


def _eye_fields_for_deps(*, verify_eye: bool) -> dict[str, Any]:
    """T62 — ``GC1_RUNTIME_VERIFY_EYE=1`` 시 EyeActuator·config 주입."""
    if not verify_eye:
        return {"verify_eye": False, "eye": None}
    from gc1_runtime.layer3_eye import EyeActuator, default_eye_config

    return {"verify_eye": True, "eye": EyeActuator(default_eye_config())}


def _build_live_deps(cfg: Any, win: Any, data_name: str, *, force: bool) -> P89Deps:
    """
    T61 live P89Deps — ``live_win``·pywinauto·env 타이밍.

    atom 본체는 ``dry_run=False`` + ``live_win`` 일 때 gc_autochro/pywinauto 호출.
    """
    import time

    from gc1_runtime.layer0_config import (
        read_analysis_method_dir,
        read_gc1_runtime_verify_eye,
        read_list_neutral_x_frac,
    )
    from gc1_runtime.layer3_hand import HandActuator

    find_windows, connect_window = _pywinauto_find_connect()
    from pywinauto.keyboard import send_keys

    verify_eye = read_gc1_runtime_verify_eye()
    eye_kw = _eye_fields_for_deps(verify_eye=verify_eye)
    return P89Deps(
        dry_run=False,
        force=force,
        verify_eye=eye_kw["verify_eye"],
        eye=eye_kw["eye"],
        pdf_output_dir=cfg.pdf_output_dir,
        data_name=data_name,
        live_win=win,
        read_data_name_fn=lambda w: __import__(
            "gc_autochro", fromlist=["read_active_control_data_name"],
        ).read_active_control_data_name(w, cfg),
        hand=HandActuator(send_keys_fn=send_keys),
        clock=time.time,
        sleep=time.sleep,
        list_neutral_x_frac=read_list_neutral_x_frac(),
        mtd_dir=read_analysis_method_dir(),
        quantify_wait_sec=cfg.quantify_wait_sec,
        print_wait_sec=cfg.print_wait_sec,
        hancom_wait_sec=cfg.hancom_wait_sec,
        hancom_windows=[],
        write_pdf_on_save=False,
        find_windows=find_windows,
        connect_window=connect_window,
    )


def _prepare_live_export(
    cfg: Any,
    *,
    force: bool,
    log: LogFn,
) -> tuple[P89Deps, str, str, int]:
    """
    live export 전 Autochro 연결 — legacy ``run_autochro_export`` 와 동일 선행.

    Returns:
        (deps, data_name, pdf_path_planned, window_handle_count)
    """
    from gc_autochro import (  # noqa: PLC2701
        build_export_pdf_path,
        close_all_hancom_pdf_windows,
        connect_main_window,
        read_active_control_data_name,
    )

    handle_count = _autochro_window_handle_count(cfg)
    stale_closed = close_all_hancom_pdf_windows()
    if stale_closed:
        log(f"이전 한컴 PDF 완료 창 {stale_closed}개 닫음")
    _, win = connect_main_window(cfg)
    data_name = read_active_control_data_name(win, cfg)
    pdf_path = build_export_pdf_path(cfg, data_name_raw=data_name)
    log(f"제어목록 데이터명: {data_name}")
    log(f"PDF 저장 이름: {os.path.basename(pdf_path)}")
    deps = _build_live_deps(cfg, win, data_name, force=force)
    return deps, data_name, pdf_path, handle_count


def _build_minimal_dry_deps(cfg: Any, data_name: str, *, force: bool) -> P89Deps:
    """
    AUTOCHRO_DRY_RUN=1 기본 mock — ``gc_autochro --dry-run``·T61 e2e 용.

    unittest 는 ``ExportJobContext.deps`` 로 더 정밀한 mock 주입 가능.
    """
    import time

    from gc1_runtime.layer0_ctl import ListViewGeom, TreeGeom
    from gc1_runtime.layer3_hand import HandActuator

    tick = {"t": 5000.0}

    def clock() -> float:
        return tick["t"]

    def sleep(sec: float) -> None:
        tick["t"] += sec

    mtd_dir = cfg.pdf_output_dir
    if data_name:
        compact = re.sub(r"\s+", "", data_name.strip())
        match = re.match(r"^(\d{8})", compact)
        if match:
            mtd_path = os.path.join(mtd_dir, f"{match.group(1)} 분석방법.MTD")
            try:
                with open(mtd_path, "w", encoding="utf-8") as fh:
                    fh.write("mtd")
            except OSError:
                pass

    hand = HandActuator(send_keys_fn=lambda k, **__: None)
    name = data_name or "20260630_DRE-01"
    from gc1_runtime.layer0_config import read_gc1_runtime_verify_eye

    verify_eye = read_gc1_runtime_verify_eye()
    eye_kw = _eye_fields_for_deps(verify_eye=verify_eye)
    return P89Deps(
        dry_run=True,
        force=force,
        verify_eye=eye_kw["verify_eye"],
        eye=eye_kw["eye"],
        pdf_output_dir=cfg.pdf_output_dir,
        mtd_dir=mtd_dir,
        data_name=name,
        on_control_tab=True,
        listview_geoms=[
            ListViewGeom(top=100, bottom=280, left=20, right=420, item_count=8),
            ListViewGeom(top=400, bottom=600, left=20, right=420, item_count=5),
        ],
        tree_lines=[name, "YL6500 GC"],
        tree_geom=TreeGeom(top=120, bottom=520, left=10, right=250),
        hand=hand,
        clock=clock,
        sleep=sleep,
        peak_table_text="0 0 0 0 0",
        peak_table_after_mtd="0.12 3.45 5.6",
        peak_table_after_p6="0 0 0 0 0",
        peak_table_after_quantify="0.12 3.45 5.6",
        progress_visible=lambda: False,
        save_dialog_visible=lambda: True,
        write_pdf_on_save=True,
        print_wait_sec=5,
    )


__all__ = [
    "ExportJobContext",
    "JobResult",
    "apply_no_prep_skips",
    "apply_resume_from",
    "build_export_gate_input",
    "ensure_job_state",
    "_build_live_deps",
    "run_autochro_export",
    "run_export_phases",
]
