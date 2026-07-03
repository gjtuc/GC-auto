# -*- coding: utf-8 -*-
"""O3 — OriginSession context manager."""

from __future__ import annotations

import logging
import os
import subprocess
import sys
import time
from types import ModuleType
from typing import Callable, Optional

from data_pc_origin.o3_import import import_originpro
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


def _try_origin_com_graceful_save(emit: Callable[[str], None]) -> None:
    """실행 중 Origin에 COM으로 저장·종료 시도 (실패해도 taskkill 로 이어감)."""
    try:
        op = import_originpro()
        set_show_false(op)
        set_oext(op, True)
        lt = getattr(op, "LT_execute", None)
        if callable(lt):
            for cmd in ("doc -s", "doc -s 1"):
                try:
                    lt(cmd)
                except Exception:
                    pass
        save_fn = getattr(op, "save", None)
        if callable(save_fn):
            try:
                save_fn()
            except Exception:
                pass
        exit_fn = getattr(op, "exit", None)
        if callable(exit_fn):
            exit_fn()
        emit("[Origin] COM 저장·종료 시도 완료")
    except Exception as exc:
        emit(f"[Origin] COM 저장 시도 생략 ({exc})")


def save_and_force_quit_origin_gui(
    *,
    log: Callable[[str], None] | None = None,
) -> bool:
    """실행 중 Origin GUI — 저장 시도 후 강제 종료 (사용자 동의 없음)."""
    emit = log or _LOGGER.info
    if not is_origin_gui_running():
        return True
    if _keep_origin_gui():
        raise OriginGuiBusyError(
            "Origin GUI가 실행 중입니다 (DATA_PC_KEEP_ORIGIN_GUI=1)"
        )
    emit("[Origin] 실행 중 Origin 감지 — 저장 후 종료")
    _try_origin_com_graceful_save(emit)
    if is_origin_gui_running():
        kill_stale_origin_gui(allow_kill=True, log=emit)
    if not wait_origin_gui_stopped():
        raise OriginGuiBusyError("Origin GUI 종료 대기 시간 초과")
    emit("[Origin] Origin GUI 정리 완료")
    return True


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
                set_oext(op, False)
                self._op = None
        return False
