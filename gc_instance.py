# -*- coding: utf-8 -*-
"""GC --watch 단일 실행 보장 (중복 콘솔 자동 정리).

장비 PC(gc_automation.py --watch) 전용. lock·pid 파일은 EXCEL_OUTPUT_DIR
(Desktop\\박은규 또는 Desktop\\KCH) 아래에 생성. 은규 PC/차헌 PC와 무관.
"""

from __future__ import annotations

import atexit
import os
import re
import subprocess
import sys

_MUTEX_NAME = "Local\\ChemStationGCWatch"
_mutex_handle = None

_SUBPROCESS_FLAGS = 0
if sys.platform == "win32" and hasattr(subprocess, "CREATE_NO_WINDOW"):
    _SUBPROCESS_FLAGS = subprocess.CREATE_NO_WINDOW


def _lock_path(excel_output_dir: str) -> str:
    from gc_profiles import gc_runtime_dir

    return os.path.join(gc_runtime_dir(excel_output_dir), ".gc_watch.pid")


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


def _kill_pid(pid: int) -> None:
    if pid <= 0 or pid == os.getpid():
        return
    if sys.platform == "win32":
        subprocess.run(
            ["taskkill", "/PID", str(pid), "/F"],
            capture_output=True,
            creationflags=_SUBPROCESS_FLAGS,
        )
    else:
        try:
            os.kill(pid, 9)
        except OSError:
            pass


def _parse_wmic_process_ids(stdout: str) -> list[int]:
    pids: list[int] = []
    for line in stdout.splitlines():
        line = line.strip()
        if line.startswith("ProcessId="):
            val = line.split("=", 1)[1].strip()
            if val.isdigit():
                pids.append(int(val))
    return pids


def _wmic_python_pids(where_extra: str) -> list[int]:
    if sys.platform != "win32":
        return []
    where = f"name='python.exe' and {where_extra}"
    try:
        result = subprocess.run(
            ["wmic", "process", "where", where, "get", "ProcessId", "/format:list"],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=20,
            creationflags=_SUBPROCESS_FLAGS,
        )
    except (OSError, subprocess.TimeoutExpired):
        return []
    return _parse_wmic_process_ids(result.stdout)


def find_watch_process_pids() -> list[int]:
    """gc_automation.py --watch 프로세스 PID 목록."""
    return _wmic_python_pids(
        "CommandLine like '%gc_automation.py%' and CommandLine like '%--watch%'"
    )


def find_watchdog_process_pids() -> list[int]:
    return _wmic_python_pids("CommandLine like '%gc_watchdog%'")


def kill_other_watch_processes(exclude_pid: int | None = None) -> int:
    """다른 --watch 프로세스 종료 (현재 PID 제외)."""
    killed = 0
    my_pid = exclude_pid or os.getpid()
    for pid in find_watch_process_pids():
        if pid != my_pid:
            _kill_pid(pid)
            killed += 1
    return killed


def clear_stale_lock_file(excel_output_dir: str) -> None:
    lock_path = _lock_path(excel_output_dir)
    if not os.path.isfile(lock_path):
        return
    pid = _read_lock_pid(lock_path)
    if pid is None or not _pid_alive(pid) or pid == os.getpid():
        try:
            os.remove(lock_path)
        except OSError:
            pass


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

    clear_stale_lock_file(excel_output_dir)

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


def ensure_watch_exclusive(excel_output_dir: str, heartbeat_tolerance_min: int = 5) -> str:
    """
    watch 시작 전 중복 정리.

    Returns:
        'acquired'         … 이 프로세스가 감시 담당
        'already_healthy'  … 다른 watch가 정상 동작 — 이 프로세스는 종료
        'failed'           … lock 획득 실패
    """
    from gc_status import verify_desktop_heartbeat

    check = verify_desktop_heartbeat(heartbeat_tolerance_min)
    if check.ok:
        other_pids = [p for p in find_watch_process_pids() if p != os.getpid()]
        if other_pids:
            return "already_healthy"

    clear_stale_lock_file(excel_output_dir)
    kill_other_watch_processes(exclude_pid=os.getpid())

    if acquire_watch_lock(excel_output_dir):
        return "acquired"

    # mutex 잔류 — 기존 watch PID 정리 후 1회 재시도
    for pid in find_watch_process_pids():
        if pid != os.getpid():
            _kill_pid(pid)
    clear_stale_lock_file(excel_output_dir)
    if acquire_watch_lock(excel_output_dir):
        return "acquired"

    return "failed"


def stop_all_watch(excel_output_dir: str | None = None) -> int:
    """watch·watchdog 프로세스 전부 종료."""
    pids = find_watchdog_process_pids() + find_watch_process_pids()
    for pid in pids:
        _kill_pid(pid)

    out_dir = excel_output_dir
    if not out_dir:
        try:
            from gc_profiles import resolve_profile

            out_dir = resolve_profile().excel_output_dir
        except Exception:
            out_dir = os.path.join(os.path.expanduser("~"), "Desktop", "KCH")
    clear_stale_lock_file(out_dir)
    return len(pids)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="GC watch instance utilities")
    parser.add_argument("--stop-watch", action="store_true", help="watch·watchdog 전부 종료")
    args = parser.parse_args()
    if args.stop_watch:
        count = stop_all_watch()
        if count:
            print(f"[안내] GC Watch 종료 — {count}개 프로세스")
        else:
            print("[안내] 실행 중인 GC Watch 가 없습니다.")
