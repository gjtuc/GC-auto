# -*- coding: utf-8 -*-
"""O1 — Origin 설치·프로세스 probe."""

from __future__ import annotations

import importlib
import subprocess
import sys
from types import ModuleType
from typing import Optional, Tuple

from data_pc_origin.o0_types import ProbeResult


def try_import_originpro() -> Tuple[ProbeResult, Optional[ModuleType]]:
    try:
        op = importlib.import_module("originpro")
    except ImportError as exc:
        return ProbeResult(False, str(exc), "I01"), None
    return ProbeResult(True, "ok", "I01"), op


def origin_exe_running() -> ProbeResult:
    """Origin64.exe 실행 여부 (정보용 — 미실행도 ok)."""
    if sys.platform != "win32":
        return ProbeResult(True, "non-windows skip", "I02")
    try:
        proc = subprocess.run(
            ["tasklist", "/FI", "IMAGENAME eq Origin64.exe", "/NH"],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=10,
            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        return ProbeResult(True, f"tasklist skip: {exc}", "I02")
    running = "Origin64.exe" in (proc.stdout or "")
    detail = "running" if running else "not running"
    return ProbeResult(True, detail, "I02")


def probe_origin_install() -> ProbeResult:
    result, _module = try_import_originpro()
    if not result.ok:
        return result
    running = origin_exe_running()
    detail = f"installed; origin_exe={running.detail}"
    return ProbeResult(True, detail, "I03")
