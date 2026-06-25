# -*- coding: utf-8 -*-
"""
gc_watchdog.py — GC watch 감시·멈춤 시 자동 재시작

=============================================================================
[어느 PC — 장비 PC 전용]
=============================================================================

  **GC2/GC3 장비 PC** (차헌, Desktop\\KCH) 운영 안정화용.
  은규 PC / 차헌 PC / GC1 장비 PC에서는 보통 미사용.

  gc_start_watch.bat 과 별도로 watchdog 실행 시
  heartbeat stale → watch 프로세스 kill + 재spawn.

  GC1 장비 PC: gc_error_handler.py 도 watch 재시작 담당 (중복 가능 — env로 조절).

heartbeat(.gc_watch_status.json / MMDDHHmm.txt)가 WATCH_HEARTBEAT_STALE_SEC 이상
갱신되지 않으면 watch 프로세스를 종료하고 다시 시작합니다.

이미 정상 watch가 떠 있으면 중복 spawn 하지 않고 해당 PID만 감시합니다.
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import threading
import time
from datetime import datetime

from gc_config import WATCH_HEARTBEAT_STALE_SEC, default_watch_status_json
from gc_console import setup_console_encoding
from gc_watch_log import watch_activity_log_path

setup_console_encoding()

_SUBPROCESS_FLAGS = 0
if sys.platform == "win32" and hasattr(subprocess, "CREATE_NO_WINDOW"):
    _SUBPROCESS_FLAGS = subprocess.CREATE_NO_WINDOW


def _parse_heartbeat(status_json_path: str) -> tuple[bool, float | None, int | None]:
    """(alive, last_heartbeat_epoch, pid)"""
    if not os.path.isfile(status_json_path):
        return False, None, None
    try:
        with open(status_json_path, encoding="utf-8") as f:
            data = json.load(f)
    except (OSError, json.JSONDecodeError):
        return False, None, None

    alive = bool(data.get("alive"))
    pid = data.get("pid")
    pid_int = int(pid) if isinstance(pid, int) or (isinstance(pid, str) and str(pid).isdigit()) else None

    hb = data.get("last_heartbeat")
    if not hb:
        return alive, None, pid_int
    try:
        dt = datetime.strptime(str(hb), "%Y-%m-%d %H:%M:%S")
        return alive, dt.timestamp(), pid_int
    except ValueError:
        return alive, None, pid_int


def _pid_alive(pid: int) -> bool:
    if pid <= 0:
        return False
    if sys.platform == "win32":
        import ctypes

        handle = ctypes.windll.kernel32.OpenProcess(0x1000, False, pid)
        if handle:
            ctypes.windll.kernel32.CloseHandle(handle)
            return True
        return False
    try:
        os.kill(pid, 0)
        return True
    except OSError:
        return False


def _kill_pid(pid: int) -> None:
    if pid <= 0:
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


def _heartbeat_fresh(alive: bool, hb_epoch: float | None) -> bool:
    if not alive or hb_epoch is None:
        return False
    return (time.time() - hb_epoch) <= WATCH_HEARTBEAT_STALE_SEC


def _watch_heartbeat_stale(
    status_json: str,
) -> tuple[bool, float, int | None]:
    """heartbeat JSON·파일 mtime 기준 멈춤 여부 (hb 필드 없어도 파일 나이로 판별)."""
    alive, hb_epoch, status_pid = _parse_heartbeat(status_json)
    now = time.time()
    if hb_epoch is not None:
        age = now - hb_epoch
        if not alive or age > WATCH_HEARTBEAT_STALE_SEC:
            return True, age, status_pid
        return False, age, status_pid
    try:
        age = now - os.path.getmtime(status_json)
    except OSError:
        age = float(WATCH_HEARTBEAT_STALE_SEC + 1)
    if age > WATCH_HEARTBEAT_STALE_SEC:
        return True, age, status_pid
    return False, age, status_pid


def _start_activity_log_tail() -> threading.Event:
    """watch 숨김 프로세스 활동 로그 → GC Watch 창에 실시간 표시."""
    log_path = watch_activity_log_path()
    stop = threading.Event()

    def _worker() -> None:
        pos = 0
        if os.path.isfile(log_path):
            try:
                pos = os.path.getsize(log_path)
            except OSError:
                pos = 0
        while not stop.is_set():
            try:
                if os.path.isfile(log_path):
                    with open(log_path, encoding="utf-8") as f:
                        f.seek(pos)
                        chunk = f.read()
                        if chunk:
                            for line in chunk.splitlines():
                                if line.strip():
                                    print(line)
                            pos = f.tell()
            except OSError:
                pass
            stop.wait(0.4)

    threading.Thread(target=_worker, name="gc-watch-activity-tail", daemon=True).start()
    return stop


def _find_healthy_watch(status_json: str) -> int | None:
    alive, hb_epoch, status_pid = _parse_heartbeat(status_json)
    if not _heartbeat_fresh(alive, hb_epoch):
        return None
    if status_pid and _pid_alive(status_pid):
        return status_pid
    from gc_instance import find_watch_process_pids

    for pid in find_watch_process_pids():
        if _pid_alive(pid):
            return pid
    return None


def should_start_new_supervisor(status_json: str | None = None) -> bool:
    """새 watchdog 창이 필요하면 True (다른 watchdog가 이미 있으면 False)."""
    from gc_instance import find_watchdog_process_pids

    others = [p for p in find_watchdog_process_pids() if p != os.getpid()]
    return len(others) == 0


def _exit_if_duplicate_supervisor(status_json: str) -> None:
    """정상 감시가 이미 있을 때 중복 watchdog 창은 자동 종료."""
    if not should_start_new_supervisor(status_json):
        healthy_pid = _find_healthy_watch(status_json)
        print(
            f"[watchdog] 다른 감시 창이 이미 실행 중 (watch PID {healthy_pid}) — "
            "이 창 자동 종료"
        )
        sys.exit(0)


def _monitor_existing_watch(status_json: str, poll_sec: int) -> None:
    """spawn 없이 기존 watch PID heartbeat만 감시."""
    supervised_pid = _find_healthy_watch(status_json)
    if not supervised_pid:
        return

    print(f"[watchdog] 기존 watch 정상 (PID {supervised_pid}) — 중복 시작 안 함")
    stale_reported = False

    while True:
        time.sleep(poll_sec)
        _, _, status_pid = _parse_heartbeat(status_json)
        if status_pid and _pid_alive(status_pid):
            supervised_pid = status_pid

        stale, age, status_pid = _watch_heartbeat_stale(status_json)
        if stale:
            if not stale_reported:
                print(
                    f"[watchdog] heartbeat {int(age)}초 경과 — watch 멈춤 감지, 재시작합니다"
                )
                stale_reported = True
            target = supervised_pid
            if status_pid and _pid_alive(status_pid):
                target = status_pid
            if target and _pid_alive(target):
                _kill_pid(target)
            return

        if supervised_pid and not _pid_alive(supervised_pid):
            print("[watchdog] watch 프로세스 종료 감지 — 재시작합니다")
            return


def supervise_watch(script_dir: str, poll_sec: int = 30) -> None:
    """watch subprocess 실행 — heartbeat 멈춤 시 kill 후 재시작."""
    watch_cmd = [sys.executable, os.path.join(script_dir, "gc_automation.py"), "--watch"]
    status_json = default_watch_status_json()

    _start_activity_log_tail()

    print()
    print(" [GC Watch] 감시 시작 — heartbeat 멈춤 시 자동 재시작")
    print(" 종료: 이 창을 닫거나 gc_stop_watch.bat 실행")
    print()
    print(
        f"[watchdog] GC watch 감시 시작 — heartbeat {WATCH_HEARTBEAT_STALE_SEC}초 이상 "
        "멈추면 재시작"
    )
    print(f"[watchdog] 상태 파일: {status_json}")
    print(f"[watchdog] 활동 로그: {watch_activity_log_path()}")

    from gc_instance import kill_other_watch_processes

    while True:
        healthy_pid = _find_healthy_watch(status_json)
        if healthy_pid:
            _monitor_existing_watch(status_json, poll_sec)
            print("[watchdog] 5초 후 재시작...")
            time.sleep(5)
            continue

        kill_other_watch_processes()
        print(f"\n[watchdog] {datetime.now().strftime('%H:%M:%S')} watch 프로세스 시작...")
        proc = subprocess.Popen(
            watch_cmd,
            cwd=script_dir,
            env=os.environ.copy(),
            creationflags=_SUBPROCESS_FLAGS,
        )
        stale_reported = False

        while proc.poll() is None:
            time.sleep(poll_sec)
            stale, age, status_pid = _watch_heartbeat_stale(status_json)
            if stale:
                if not stale_reported:
                    print(
                        f"[watchdog] heartbeat {int(age)}초 경과 — watch 멈춤 감지, 재시작합니다"
                    )
                    stale_reported = True
                target_pid = proc.pid
                if status_pid and _pid_alive(status_pid):
                    target_pid = status_pid
                _kill_pid(target_pid)
                try:
                    proc.wait(timeout=15)
                except subprocess.TimeoutExpired:
                    _kill_pid(proc.pid)
                    proc.wait(timeout=5)
                break

            if proc.poll() is not None:
                break

        code = proc.poll()
        if _find_healthy_watch(status_json):
            print("[watchdog] 다른 watch가 정상 동작 — 중복 spawn 중단")
            continue

        print(f"[watchdog] watch 종료 (code={code}) — 5초 후 재시작")
        time.sleep(5)


def main() -> None:
    parser = argparse.ArgumentParser(description="GC watch watchdog — 멈춤 시 자동 재시작")
    parser.add_argument(
        "--supervise",
        action="store_true",
        help="watch를 감시하며 heartbeat 멈춤 시 재시작",
    )
    parser.add_argument(
        "--supervise-if-needed",
        action="store_true",
        help="정상 감시가 없을 때만 supervise (있으면 exit 1)",
    )
    parser.add_argument(
        "--check-start-needed",
        action="store_true",
        help="새 감시 창이 필요하면 exit 0, 이미 정상 감시 중이면 exit 1",
    )
    parser.add_argument("--poll-sec", type=int, default=30)
    args = parser.parse_args()
    script_dir = os.path.dirname(os.path.abspath(__file__))

    if args.check_start_needed:
        sys.exit(0 if should_start_new_supervisor() else 1)

    if args.supervise_if_needed:
        if not should_start_new_supervisor():
            sys.exit(1)
        _exit_if_duplicate_supervisor(default_watch_status_json())
        supervise_watch(script_dir, poll_sec=max(15, args.poll_sec))
        return

    if args.supervise:
        status_json = default_watch_status_json()
        _exit_if_duplicate_supervisor(status_json)
        supervise_watch(script_dir, poll_sec=max(15, args.poll_sec))
        return

    parser.print_help()


if __name__ == "__main__":
    main()
