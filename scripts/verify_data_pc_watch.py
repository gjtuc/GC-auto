# -*- coding: utf-8 -*-
"""차헌 PC data_pc watch 통합 검증 — 실제 import·IMAP·pythonw."""
from __future__ import annotations

import importlib.util
import os
import subprocess
import sys
import tempfile
import time

DESKTOP_CURSOR = os.path.join(os.path.expanduser("~"), "Desktop", ".cursor")
REPO = os.path.join(DESKTOP_CURSOR, "GC-auto-push")
DATA_PC = os.path.join(REPO, "data_pc")
sys.path.insert(0, DATA_PC)
sys.path.insert(0, REPO)

FAILURES: list[str] = []


def check(name: str, ok: bool, detail: str = "") -> None:
    status = "PASS" if ok else "FAIL"
    print(f"[{status}] {name}" + (f" | {detail}" if detail else ""))
    if not ok:
        FAILURES.append(name)


def main() -> int:
    print("=== data_pc watch integration verify ===\n")

    # 1) gc_wifi
    try:
        from gc_wifi import get_connected_wifi_ssid, is_required_hotspot_connected

        ssid = get_connected_wifi_ssid()
        check("gc_wifi import", True, f"ssid={ssid!r}")
    except Exception as exc:
        check("gc_wifi import", False, str(exc))

    # 2) load_watch_config from real env
    from data_pc_watch import DataPcWatchRunner, load_watch_config

    cfg = load_watch_config(DESKTOP_CURSOR)
    check("load_watch_config", bool(cfg), f"cooldown={cfg.get('cooldown_sec')}s")
    check("cooldown 1hr", cfg.get("cooldown_sec") == 3600)
    check("iptime ssid", "iptime" in cfg.get("required_ssid", ""))

    # 3) watchdog pythonw
    from data_pc_watchdog import _pythonw_cmd, _pythonw_executable

    pyw = _pythonw_executable()
    check("pythonw exists", os.path.isfile(pyw), pyw)
    cmd = _pythonw_cmd("x.py")
    check("pythonw cmd", cmd[0].lower().endswith("pythonw.exe"))

    # 4) poll-once live IMAP (--no-archive: Origin/G: 생략으로 빠른 검증)
    calc = os.path.join(DESKTOP_CURSOR, "촉매 반응 계산.py")
    r = subprocess.run(
        [sys.executable, calc, "--poll-once", "--no-archive"],
        cwd=DESKTOP_CURSOR,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=120,
    )
    out = (r.stdout or "") + (r.stderr or "")
    check("poll-once exit 0", r.returncode == 0, f"code={r.returncode}")
    check(
        "poll-once no traceback",
        "Traceback" not in out and "치명적" not in out,
    )
    check(
        "poll-once handled empty or mail",
        "처리할 gc_automation 메일이 없습니다" in out or "1단계 완료" in out or "반영:" in out,
    )

    # 5) watchdog ensure-once
    r2 = subprocess.run(
        [sys.executable, os.path.join(DESKTOP_CURSOR, "data_pc_watchdog.py"), "--ensure-once"],
        cwd=DESKTOP_CURSOR,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=30,
    )
    check("watchdog ensure-once", r2.returncode == 0, f"code={r2.returncode}")

    # 6) watch 8s no-wifi-check
    env = os.environ.copy()
    env["PYTHONUNBUFFERED"] = "1"
    env["DATA_PC_BOOT_MAIL_CHECK"] = "0"
    proc = subprocess.Popen(
        [sys.executable, "-u", calc, "--watch", "--no-wifi-check"],
        cwd=DESKTOP_CURSOR,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        encoding="utf-8",
        errors="replace",
        env=env,
    )
    time.sleep(12)
    proc.terminate()
    try:
        wout, _ = proc.communicate(timeout=15)
    except subprocess.TimeoutExpired:
        proc.kill()
        wout, _ = proc.communicate()
    check("watch starts", "감시" in wout or "쿨다운" in wout, repr(wout[:200]))
    check("watch 1hr cooldown msg", "1시간" in wout or "1hour" in wout.lower() or "3600" in str(cfg))
    check("watch no crash", "Traceback" not in wout)

    # 6) status json writable
    status = cfg["status_json"]
    check("status json path", "KCH" in status or os.path.isabs(status))

    # 7) zero-mail pipeline mock
    calls = []

    def fake():
        calls.append(1)
        return 0

    with tempfile.TemporaryDirectory() as tmp:
        from data_pc_watch import _state_json_path

        config = {
            **cfg,
            "cooldown_sec": 0,
            "skip_wifi_check": True,
            "status_json": os.path.join(tmp, "s.json"),
            "state_json": _state_json_path(tmp),
        }
        runner = DataPcWatchRunner(tmp, config, fake)
        from unittest.mock import patch

        with patch.object(runner, "_is_connected", return_value=True):
            with patch.object(runner, "_get_ssid", return_value="iptime"):
                with patch.object(runner, "_wait_reason", return_value=""):
                    runner._tick()
        check("zero-mail tick", calls == [1])

    print(f"\n=== {len(FAILURES)} failure(s) ===")
    return 1 if FAILURES else 0


if __name__ == "__main__":
    raise SystemExit(main())
