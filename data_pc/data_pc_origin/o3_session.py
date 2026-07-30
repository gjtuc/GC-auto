# -*- coding: utf-8 -*-
"""O3 — Origin GUI 세션: 저장 후 종료, COM attach.

[증상 — 차헌 PC·은규 PC 공통]
  파이프라인(또는 supervisor)이 Origin COM 작업 전에 GUI를 정리할 때,
  예전 코드는 ``doc -s``(dirty 플래그만 해제, 실제 저장 아님) 후 ``taskkill /F`` 를
  써서 **저장 안 된 .opju 가 강제 종료**되거나, ``exit`` 로 **저장 확인 대화상자**에
  멈추는 경우가 있었다.

[해결 원칙 — ``save_and_force_quit_origin_gui``]
  1. 창 제목에서 .opju 경로 파싱 → ``project.save(명시적경로)`` (COM)
  2. 경로 없으면 ``DATA_PC_ORIGIN_RECOVERY_DIR`` 백업 (.opju)
  3. COM 실패 시 ``o3_ui_win32.ps1`` 로 Ctrl+S / 저장 대화상자 [예]
  4. 창 제목 ``*``(미저장) 이 사라지고 저장이 ``ok:`` 일 때만 ``taskkill``
  5. 저장 실패 시 ``OriginGuiBusyError`` — **taskkill 하지 않음** (작업 보호)
  6. WM_CLOSE / ``taskkill /IM`` graceful 종료는 사용 안 함 (대화상자 유발)

[은규 PC 배포]
  ``git pull`` 후 ``data_pc/data_pc_origin/`` 전체를 script_dir 로 복사해야 한다.
  ``o3_ui_win32.ps1`` 이 같은 폴더에 있어야 UI 폴백이 동작한다.
  자동: ``scripts/port_eungyu_data_pc.ps1`` — 수동: STEP6·이식 가이드 참고.
  상세: ``docs/DATA_PC_ORIGIN_SAVE.md``

[환경 변수]
  DATA_PC_KEEP_ORIGIN_GUI=1  — 사용자 Origin 을 절대 종료하지 않음
  DATA_PC_ORIGIN_AUTO_KILL=1 — COM 전 저장·종료 (기본)
  DATA_PC_ORIGIN_RECOVERY_DIR — untitled 프로젝트 백업 폴더
"""

from __future__ import annotations

import logging
import os
import subprocess
import sys
import time
from types import ModuleType
from typing import Callable, Optional

from data_pc_origin.o3_import import import_originpro, reset_originpro_cache
from data_pc_origin.o3_plugins import PluginRegistry

_LOGGER = logging.getLogger("data_pc_origin")

_ORIGIN_IMAGE_NAMES = ("Origin64.exe", "Origin.exe")


class OriginGuiBusyError(RuntimeError):
    """Origin GUI가 켜져 있어 COM 자동화를 시작할 수 없음."""


class OriginComTimeoutError(RuntimeError):
    """Origin COM 작업이 제한 시간 내에 끝나지 않음."""

_SUBPROCESS_FLAGS = 0
if sys.platform == "win32" and hasattr(subprocess, "CREATE_NO_WINDOW"):
    _SUBPROCESS_FLAGS = subprocess.CREATE_NO_WINDOW


def _keep_origin_gui() -> bool:
    return os.getenv("DATA_PC_KEEP_ORIGIN_GUI", "").strip().lower() in (
        "1",
        "true",
        "yes",
        "on",
    )


def _auto_kill_origin_enabled() -> bool:
    """COM 직전 기존 Origin GUI 자동 종료 (기본 켜짐)."""
    return os.getenv("DATA_PC_ORIGIN_AUTO_KILL", "1").strip().lower() in (
        "1",
        "true",
        "yes",
        "on",
    )


def _origin_stop_timeout_sec() -> float:
    try:
        return max(5.0, float(os.getenv("DATA_PC_ORIGIN_STOP_TIMEOUT_SEC", "45")))
    except ValueError:
        return 45.0


def _origin_stop_poll_sec() -> float:
    try:
        return max(0.25, float(os.getenv("DATA_PC_ORIGIN_STOP_POLL_SEC", "0.5")))
    except ValueError:
        return 0.5


def origin_com_timeout_sec() -> float:
    try:
        return max(60.0, float(os.getenv("DATA_PC_ORIGIN_COM_TIMEOUT_SEC", "600")))
    except ValueError:
        return 600.0


