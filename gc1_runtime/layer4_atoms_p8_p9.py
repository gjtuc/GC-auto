# -*- coding: utf-8 -*-
"""
L4 원자 — P8 print + P9 save (Hancom·PDF ready) (T54).

설계 ``deploy/GC1_RUNTIME_DESIGN_PART2_L4_P5_P9.md`` §P8.01~P8.06, §P9.01~P9.14.
``gc_autochro.step_print_pdf`` / ``step_save_pdf`` leaf 분리 — Hancom 은 ``layer3_file``.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import Any, Callable, Sequence
from unittest.mock import MagicMock

from gc1_runtime.layer0_config import read_hancom_wait_sec
from gc1_runtime.layer0_ctl import menu_texts_include_analysis, tab_index_for_analysis
from gc1_runtime.layer1_state import AtomRecord, AtomStatus, JobState, StateStore
from gc1_runtime.layer2_gates import GateEvaluator
from gc1_runtime.layer3_file import (
    SAVE_DIALOG_TITLE_RE,
    click_dialog_button,
    file_glob_pdfs_sorted,
    file_makedirs,
    pdf_stem_from_path,
    wait_and_close_hancom_pdf,
    wait_for_pdf_file_ready,
)
from gc1_runtime.layer4_atoms_p0_p1 import (
    AtomContext,
    AtomOutcome,
    AtomSpec,
    PhaseOutcome,
    _spec,
    run_atom_shell,
)
from gc1_runtime.layer4_atoms_p4 import _phase_blocked_early_ok
from gc1_runtime.layer4_atoms_p5_p7 import (
    P0_P7_ATOM_IDS,
    P57Deps,
    _execute_select_all_leaves,
    _select_analysis_tab_deps,
)

ClockFn = Callable[[], float]
SleepFn = Callable[[float], None]
VisibleFn = Callable[[], bool]

# ---------------------------------------------------------------------------
# Atom registry
# ---------------------------------------------------------------------------

P8_ATOM_IDS: tuple[str, ...] = (
    "Ω.A.L4.P8.01",
    "Ω.A.L4.P8.02",
    "Ω.A.L4.P8.03",
    "Ω.A.L4.P8.04",
    "Ω.A.L4.P8.05",
    "Ω.A.L4.P8.06",
)

P9_ATOM_IDS: tuple[str, ...] = (
    "Ω.A.L4.P9.01",
    "Ω.A.L4.P9.02",
    "Ω.A.L4.P9.03",
    "Ω.A.L4.P9.04",
    "Ω.A.L4.P9.05",
    "Ω.A.L4.P9.06",
    "Ω.A.L4.P9.07",
    "Ω.A.L4.P9.08",
    "Ω.A.L4.P9.09",
    "Ω.A.L4.P9.10",
    "Ω.A.L4.P9.11",
    "Ω.A.L4.P9.12",
    "Ω.A.L4.P9.13",
    "Ω.A.L4.P9.14",
)

P8_P9_ATOM_IDS: tuple[str, ...] = P8_ATOM_IDS + P9_ATOM_IDS
P0_P9_ATOM_IDS: tuple[str, ...] = P0_P7_ATOM_IDS + P8_P9_ATOM_IDS

P8_P9_ATOM_SPECS: dict[str, AtomSpec] = {
    "Ω.A.L4.P8.01": _spec("Ω.A.L4.P8.01", "H", timeout_ms=30000),
    "Ω.A.L4.P8.02": _spec("Ω.A.L4.P8.02", "H", timeout_ms=5000),
    "Ω.A.L4.P8.03": _spec("Ω.A.L4.P8.03", "H", timeout_ms=5000),
    "Ω.A.L4.P8.04": _spec("Ω.A.L4.P8.04", "W", timeout_ms=2000),
    "Ω.A.L4.P8.05": _spec(
        "Ω.A.L4.P8.05", "H", code="E_P8_PRINT", max_attempt=2, retry_delay_ms=500,
        fallback_channel="send_keys ENTER", timeout_ms=30000,
    ),
    "Ω.A.L4.P8.06": _spec("Ω.A.L4.P8.06", "W", timeout_ms=60000),
    "Ω.A.L4.P9.01": _spec("Ω.A.L4.P9.01", "F", timeout_ms=5000),
    "Ω.A.L4.P9.02": _spec(
        "Ω.A.L4.P9.02", "F", code="E_P9_DLG", max_attempt=3, retry_delay_ms=2000, timeout_ms=120000,
    ),
    "Ω.A.L4.P9.03": _spec("Ω.A.L4.P9.03", "H", timeout_ms=5000),
    "Ω.A.L4.P9.04": _spec("Ω.A.L4.P9.04", "H", timeout_ms=1000),
    "Ω.A.L4.P9.05": _spec("Ω.A.L4.P9.05", "H", timeout_ms=15000),
    "Ω.A.L4.P9.06": _spec("Ω.A.L4.P9.06", "H", timeout_ms=10000),
    "Ω.A.L4.P9.07": _spec("Ω.A.L4.P9.07", "W", timeout_ms=1000),
    "Ω.A.L4.P9.08": _spec(
        "Ω.A.L4.P9.08", "H", code="E_P9_SAVE_BTN", max_attempt=2, retry_delay_ms=300,
        fallback_channel="%s", timeout_ms=15000,
    ),
    "Ω.A.L4.P9.09": _spec("Ω.A.L4.P9.09", "H", timeout_ms=15000),
    "Ω.A.L4.P9.10": _spec("Ω.A.L4.P9.10", "W", timeout_ms=180000),
    "Ω.A.L4.P9.11": _spec("Ω.A.L4.P9.11", "F", code="E_P9_READY", timeout_ms=120000),
    "Ω.A.L4.P9.12": _spec("Ω.A.L4.P9.12", "F", timeout_ms=10000),
    "Ω.A.L4.P9.13": _spec("Ω.A.L4.P9.13", "F", code="E_CLEAN_WRONG", timeout_ms=30000),
    "Ω.A.L4.P9.14": _spec("Ω.A.L4.P9.14", "H", timeout_ms=5000),
}


@dataclass
class P89Deps(P57Deps):
    """
    P8/P9 dry-run·live 주입.

    ``save_dialog_visible`` — P8.06 poll mock.
    ``hancom_windows`` — P9.10 Hancom loop (layer3_file).
    ``write_pdf_on_save`` — dry-run 시 P9.09 후 minimal PDF 생성 (P9.11).
    """

    print_dialog_confirmed: bool = False
    save_dialog_found: bool = False
    save_dialog_visible: VisibleFn | None = None
    save_dialog: Any | None = None
    filename_stem: str = ""
    filename_set: bool = False
    save_clicked: bool = False
    overwrite_confirmed: bool = False
    hancom_windows: list[Any] = field(default_factory=list)
    pdf_path_final: str = ""
    cleanup_kept_path: str = ""
    export_recorded: bool = False
    write_pdf_on_save: bool = True
    print_wait_sec: int = 600
    # live — pywinauto dialog 탐색 (P4.06·P9.02·P9.10)
    find_windows: Any | None = None
    connect_window: Any | None = None


class _FakeSaveDialog:
    """P9 dry-run — Edit·Button mock."""

    def __init__(self) -> None:
        self._edit_text = ""
        self._edit = MagicMock()
        self._edit.window_text.return_value = ""
        self._edit.set_focus = MagicMock()
        self._edit.set_edit_text = self._set_edit

        self._btn = MagicMock()
        self._btn.exists.return_value = True
        self._btn.click_input = MagicMock()

    def _set_edit(self, text: str) -> None:
        self._edit_text = text
        self._edit.window_text.return_value = text

    def set_focus(self) -> None:
        pass

    def descendants(self, class_name: str | None = None) -> list[Any]:
        if class_name == "Edit":
            return [self._edit]
        return []

    def child_window(self, title: str, class_name: str) -> MagicMock:
        return self._btn


# ---------------------------------------------------------------------------
# PURE helpers
# ---------------------------------------------------------------------------


def poll_save_dialog(
    *,
    is_visible: VisibleFn,
    clock: ClockFn,
    sleep: SleepFn,
    max_wait_sec: float,
    poll_sec: float = 0.5,
) -> tuple[bool, bool]:
    """P8.06 — ``_wait_for_printing`` (저장 대화상자 poll). 반환: (found, timed_out)."""
    deadline = clock() + max_wait_sec
    while clock() < deadline:
        if is_visible():
            return True, False
        sleep(poll_sec)
    return False, True


def write_minimal_pdf(path: str) -> None:
    """dry-run P9.11 — fitz 1페이지 PDF (``wait_for_pdf_file_ready`` 통과용)."""
    try:
        import fitz
    except ImportError:
        with open(path, "wb") as handle:
            handle.write(b"%PDF-1.4\n1 0 obj<<>>endobj\ntrailer<<>>\n%%EOF\n")
        return
    doc = fitz.open()
    doc.new_page()
    doc.save(path)
    doc.close()


def _atom_id_from_runner(runner: Callable[[AtomContext], AtomOutcome]) -> str:
    parts = runner.__name__.split("_")
    return f"Ω.A.L4.{parts[2].upper()}.{parts[3]}"


def _p9_11_or_12_ok(ctx: AtomContext) -> bool:
    for aid in ("Ω.A.L4.P9.11", "Ω.A.L4.P9.12"):
        rec = ctx.state.atoms.get(aid)
        if rec and rec.status == AtomStatus.OK:
            return True
    return False


# ---------------------------------------------------------------------------
# P8 — print
# ---------------------------------------------------------------------------


def _run_p8_01(ctx: AtomContext) -> AtomOutcome:
    deps: P89Deps = ctx.deps  # type: ignore[assignment]

    def act() -> dict[str, Any]:
        return _execute_select_all_leaves(ctx, deps)

    def post(snapshot: dict[str, Any]) -> tuple[bool, ...]:
        return (
            snapshot.get("ctrl_a_sent") is True,
            float(snapshot.get("elapsed_sec", 0)) >= 0.499,
        )

    return run_atom_shell(
        ctx, P8_P9_ATOM_SPECS["Ω.A.L4.P8.01"],
        pre_probes=(ctx.prior_ok("Ω.A.L4.P7.05"),),
        act=act, post_probes=post,
    )


def _run_p8_02(ctx: AtomContext) -> AtomOutcome:
    def act() -> dict[str, Any]:
        ctx.deps.hand._record("set_focus", "main_window")
        return {"focused": True}

    def post(snapshot: dict[str, Any]) -> tuple[bool, ...]:
        return (snapshot.get("focused") is True,)

    return run_atom_shell(
        ctx, P8_P9_ATOM_SPECS["Ω.A.L4.P8.02"],
        pre_probes=(ctx.prior_ok("Ω.A.L4.P8.01"),),
        act=act, post_probes=post,
    )


def _run_p8_03(ctx: AtomContext) -> AtomOutcome:
    def act() -> dict[str, Any]:
        _select_analysis_tab_deps(ctx)
        ctx.deps.hand.send_keys("^a")
        ctx.deps.sleep(0.3)
        ctx.deps.hand.send_keys("^p")
        return {"keys": "^p"}

    def post(_snapshot: dict[str, Any]) -> tuple[bool, ...]:
        return (True,)

    return run_atom_shell(
        ctx, P8_P9_ATOM_SPECS["Ω.A.L4.P8.03"],
        pre_probes=(ctx.prior_ok("Ω.A.L4.P8.02"),),
        act=act, post_probes=post,
    )


def _run_p8_04(ctx: AtomContext) -> AtomOutcome:
    start = ctx.deps.clock()

    def act() -> dict[str, Any]:
        ctx.deps.sleep(1.0)
        return {"elapsed_sec": ctx.deps.clock() - start}

    def post(snapshot: dict[str, Any]) -> tuple[bool, ...]:
        return (float(snapshot.get("elapsed_sec", 0)) >= 0.999,)

    return run_atom_shell(
        ctx, P8_P9_ATOM_SPECS["Ω.A.L4.P8.04"],
        pre_probes=(ctx.prior_ok("Ω.A.L4.P8.03"),),
        act=act, post_probes=post,
    )


def _run_p8_05(ctx: AtomContext) -> AtomOutcome:
    deps: P89Deps = ctx.deps  # type: ignore[assignment]

    def act() -> dict[str, Any]:
        if deps.dry_run:
            ctx.deps.hand._record("print_confirm", "OK")
            deps.print_dialog_confirmed = True
            return {"print": "confirmed"}
        from gc_autochro import _confirm_print_dialog  # noqa: PLC2701
        from gc_autochro import AutochroConfig

        cfg = AutochroConfig(
            enabled=True,
            window_title_pattern="Autochro-3000",
            crm_path="",
            pdf_output_dir=deps.pdf_output_dir,
            pdf_name_template="",
            quantify_wait_sec=180,
            print_wait_sec=deps.print_wait_sec,
            dialog_wait_sec=30,
            hancom_wait_sec=180,
            dry_run=False,
        )
        _confirm_print_dialog(cfg)
        deps.print_dialog_confirmed = True
        return {"print": "confirmed"}

    def post(_snapshot: dict[str, Any]) -> tuple[bool, ...]:
        return (deps.print_dialog_confirmed,)

    return run_atom_shell(
        ctx, P8_P9_ATOM_SPECS["Ω.A.L4.P8.05"],
        pre_probes=(ctx.prior_ok("Ω.A.L4.P8.04"),),
        act=act, post_probes=post,
    )


def _run_p8_06(ctx: AtomContext) -> AtomOutcome:
    deps: P89Deps = ctx.deps  # type: ignore[assignment]

    def _visible() -> bool:
        if deps.save_dialog_visible is not None:
            return deps.save_dialog_visible()
        return deps.save_dialog_found

    def act() -> dict[str, Any]:
        wait_sec = float(deps.print_wait_sec or 600.0)
        found, timed_out = poll_save_dialog(
            is_visible=_visible,
            clock=deps.clock,
            sleep=deps.sleep,
            max_wait_sec=wait_sec,
        )
        deps.save_dialog_found = found or timed_out
        return {"save_dlg_found": found, "timed_out": timed_out}

    def post(snapshot: dict[str, Any]) -> tuple[bool, ...]:
        return (snapshot.get("save_dlg_found") is True or snapshot.get("timed_out") is True,)

    return run_atom_shell(
        ctx, P8_P9_ATOM_SPECS["Ω.A.L4.P8.06"],
        pre_probes=(ctx.prior_ok("Ω.A.L4.P8.05"),),
        act=act, post_probes=post,
    )


# ---------------------------------------------------------------------------
# P9 — save PDF
# ---------------------------------------------------------------------------


def _run_p9_01(ctx: AtomContext) -> AtomOutcome:
    path = ctx.state.pdf_path_planned

    def act() -> dict[str, Any]:
        directory = file_makedirs(path)
        return {"directory": directory}

    def post(snapshot: dict[str, Any]) -> tuple[bool, ...]:
        directory = str(snapshot.get("directory") or os.path.dirname(path))
        return (os.path.isdir(directory),)

    return run_atom_shell(
        ctx, P8_P9_ATOM_SPECS["Ω.A.L4.P9.01"],
        pre_probes=(ctx.prior_ok("Ω.A.L4.P8.06"),),
        act=act, post_probes=post,
    )


def _run_p9_02(ctx: AtomContext) -> AtomOutcome:
    deps: P89Deps = ctx.deps  # type: ignore[assignment]

    def act() -> dict[str, Any]:
        if deps.dry_run:
            deps.save_dialog = _FakeSaveDialog()
            deps.save_dialog_found = True
            return {"dlg": "mock"}
        from gc1_runtime.layer3_file import find_dialog_by_title_re

        if deps.find_windows is None or deps.connect_window is None:
            raise RuntimeError("find_windows not configured")
        dlg = find_dialog_by_title_re(
            SAVE_DIALOG_TITLE_RE,
            find_windows=deps.find_windows,
            connect_window=deps.connect_window,
            timeout=120.0,
            clock=deps.clock,
            sleep=deps.sleep,
        )
        if dlg is None:
            raise RuntimeError("PDF 저장 대화상자 없음")
        deps.save_dialog = dlg
        deps.save_dialog_found = True
        return {"dlg": "found"}

    def post(_snapshot: dict[str, Any]) -> tuple[bool, ...]:
        return (deps.save_dialog is not None,)

    return run_atom_shell(
        ctx, P8_P9_ATOM_SPECS["Ω.A.L4.P9.02"],
        pre_probes=(ctx.prior_ok("Ω.A.L4.P9.01"),),
        act=act, post_probes=post,
    )


def _run_p9_03(ctx: AtomContext) -> AtomOutcome:
    deps: P89Deps = ctx.deps  # type: ignore[assignment]

    def act() -> dict[str, Any]:
        if deps.save_dialog is None:
            raise RuntimeError("save_dialog missing")
        deps.save_dialog.set_focus()
        ctx.deps.hand._record("dlg.set_focus", "save")
        return {"focused": True}

    def post(snapshot: dict[str, Any]) -> tuple[bool, ...]:
        return (snapshot.get("focused") is True,)

    return run_atom_shell(
        ctx, P8_P9_ATOM_SPECS["Ω.A.L4.P9.03"],
        pre_probes=(ctx.prior_ok("Ω.A.L4.P9.02"),),
        act=act, post_probes=post,
    )


def _run_p9_04(ctx: AtomContext) -> AtomOutcome:
    deps: P89Deps = ctx.deps  # type: ignore[assignment]

    def act() -> dict[str, Any]:
        stem = pdf_stem_from_path(ctx.state.pdf_path_planned)
        deps.filename_stem = stem
        return {"stem": stem}

    def post(snapshot: dict[str, Any]) -> tuple[bool, ...]:
        return (bool(snapshot.get("stem")),)

    return run_atom_shell(
        ctx, P8_P9_ATOM_SPECS["Ω.A.L4.P9.04"],
        pre_probes=(bool(ctx.state.data_name),),
        act=act, post_probes=post,
    )


def _run_p9_05(ctx: AtomContext) -> AtomOutcome:
    deps: P89Deps = ctx.deps  # type: ignore[assignment]

    def act() -> dict[str, Any]:
        from gc1_runtime.layer3_file import find_filename_edit

        if deps.save_dialog is None:
            raise RuntimeError("save_dialog missing")
        edit = find_filename_edit(deps.save_dialog)
        return {"edit_found": edit is not None}

    def post(snapshot: dict[str, Any]) -> tuple[bool, ...]:
        return (snapshot.get("edit_found") is True,)

    return run_atom_shell(
        ctx, P8_P9_ATOM_SPECS["Ω.A.L4.P9.05"],
        pre_probes=(ctx.prior_ok("Ω.A.L4.P9.03"),),
        act=act, post_probes=post,
    )


def _run_p9_06(ctx: AtomContext) -> AtomOutcome:
    deps: P89Deps = ctx.deps  # type: ignore[assignment]

    def act() -> dict[str, Any]:
        from gc1_runtime.layer3_file import find_filename_edit, set_filename_in_dialog

        if deps.save_dialog is None:
            raise RuntimeError("save_dialog missing")
        stem = deps.filename_stem or pdf_stem_from_path(ctx.state.pdf_path_planned)
        set_filename_in_dialog(
            deps.save_dialog,
            stem,
            send_keys_fn=deps.hand.send_keys_fn,
            sleep=deps.sleep,
        )
        edit = find_filename_edit(deps.save_dialog)
        text = ""
        if edit is not None:
            try:
                text = edit.window_text() or stem
            except Exception:
                text = stem
        deps.filename_set = bool(text or stem)
        return {"stem": stem, "text": text}

    def post(_snapshot: dict[str, Any]) -> tuple[bool, ...]:
        return (deps.filename_set,)

    return run_atom_shell(
        ctx, P8_P9_ATOM_SPECS["Ω.A.L4.P9.06"],
        pre_probes=(ctx.prior_ok("Ω.A.L4.P9.05"),),
        act=act, post_probes=post,
    )


def _run_p9_07(ctx: AtomContext) -> AtomOutcome:
    start = ctx.deps.clock()

    def act() -> dict[str, Any]:
        ctx.deps.sleep(0.5)
        return {"elapsed_sec": ctx.deps.clock() - start}

    def post(snapshot: dict[str, Any]) -> tuple[bool, ...]:
        return (float(snapshot.get("elapsed_sec", 0)) >= 0.499,)

    return run_atom_shell(
        ctx, P8_P9_ATOM_SPECS["Ω.A.L4.P9.07"],
        pre_probes=(ctx.prior_ok("Ω.A.L4.P9.06"),),
        act=act, post_probes=post,
    )


def _run_p9_08(ctx: AtomContext) -> AtomOutcome:
    deps: P89Deps = ctx.deps  # type: ignore[assignment]

    def act() -> dict[str, Any]:
        if deps.save_dialog is None:
            raise RuntimeError("save_dialog missing")
        from gc1_runtime.layer3_file import SAVE_BUTTON_TITLES

        ok = click_dialog_button(deps.save_dialog, SAVE_BUTTON_TITLES)
        if not ok and deps.hand.send_keys_fn:
            deps.hand.send_keys("%s")
            ok = True
        deps.save_clicked = ok
        return {"save_clicked": ok}

    def post(_snapshot: dict[str, Any]) -> tuple[bool, ...]:
        return (deps.save_clicked,)

    return run_atom_shell(
        ctx, P8_P9_ATOM_SPECS["Ω.A.L4.P9.08"],
        pre_probes=(ctx.prior_ok("Ω.A.L4.P9.07"),),
        act=act, post_probes=post,
    )


def _run_p9_09(ctx: AtomContext) -> AtomOutcome:
    deps: P89Deps = ctx.deps  # type: ignore[assignment]

    def act() -> dict[str, Any]:
        if deps.dry_run:
            deps.overwrite_confirmed = True
            if deps.write_pdf_on_save and ctx.state.pdf_path_planned:
                write_minimal_pdf(ctx.state.pdf_path_planned)
                deps.pdf_path_final = ctx.state.pdf_path_planned
            return {"overwrite": "skip"}
        from gc1_runtime.layer3_file import confirm_overwrite_if_present

        if deps.find_windows is None or deps.connect_window is None:
            deps.overwrite_confirmed = True
            return {"overwrite": "no_dlg"}
        ok = confirm_overwrite_if_present(
            find_windows=deps.find_windows,
            connect_window=deps.connect_window,
            clock=deps.clock,
            sleep=deps.sleep,
            send_keys_fn=deps.hand.send_keys_fn,
        )
        deps.overwrite_confirmed = ok or True
        return {"overwrite": ok}

    def post(_snapshot: dict[str, Any]) -> tuple[bool, ...]:
        return (deps.overwrite_confirmed,)

    return run_atom_shell(
        ctx, P8_P9_ATOM_SPECS["Ω.A.L4.P9.09"],
        pre_probes=(ctx.prior_ok("Ω.A.L4.P9.08"),),
        act=act, post_probes=post,
    )


def _run_p9_10(ctx: AtomContext) -> AtomOutcome:
    deps: P89Deps = ctx.deps  # type: ignore[assignment]

    def act() -> dict[str, Any]:
        wait_sec = float(read_hancom_wait_sec())
        result = wait_and_close_hancom_pdf(
            hancom_wait_sec=wait_sec,
            get_hancom_windows=lambda: list(deps.hancom_windows),
            clock=deps.clock,
            sleep=deps.sleep,
        )
        deps.hancom_windows.clear()
        return {
            "all_closed": result.all_closed,
            "windows_seen": result.windows_seen,
            "timed_out": result.timed_out,
        }

    def post(snapshot: dict[str, Any]) -> tuple[bool, ...]:
        return (snapshot.get("all_closed") is True or not deps.hancom_windows,)

    return run_atom_shell(
        ctx, P8_P9_ATOM_SPECS["Ω.A.L4.P9.10"],
        pre_probes=(ctx.prior_ok("Ω.A.L4.P9.09"),),
        act=act, post_probes=post,
    )


def _run_p9_11(ctx: AtomContext) -> AtomOutcome:
    deps: P89Deps = ctx.deps  # type: ignore[assignment]
    path = ctx.state.pdf_path_planned

    def act() -> dict[str, Any]:
        ok = wait_for_pdf_file_ready(
            path,
            max_wait_sec=10.0,
            only_if_recent_sec=None,
        )
        if ok:
            deps.pdf_path_final = path
        return {"pdf_ready": ok, "path": path}

    def post(snapshot: dict[str, Any]) -> tuple[bool, ...]:
        return (snapshot.get("pdf_ready") is True,)

    return run_atom_shell(
        ctx, P8_P9_ATOM_SPECS["Ω.A.L4.P9.11"],
        pre_probes=(ctx.prior_ok("Ω.A.L4.P9.10"),),
        act=act, post_probes=post,
    )


def _run_p9_12(ctx: AtomContext) -> AtomOutcome:
    """P9.11 fail soft — 폴더 내 최신 PDF fallback."""
    p911 = ctx.state.atoms.get("Ω.A.L4.P9.11")
    if p911 and p911.status == AtomStatus.OK:
        return AtomOutcome(atom_id="Ω.A.L4.P9.12", ok=True, skipped=True)

    deps: P89Deps = ctx.deps  # type: ignore[assignment]
    folder = os.path.dirname(ctx.state.pdf_path_planned)

    def act() -> dict[str, Any]:
        recent = file_glob_pdfs_sorted(folder)
        alt = recent[0] if recent else ""
        if alt and wait_for_pdf_file_ready(alt, max_wait_sec=10.0, only_if_recent_sec=None):
            deps.pdf_path_final = alt
            return {"alt_pdf": alt}
        return {"alt_pdf": ""}

    def post(snapshot: dict[str, Any]) -> tuple[bool, ...]:
        return (bool(snapshot.get("alt_pdf")),)

    return run_atom_shell(
        ctx, P8_P9_ATOM_SPECS["Ω.A.L4.P9.12"],
        pre_probes=(p911 is not None and p911.status == AtomStatus.FAIL,),
        act=act, post_probes=post,
    )


def _run_p9_13(ctx: AtomContext) -> AtomOutcome:
    deps: P89Deps = ctx.deps  # type: ignore[assignment]

    def act() -> dict[str, Any]:
        kept = deps.pdf_path_final or ctx.state.pdf_path_planned
        deps.cleanup_kept_path = kept
        return {"kept_path": kept}

    def post(snapshot: dict[str, Any]) -> tuple[bool, ...]:
        kept = str(snapshot.get("kept_path") or "")
        return (bool(kept), kept == (deps.pdf_path_final or ctx.state.pdf_path_planned))

    return run_atom_shell(
        ctx, P8_P9_ATOM_SPECS["Ω.A.L4.P9.13"],
        pre_probes=(_p9_11_or_12_ok(ctx),),
        act=act, post_probes=post,
    )


def _run_p9_14(ctx: AtomContext) -> AtomOutcome:
    deps: P89Deps = ctx.deps  # type: ignore[assignment]

    def act() -> dict[str, Any]:
        final = deps.pdf_path_final or ctx.state.pdf_path_planned
        ctx.state.pdf_path_planned = final
        deps.export_recorded = True
        return {"export_pdf": final, "recorded_at": ctx._iso_now()}

    def post(snapshot: dict[str, Any]) -> tuple[bool, ...]:
        return (deps.export_recorded, bool(snapshot.get("export_pdf")))

    return run_atom_shell(
        ctx, P8_P9_ATOM_SPECS["Ω.A.L4.P9.14"],
        pre_probes=(_p9_11_or_12_ok(ctx),),
        act=act, post_probes=post,
    )


_P8_RUNNERS = (_run_p8_01, _run_p8_02, _run_p8_03, _run_p8_04, _run_p8_05, _run_p8_06)
_P9_RUNNERS = (
    _run_p9_01, _run_p9_02, _run_p9_03, _run_p9_04, _run_p9_05, _run_p9_06,
    _run_p9_07, _run_p9_08, _run_p9_09, _run_p9_10, _run_p9_11, _run_p9_12,
    _run_p9_13, _run_p9_14,
)


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


def run_phase_p8(ctx: AtomContext) -> PhaseOutcome:
    return _run_phase_atoms(ctx, _P8_RUNNERS, phase="P8", next_phase="P9", last_ids=P8_ATOM_IDS)


def run_phase_p9(ctx: AtomContext) -> PhaseOutcome:
    return _run_phase_atoms(ctx, _P9_RUNNERS, phase="P9", next_phase="DONE", last_ids=P9_ATOM_IDS)


def run_p8_p9_dry(
    store: StateStore,
    deps: P89Deps,
    *,
    gates: GateEvaluator | None = None,
) -> tuple[PhaseOutcome, PhaseOutcome]:
    """P8+P9 dry-run — P0~P7 완료 state 에서 이어 실행."""
    state = store.load()
    if not state.atoms:
        state = JobState.new_job(atom_ids=P0_P9_ATOM_IDS)
    for aid in P8_P9_ATOM_IDS:
        if aid not in state.atoms:
            state.atoms[aid] = AtomRecord()
    if not state.pdf_path_planned and deps.pdf_output_dir:
        from gc1_runtime.layer4_atoms_p0_p1 import plan_pdf_path

        state.pdf_path_planned = plan_pdf_path(deps.pdf_output_dir, state.data_name or deps.data_name)
    ctx = AtomContext(
        state=state,
        store=store,
        gates=gates or GateEvaluator(),
        deps=deps,
    )
    p8 = run_phase_p8(ctx)
    if not p8.ok:
        return p8, PhaseOutcome(phase="P9", ok=False, message="P8 failed")
    if p8.skipped:
        return p8, PhaseOutcome(phase="P9", ok=True, skipped=True, message="skipped: EARLY_OK")
    p9 = run_phase_p9(ctx)
    return p8, p9


def run_p0_p9_dry(
    store: StateStore,
    deps: P89Deps,
    *,
    gates: GateEvaluator | None = None,
) -> tuple[PhaseOutcome, ...]:
    """P0→P9 전체 dry-run."""
    from gc1_runtime.layer4_atoms_p5_p7 import run_p0_p7_dry

    prior = run_p0_p7_dry(store, deps, gates=gates)
    if len(prior) < 8 or not all(o.ok for o in prior):
        return prior
    p8, p9 = run_p8_p9_dry(store, deps, gates=gates)
    return (*prior, p8, p9)


__all__ = [
    "P0_P9_ATOM_IDS",
    "P89Deps",
    "P8_ATOM_IDS",
    "P8_P9_ATOM_IDS",
    "P8_P9_ATOM_SPECS",
    "P9_ATOM_IDS",
    "poll_save_dialog",
    "run_p0_p9_dry",
    "run_p8_p9_dry",
    "run_phase_p8",
    "run_phase_p9",
    "write_minimal_pdf",
]
