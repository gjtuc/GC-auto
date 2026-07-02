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