def origin_com_poll_sec() -> float:
    try:
        return max(5.0, float(os.getenv("DATA_PC_ORIGIN_POLL_SEC", "15")))
    except ValueError:
        return 15.0


def wait_origin_gui_stopped(
    *,
    timeout_sec: float | None = None,
    poll_sec: float | None = None,
) -> bool:
    """Origin GUI 프로세스가 사라질 때까지 대기."""
    deadline = time.time() + (timeout_sec if timeout_sec is not None else _origin_stop_timeout_sec())
    step = poll_sec if poll_sec is not None else _origin_stop_poll_sec()
    while time.time() < deadline:
        if not is_origin_gui_running():
            return True
        time.sleep(step)
    return not is_origin_gui_running()


def ensure_origin_gui_clear_for_com(
    *,
    allow_kill: bool | None = None,
    log: Callable[[str], None] | None = None,
) -> bool:
    """
    4단계 COM 직전 — Origin GUI 실행 여부 확인 후 저장·종료.

    · DATA_PC_KEEP_ORIGIN_GUI=1 → 실행 중이면 OriginGuiBusyError
    · 기본(DATA_PC_ORIGIN_AUTO_KILL=1) → 저장 시도 후 종료
  · allow_kill=False → 실행 중이면 OriginGuiBusyError (supervisor 등)
    """
    emit = log or _LOGGER.info
    if not is_origin_gui_running():
        return True
    if _keep_origin_gui():
        raise OriginGuiBusyError(
            "Origin GUI가 실행 중입니다 (DATA_PC_KEEP_ORIGIN_GUI=1 — COM 자동화 불가)"
        )
    do_kill = _auto_kill_origin_enabled() if allow_kill is None else bool(allow_kill)
    if not do_kill:
        raise OriginGuiBusyError(
            "Origin GUI가 실행 중입니다 — 종료 후 COM 작업을 다시 시도하세요"
        )
    save_and_force_quit_origin_gui(log=emit)
    return True


def _origin_lt_run(op: ModuleType, cmd: str) -> tuple[bool, str]:
    """LabTalk 실행 — LT_execute(구버전) 또는 lt_exec."""
    for name in ("LT_execute", "lt_exec"):
        fn = getattr(op, name, None)
        if not callable(fn):
            continue
        try:
            result = fn(cmd)
            return True, f"ok:{result!r}"
        except Exception as exc:
            return False, f"err:{type(exc).__name__}:{exc}"
    return False, "no_lt_runner"


def _origin_recovery_save_path() -> str:
    """저장 경로 없는(untitled) 프로젝트 백업 위치."""
    custom = os.getenv("DATA_PC_ORIGIN_RECOVERY_DIR", "").strip()
    if custom:
        base = custom
    else:
        base = os.path.join(
            os.path.expanduser("~"),
            "Documents",
            "Origin Recovery",
            "gc_automation",
        )
    os.makedirs(base, exist_ok=True)
    stamp = time.strftime("%Y%m%d_%H%M%S")
    return os.path.join(base, f"origin_autosave_{stamp}.opju")


def _lt_save_path(path: str) -> str:
    """LabTalk save 명령용 경로 (슬래시)."""
    return path.replace("\\", "/")


def _get_origin_main_window_title() -> str:
    """Origin 메인 창 제목 (.opju 포함)."""
    if sys.platform != "win32":
        return ""
    proc = subprocess.run(
        [
            "powershell.exe",
            "-NoProfile",
            "-Command",
            "[Console]::OutputEncoding=[Text.UTF8Encoding]::UTF8; "
            "(Get-Process Origin64,Origin -ErrorAction SilentlyContinue | "
            "Where-Object { $_.MainWindowTitle -like '*.opju*' -or $_.MainWindowTitle -like '*.opj*' } | "
            "Select-Object -First 1).MainWindowTitle",
        ],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        creationflags=_SUBPROCESS_FLAGS,
    )
    return (proc.stdout or "").strip()


def _origin_has_unsaved_changes() -> bool:
    """창 제목의 * 표시로 미저장 변경 여부 확인.

    Origin 은 저장 전 제목에 ``.opju *`` 를 붙인다. taskkill 전에 반드시 False 여야 한다.
    """
    title = _get_origin_main_window_title()
    return ".opju *" in title or ".opj *" in title


