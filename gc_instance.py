# -*- coding: utf-8 -*-
"""GC --watch 단일 실행 보장 (중복 콘솔 방지)."""

from __future__ import annotations

import atexit
import os
import sys

_MUTEX_NAME = "Local\\ChemStationGCWatch"
_mutex_handle = None


def _lock_path(excel_output_dir: str) -> str:
    return os.path.join(excel_output_dir, ".gc_watch.pid")


def _pid_alive(pid: int) -> bool:
    if pid <= 0:
        return False
    if sys.platform == "win32":
        import ctypes

        PROCESS_QUERY_LIMITED_INFORMATION = 0x1000
        handle = ctypes.windll.kernel32.OpenProcess(PROCESS_QUERY_LIMITED_INFORMATION, False, pid)
        if handle:
            ctypes.windll.kernel32.CloseHandle(handle)
            return True
        return False
    try:
        os.kill(pid, 0)
        return True
    except OSError:
        return False


def _read_lock_pid(path: str) -> int | None:
    try:
        with open(path, encoding="utf-8") as lock_file:
            return int(lock_file.read().strip())
    except (OSError, ValueError):
        return None


def acquire_watch_lock(excel_output_dir: str) -> bool:
    """
    --watch 는 PC당 1개만 실행.

    Returns:
        True  … 이 프로세스가 감시 담당
        False … 이미 다른 감시 프로세스 실행 중
    """
    global _mutex_handle
    os.makedirs(excel_output_dir, exist_ok=True)
    lock_path = _lock_path(excel_output_dir)

    existing_pid = _read_lock_pid(lock_path) if os.path.isfile(lock_path) else None
    if existing_pid is not None and _pid_alive(existing_pid) and existing_pid != os.getpid():
        return False

    if sys.platform == "win32":
        import ctypes

        _mutex_handle = ctypes.windll.kernel32.CreateMutexW(None, True, _MUTEX_NAME)
        if ctypes.windll.kernel32.GetLastError() == 183:  # ERROR_ALREADY_EXISTS
            if _mutex_handle:
                ctypes.windll.kernel32.CloseHandle(_mutex_handle)
                _mutex_handle = None
            return False

    with open(lock_path, "w", encoding="utf-8") as lock_file:
        lock_file.write(str(os.getpid()))

    atexit.register(release_watch_lock, excel_output_dir)
    return True


def release_watch_lock(excel_output_dir: str) -> None:
    global _mutex_handle
    lock_path = _lock_path(excel_output_dir)
    try:
        if os.path.isfile(lock_path):
            pid = _read_lock_pid(lock_path)
            if pid == os.getpid():
                os.remove(lock_path)
    except OSError:
        pass
    if sys.platform == "win32" and _mutex_handle:
        import ctypes

        ctypes.windll.kernel32.CloseHandle(_mutex_handle)
        _mutex_handle = None
