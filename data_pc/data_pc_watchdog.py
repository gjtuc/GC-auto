# -*- coding: utf-8 -*-
"""
data_pc_watchdog.py — 데이터 PC watch 백그라운드 감시·자동 재시작

Windows 로그인 시 Task Scheduler로 실행 (차헌: Chaheon_GC_DataPC_Watch).
watch 프로세스가 멈추면 자동 재시작합니다.

로그: %USERPROFILE%\\.cursor\\gc-runtime-temp\\data_pc_watchdog.log
가이드: deploy/DATA_PC_WATCH.md
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import time
from datetime import datetime

def _pythonw_executable() -> str:
    """콘솔 창 없이 실행 — Windows 자동 감시용."""
    exe = sys.executable
    if os.path.basename(exe).lower() == "pythonw.exe":
        return exe
    candidate = os.path.join(os.path.dirname(exe), "pythonw.exe")
    if os.path.isfile(candidate):
        return candidate
    return exe


def _pythonw_cmd(*script_args: str) -> list[str]:
    return [_pythonw_executable(), *script_args]


_SUBPROCESS_FLAGS = 0
if sys.platform == "win32" and hasattr(subprocess, "CREATE_NO_WINDOW"):
    _SUBPROCESS_FLAGS = subprocess.CREATE_NO_WINDOW


def _default_script_dir() -> str:
    return os.path.join(os.path.expanduser("~"), "Desktop", ".cursor")


def _status_json(script_dir: str) -> str:
    for sub in ("KCH", "PEG"):
        folder = os.path.join(script_dir, sub)
        if os.path.isdir(folder):
            return os.path.join(folder, ".data_pc_watch_status.json")
    return os.path.join(script_dir, ".data_pc_watch_status.json")


def _log_path() -> str:
    path = os.path.join(os.path.expanduser("~"), ".cursor", "gc-runtime-temp", "data_pc_watchdog.log")
    os.makedirs(os.path.dirname(path), exist_ok=True)
    return path


def _log(message: str) -> None:
    line = f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} {message}"
    try:
        with open(_log_path(), "a", encoding="utf-8") as f:
            f.write(line + "\n")
    except OSError:
        pass


def _env_int(name: str, default: int) -> int:
    try:
        return int(os.getenv(name, str(default)).strip())
    except (TypeError, ValueError):
        return default


def _parse_status(path: str) -> tuple[bool, float | None, int | None]:
    if not os.path.isfile(path):
        return False, None, None
    try:
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
    except (OSError, json.JSONDecodeError):
        return False, None, None
    alive = bool(data.get("alive"))
    pid = data.get("pid")
    pid_int = int(pid) if isinstance(pid, (int, str)) and str(pid).isdigit() else None
    updated = data.get("last_heartbeat") or data.get("updated_at")
    if not updated:
        return alive, None, pid_int
    try:
        dt = datetime.strptime(str(updated), "%Y-%m-%d %H:%M:%S")
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


def _heartbeat_fresh(alive: bool, hb_epoch: float | None, stale_sec: int) -> bool:
    if not alive or hb_epoch is None:
        return False
    return (time.time() - hb_epoch) <= stale_sec


def _stale_sec() -> int:
    return _env_int("DATA_PC_WATCH_HEARTBEAT_STALE_SEC", 180)


def is_watch_healthy(script_dir: str) -> bool:
    status_path = _status_json(script_dir)
    alive, hb_epoch, status_pid = _parse_status(status_path)
    if not status_pid or not _pid_alive(status_pid):
        return False
    return _heartbeat_fresh(alive, hb_epoch, _stale_sec())


def _find_watchdog_pids() -> list[int]:
    if sys.platform != "win32":
        return []
    try:
        out = subprocess.run(
            [
                "wmic",
                "process",
                "where",
                "name='python.exe'",
                "get",
                "ProcessId,CommandLine",
            ],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            creationflags=_SUBPROCESS_FLAGS,
        )
    except OSError:
        return []
    if out.returncode != 0:
        return []
    pids = []
    for line in out.stdout.splitlines():
        if "data_pc_watchdog.py" not in line:
            continue
        parts = line.strip().split()
        if parts and parts[-1].isdigit():
            pids.append(int(parts[-1]))
    return pids


def _ensure_wifi(script_dir: str) -> None:
    try:
        repo = os.path.join(script_dir, "GC-auto-push")
        if os.path.isdir(repo) and repo not in sys.path:
            sys.path.insert(0, repo)
        from gc_wifi_autoconnect import ensure_wifi_connected

        ensure_wifi_connected(script_dir)
    except Exception as exc:
        _log(f"[wifi] 자동 연결 생략: {exc}")


def ensure_watch_running(script_dir: str, *, hidden: bool = True) -> bool:
    if is_watch_healthy(script_dir):
        return False
    if _find_watchdog_pids():
        _log("[ensure] watchdog 이미 실행 중 - watch 복구 대기")
        return False

    vbs = os.path.join(script_dir, "gc_data_pc_start_watch_hidden.vbs")
    if os.path.isfile(vbs):
        _log("[ensure] hidden VBS 로 watchdog 강제 시작")
        flags = _SUBPROCESS_FLAGS if hidden else 0
        subprocess.Popen(["wscript.exe", vbs], creationflags=flags)
        return True

    _log("[ensure] VBS 없음 - watchdog 직접 시작")
    flags = _SUBPROCESS_FLAGS if hidden else 0
    subprocess.Popen(
        _pythonw_cmd(
            os.path.join(script_dir, "data_pc_watchdog.py"),
            "--script-dir",
            script_dir,
        ),
        cwd=script_dir,
        creationflags=flags,
    )
    return True


def supervise(script_dir: str, *, poll_sec: int = 30, hidden: bool = True) -> None:
    stale_sec = _stale_sec()
    status_path = _status_json(script_dir)
    watch_script = os.path.join(script_dir, "촉매 반응 계산.py")
    if not os.path.isfile(watch_script):
        _log(f"[오류] 스크립트 없음: {watch_script}")
        sys.exit(1)

    watch_cmd = _pythonw_cmd(watch_script, "--watch")
    env = os.environ.copy()
    env.setdefault("PYTHONPYCACHEPREFIX", os.path.join(os.path.expanduser("~"), ".cursor", "gc-python-cache"))
    env.setdefault("GC_DATA_PC_RUNTIME", os.path.join(os.path.expanduser("~"), ".cursor", "gc-runtime-temp"))

    _log(f"[watchdog] 시작 script_dir={script_dir} stale={stale_sec}s")
    _ensure_wifi(script_dir)

    while True:
        alive, hb_epoch, status_pid = _parse_status(status_path)
        if status_pid and _pid_alive(status_pid) and _heartbeat_fresh(alive, hb_epoch, stale_sec):
            time.sleep(poll_sec)
            continue

        if status_pid and _pid_alive(status_pid):
            _log(f"[watchdog] heartbeat stale - PID {status_pid} 종료")
            _kill_pid(status_pid)

        _log(f"[watchdog] watch 프로세스 시작 (pythonw={_pythonw_executable()})")
        flags = _SUBPROCESS_FLAGS if hidden else 0
        proc = subprocess.Popen(
            watch_cmd,
            cwd=script_dir,
            env=env,
            creationflags=flags,
        )
        supervised_pid = proc.pid

        while True:
            time.sleep(poll_sec)
            if proc.poll() is not None:
                _log(f"[watchdog] watch 종료 code={proc.returncode} - 재시작 대기")
                break
            alive, hb_epoch, status_pid = _parse_status(status_path)
            check_pid = status_pid if status_pid and _pid_alive(status_pid) else supervised_pid
            if not _heartbeat_fresh(alive, hb_epoch, stale_sec):
                _log("[watchdog] heartbeat 멈춤 - watch 재시작")
                if _pid_alive(check_pid):
                    _kill_pid(check_pid)
                elif proc.poll() is None:
                    _kill_pid(supervised_pid)
                break

        time.sleep(5)


def main() -> None:
    parser = argparse.ArgumentParser(description="데이터 PC watch 감시")
    parser.add_argument("--script-dir", default=_default_script_dir())
    parser.add_argument("--poll-sec", type=int, default=30)
    parser.add_argument("--visible", action="store_true", help="콘솔 창 표시 (디버그용)")
    parser.add_argument(
        "--ensure-once",
        action="store_true",
        help="watch 미동작 시 1회 강제 시작 (작업 스케줄러 안전망)",
    )
    args = parser.parse_args()
    if args.ensure_once:
        _ensure_wifi(args.script_dir)
        started = ensure_watch_running(args.script_dir, hidden=not args.visible)
        _log("[ensure] 강제 시작" if started else "[ensure] 이미 정상")
        sys.exit(0)
    supervise(args.script_dir, poll_sec=args.poll_sec, hidden=not args.visible)


if __name__ == "__main__":
    main()