def _run_origin_ui_script(action: str) -> str:
    """o3_ui_win32.ps1 — AnswerSaveYes | CtrlS.

    COM ``project.save`` 가 실패하거나 ``exit`` 후 저장 대화상자가 뜰 때 UI 폴백.
    스크립트는 ``data_pc_origin/o3_ui_win32.ps1`` 과 같은 디렉터리에 있어야 한다.
    """
    script = os.path.join(os.path.dirname(__file__), "o3_ui_win32.ps1")
    proc = subprocess.run(
        [
            "powershell.exe",
            "-NoProfile",
            "-ExecutionPolicy",
            "Bypass",
            "-File",
            script,
            "-Action",
            action,
        ],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        creationflags=_SUBPROCESS_FLAGS,
    )
    return (proc.stdout or "").strip().splitlines()[-1] if proc.stdout else ""


def _answer_pending_save_dialog_yes(emit: Callable[[str], None]) -> bool:
    """이전 exit로 떠 있는 'Save changes?' 대화상자 → Yes."""
    if sys.platform != "win32":
        return False
    answered = _run_origin_ui_script("AnswerSaveYes") == "answered"
    if answered:
        emit("[Origin] 저장 확인 대화상자 — Yes 처리")
        time.sleep(1.5)
    return answered


def _save_via_ui_ctrl_s(emit: Callable[[str], None]) -> bool:
    """COM 실패 시 Origin 창에 Ctrl+S 전송."""
    if sys.platform != "win32":
        return False
    if _run_origin_ui_script("CtrlS") != "sent":
        return False
    emit("[Origin] UI Ctrl+S 저장 시도")
    deadline = time.time() + 12.0
    while time.time() < deadline:
        if not _origin_has_unsaved_changes():
            emit("[Origin] UI 저장 완료 (* 사라짐)")
            return True
        time.sleep(0.5)
    return False


def _get_origin_path_from_window_title() -> str:
    """Origin 창 제목에서 .opju 전체 경로 추출 (COM 실패 시 폴백)."""
    if sys.platform != "win32":
        return ""
    proc = subprocess.run(
        [
            "powershell.exe",
            "-NoProfile",
            "-Command",
            "[Console]::OutputEncoding=[Text.UTF8Encoding]::UTF8; "
            "(Get-Process Origin64,Origin -ErrorAction SilentlyContinue | "
            "Where-Object { $_.MainWindowTitle } | Select-Object -First 1)"
            ".MainWindowTitle",
        ],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        creationflags=_SUBPROCESS_FLAGS,
    )
    title = (proc.stdout or "").strip()
    if not title or " - " not in title:
        return ""
    left, rest = title.split(" - ", 1)
    fname = left.replace("*", "").strip()
    if not fname.lower().endswith((".opju", ".opj")):
        return ""
    folder = rest.split(" - ", 1)[0].strip().rstrip("\\/")
    if not folder:
        return ""
    return os.path.join(folder, fname)


def _get_project_name(op: ModuleType) -> str:
    """실행 중 Origin 프로젝트 이름 (%G)."""
    get_lt = getattr(op, "get_lt_str", None)
    if not callable(get_lt):
        return ""
    ok, _ = _origin_lt_run(op, "gc_projname$ = %G")
    if not ok:
        return ""
    try:
        return (get_lt("gc_projname$") or "").strip()
    except Exception:
        return ""


def _get_running_project_path(op: ModuleType) -> str:
    """실행 중 Origin — 저장된 프로젝트 전체 경로 (%X / %G)."""
    from_title = _get_origin_path_from_window_title()
    if from_title:
        return from_title
    get_lt = getattr(op, "get_lt_str", None)
    if not callable(get_lt):
        return ""
    ok, _ = _origin_lt_run(op, "gc_projpath$ = %X; gc_projname$ = %G")
    if not ok:
        return ""
    try:
        raw_path = (get_lt("gc_projpath$") or "").strip()
        name = (get_lt("gc_projname$") or "").strip()
    except Exception:
        return ""
    if raw_path.lower().endswith((".opju", ".opj")):
        return raw_path
    if raw_path and name:
        folder = raw_path.rstrip("\\/")
        fname = (
            name
            if name.lower().endswith((".opju", ".opj"))
            else f"{name}.opju"
        )
        return os.path.join(folder, fname)
    return ""


def _save_to_explicit_path(
    op: ModuleType,
    path: str,
    emit: Callable[[str], None],
) -> str:
    """알려진 경로로 저장 — Save 확인 대화상자 없음."""
    project_save = getattr(getattr(op, "project", None), "save", None)
    if callable(project_save):
        try:
            if project_save(path):
                emit(f"[Origin] 프로젝트 저장: {path}")
                return f"ok:explicit:{path}"
        except Exception as exc:
            last_err = f"{type(exc).__name__}:{exc}"
        else:
            last_err = "save_returned_false"
    else:
        last_err = "no_project_save"
    lt_path = _lt_save_path(path)
    ok, detail = _origin_lt_run(op, f'save -DIX "{lt_path}"')
    if ok:
        emit(f"[Origin] LabTalk 저장: {path}")
        return f"ok:explicit_lt:{path}"
    return f"err:explicit:{last_err};lt:{detail}"


def _exit_origin_without_prompt(op: ModuleType) -> str:
    """저장 완료 후 dirty 플래그 정리 → 대화상자 없이 종료."""
    if _origin_has_unsaved_changes():
        return "err:still_unsaved"
    _origin_lt_run(op, "doc -s")
    ok, detail = _origin_lt_run(op, "exit")
    if ok:
        time.sleep(2.0)
        return f"lt_exit:{detail}"
    exit_fn = getattr(op, "exit", None)
    if callable(exit_fn):
        try:
            exit_fn()
            return "detach_only"
        except Exception as exc:
            return f"err:{type(exc).__name__}:{exc}"
    return f"err:exit_failed:{detail}"


def _save_running_origin_project(op: ModuleType, emit: Callable[[str], None]) -> str:
    """실행 중 Origin 프로젝트 저장 — 기존 경로 또는 백업 폴더."""
    explicit = _get_running_project_path(op)
    if explicit:
        result = _save_to_explicit_path(op, explicit, emit)
        if result.startswith("ok:"):
            return result

    project_name = _get_project_name(op)
    if project_name and project_name.upper() != "UNTITLED":
        ok, detail = _origin_lt_run(op, "save")
        if ok:
            emit(f"[Origin] LabTalk 저장 (프로젝트: {project_name})")
            return f"ok:lt_named:{project_name}"
        named_path = _get_running_project_path(op)
        if named_path:
            result = _save_to_explicit_path(op, named_path, emit)
            if result.startswith("ok:"):
                return result

    project_mod = getattr(op, "project", None)
    save_fn = getattr(project_mod, "save", None) if project_mod is not None else None
    if not callable(save_fn):
        save_fn = getattr(op, "save", None)
    if not callable(save_fn):
        return "skipped:no_save_fn"

    recovery = _origin_recovery_save_path()
    try:
        if save_fn(recovery):
            emit(f"[Origin] 미저장 프로젝트 백업 저장: {recovery}")
            return f"ok:recovery:{recovery}"
    except Exception as exc:
        lt_path = _lt_save_path(recovery)
        ok, detail = _origin_lt_run(op, f'save -DIX "{lt_path}"')
        if ok:
            emit(f"[Origin] LabTalk 백업 저장: {recovery}")
            return f"ok:recovery_lt:{recovery}"
        return f"err:{type(exc).__name__}:{exc};lt:{detail}"

    return "err:recovery_failed"


def _save_running_origin_project_with_ui_fallback(
    op: ModuleType,
    emit: Callable[[str], None],
) -> str:
    """COM 저장 + UI(Ctrl+S) 폴백."""
    _answer_pending_save_dialog_yes(emit)
    save_result = _save_running_origin_project(op, emit)
    if save_result.startswith("ok:"):
        return save_result
    if _origin_has_unsaved_changes() and _save_via_ui_ctrl_s(emit):
        return "ok:ui_ctrl_s"
    if _answer_pending_save_dialog_yes(emit) and not _origin_has_unsaved_changes():
        return "ok:dialog_yes"
    return save_result


def _kill_headless_origin_orphans(
    log: Callable[[str], None] | None = None,
) -> int:
    """창 없는 Origin64/COM 고아 프로세스만 종료 — 사용자 GUI는 유지."""
    if sys.platform != "win32":
        return 0
    emit = log or _LOGGER.info
    proc = subprocess.run(
        [
            "powershell.exe",
            "-NoProfile",
            "-Command",
            "Get-Process Origin64,Origin -ErrorAction SilentlyContinue | "
            "Where-Object { -not $_.MainWindowTitle } | "
            "ForEach-Object { $_.Id }",
        ],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        creationflags=_SUBPROCESS_FLAGS,
    )
    killed = 0
    for line in (proc.stdout or "").splitlines():
        pid = line.strip()
        if not pid.isdigit():
            continue
        tk = subprocess.run(
            ["taskkill", "/F", "/PID", pid],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            creationflags=_SUBPROCESS_FLAGS,
        )
        if tk.returncode == 0:
            killed += 1
            emit(f"[Origin] headless 인스턴스 종료 PID={pid}")
    if killed:
        time.sleep(1.5)
    return killed


def _prepare_attached_origin_op(
    *,
    gui_already_running: bool = False,
) -> tuple[ModuleType, bool]:
    """실행 중 Origin GUI에 COM 연결."""
    op = import_originpro()
    attach_called = False
    attach_fn = getattr(op, "attach", None)
    if callable(attach_fn):
        attach_fn()
        attach_called = True
    if not gui_already_running:
        try:
            set_show_false(op)
        except Exception:
            pass
        try:
            set_oext(op, True)
        except Exception:
            pass
    return op, attach_called


def _try_origin_com_graceful_save(emit: Callable[[str], None]) -> str:
    """실행 중 Origin에 COM으로 저장·종료 시도. 저장 결과 문자열 반환."""
    gui_before = is_origin_gui_running()
    _answer_pending_save_dialog_yes(emit)
    save_result = "fail:not_attempted"
    try:
        op, _attach_called = _prepare_attached_origin_op(
            gui_already_running=gui_before,
        )
        save_result = _save_running_origin_project_with_ui_fallback(op, emit)
        if save_result.startswith("ok:") and not _origin_has_unsaved_changes():
            _exit_origin_without_prompt(op)
        elif save_result.startswith("ok:"):
            emit("[Origin] 저장됐지만 * 표시 남음 — exit 생략")
        else:
            emit("[Origin] 저장 실패 — exit 생략 (저장 확인 대화상자 방지)")
        emit("[Origin] COM 저장·종료 시도 완료")
        return save_result
    except Exception as exc:
        emit(f"[Origin] COM 저장 시도 생략 ({exc})")
        try:
            op, _ = _prepare_attached_origin_op(gui_already_running=gui_before)
            save_result = _save_running_origin_project_with_ui_fallback(op, emit)
        except Exception as rescue_exc:
            save_result = f"fail:{type(exc).__name__}:{exc};rescue:{rescue_exc}"
        return save_result


def save_and_force_quit_origin_gui(
    *,
    log: Callable[[str], None] | None = None,
) -> bool:
    """실행 중 Origin GUI — **디스크에 저장한 뒤에만** 강제 종료.

    파이프라인 4단계(``_finalize_deferred_origin_batch``)와
    ``ensure_origin_gui_clear_for_com`` 가 호출한다. 사용자 확인 없음.

    흐름: headless Origin64 정리 → COM 저장(명시 경로) → lt_exec('exit') →
    미저장(*) 남으면 예외 · taskkill 생략.

    은규 PC: ``gc-data-pc\\data_pc_origin\\`` 가 repo 와 동기화돼 있어야 한다.
    """
    emit = log or _LOGGER.info
    if not is_origin_gui_running():
        return True
    if _keep_origin_gui():
        raise OriginGuiBusyError(
            "Origin GUI가 실행 중입니다 (DATA_PC_KEEP_ORIGIN_GUI=1)"
        )
    emit("[Origin] 실행 중 Origin 감지 — 저장 후 종료")
    _kill_headless_origin_orphans(log=emit)
    save_result = _try_origin_com_graceful_save(emit)
    still_running = is_origin_gui_running()
    if still_running:
        unsaved = _origin_has_unsaved_changes()
        saved_ok = save_result.startswith("ok:")
        recovery_saved = save_result.startswith("ok:recovery")
        if saved_ok and (recovery_saved or not unsaved):
            kill_stale_origin_gui(allow_kill=True, log=emit)
            wait_origin_gui_stopped(timeout_sec=30.0)
        else:
            emit("[Origin] 저장 실패 — taskkill 생략 (작업 보호)")
            raise OriginGuiBusyError(
                f"Origin 저장 실패 — 수동 저장 후 다시 시도 ({save_result})"
            )
    if is_origin_gui_running():
        emit("[Origin] 종료 잔존 — headless 정리 후 재시도")
        _kill_headless_origin_orphans(log=emit)
        kill_stale_origin_gui(allow_kill=True, log=emit)
    if not wait_origin_gui_stopped():
        raise OriginGuiBusyError("Origin GUI 종료 대기 시간 초과")
    emit("[Origin] Origin GUI 정리 완료")
    # COM attach 직전 여유 — 직후 LT_set_var 일시 오류 완화
    try:
        cool = float(os.getenv("DATA_PC_ORIGIN_POST_QUIT_WAIT_SEC", "3"))
    except ValueError:
        cool = 3.0
    if cool > 0:
        time.sleep(cool)
    return True


def ensure_origin_stopped_after_job(
    *,
    log: Callable[[str], None] | None = None,
) -> bool:
    """시료별 Origin 작업 직후 — GUI 저장·종료, headless 고아 정리, 종료 대기.

    ``tasklist`` 타이밍으로 ``save_and_force_quit`` 가 ``skip_not_running`` 되더라도
    COM이 띄운 Origin·headless 고아를 정리해 다음 시료 COM 오류를 줄인다.
    """
    emit = log or _LOGGER.info
    if is_origin_gui_running():
        save_and_force_quit_origin_gui(log=emit)
    else:
        _kill_headless_origin_orphans(log=emit)
    wait_origin_gui_stopped()
    return not is_origin_gui_running()


def is_origin_gui_running() -> bool:
    """Origin GUI(Origin64.exe / Origin.exe) 실행 여부."""
    if sys.platform != "win32":
        return False
    proc = subprocess.run(
        ["tasklist"],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        creationflags=_SUBPROCESS_FLAGS,
    )
    if proc.returncode != 0:
        return False
    low = proc.stdout.lower()
    return any(name.lower() in low for name in _ORIGIN_IMAGE_NAMES)


def kill_stale_origin_gui(
    *,
    allow_kill: bool = False,
    log: Callable[[str], None] | None = None,
) -> int:
    """
    Origin GUI 프로세스 종료.

    · `allow_kill=False`(기본) — 종료하지 않음 (supervisor·일반 파이프라인)
    · `allow_kill=True` — 사용자 확인 후 에이전트가 호출
    · `DATA_PC_KEEP_ORIGIN_GUI=1` — 항상 건너뜀
    """
    if not allow_kill or _keep_origin_gui() or sys.platform != "win32":
        return 0
    if not is_origin_gui_running():
        return 0
    emit = log or _LOGGER.info
    if _origin_has_unsaved_changes():
        emit("[Origin] 미저장 변경 — taskkill 생략")
        return 0
    killed = 0
    for image in _ORIGIN_IMAGE_NAMES:
        proc = subprocess.run(
            ["taskkill", "/F", "/IM", image],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            creationflags=_SUBPROCESS_FLAGS,
        )
        if proc.returncode == 0:
            killed += 1
            emit(f"[Origin] {image} 종료")
    if killed:
        time.sleep(1.5)
    return killed


def set_show_false(op: ModuleType) -> None:
    op.set_show(False)


def set_oext(op: ModuleType, enabled: bool) -> None:
    """originpro 버전별 — callable oext() 또는 bool 속성 대입."""
    if not hasattr(op, "oext"):
        return
    member = getattr(op, "oext", None)
    if callable(member):
        member(enabled)
        return
    try:
        setattr(op, "oext", enabled)
    except (AttributeError, TypeError):
        pass


class OriginSession:
    """with OriginSession() as op: … — set_show(False), enter/exit, finally op.exit()."""

    def __init__(
        self,
        *,
        plugins: PluginRegistry | None = None,
        importer: Callable[[], ModuleType] | None = None,
    ) -> None:
        self.plugins = plugins or PluginRegistry()
        self._importer = importer
        self._op: ModuleType | None = None
        self._entered = False

    def __enter__(self) -> ModuleType:
        if self._importer is not None:
            self._op = self._importer()
        else:
            self._op = import_originpro()
        set_show_false(self._op)
        set_oext(self._op, True)
        self._entered = True
        return self._op

    def __exit__(self, exc_type, exc, tb) -> bool:
        op = self._op
        self._entered = False
        if op is not None:
            try:
                op.exit()
            finally:
                try:
                    set_oext(op, False)
                except Exception:
                    pass
                self._op = None
                # exit 후 캐시된 COM 핸들은 재사용 불가 — 다음 세션이 새로 attach
                reset_originpro_cache()
        return False
