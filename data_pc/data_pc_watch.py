# -*- coding: utf-8 -*-
"""
data_pc_watch.py — 데이터 PC Wi-Fi 감시 → 메일·계산·Origin 자동 파이프라인

[흐름] GC2/GC3 장비 PC watch 와 동일 원리:
  · REQUIRED_HOTSPOT Wi-Fi 연결 유지 중 DATA_PC_WATCH_INTERVAL_SEC(15초) 폴링
  · G: 잠금 시 DATA_PC_GDRIVE_RETRY_SEC(기본 15분) 재시도 — 1시간 쿨다운 미적용
  · 부팅 직후 미처리 메일 1회 (DATA_PC_BOOT_MAIL_CHECK)

[설정] Desktop\\.cursor\\gc_automation.env
  REQUIRED_HOTSPOT=iptime,iptime 2,iptime_5G   # 차헌 PC
  DATA_PC_AUTO_MAIL_COOLDOWN_HOURS=1
  DATA_PC_WATCH_INTERVAL_SEC=15

[실행]
  python "촉매 반응 계산.py" --watch
  gc_data_pc_install_autostart.bat
"""

from __future__ import annotations

import json
import os
import sys
import threading
import time
from datetime import datetime
from typing import Any, Callable, Optional


def _repo_roots() -> list[str]:
    home = os.path.expanduser("~")
    desktop_cursor = os.path.join(home, "Desktop", ".cursor")
    return [
        os.path.join(desktop_cursor, "GC-auto-push"),
        os.path.join(home, "chemstation-gc-automation"),
        os.path.join(desktop_cursor, "GC-auto"),
    ]


def _import_gc_wifi():
    for repo in _repo_roots():
        if os.path.isdir(repo) and repo not in sys.path:
            sys.path.insert(0, repo)
    from gc_wifi import (
        get_connected_wifi_ssid,
        hotspot_wait_reason,
        is_required_hotspot_connected,
    )

    return get_connected_wifi_ssid, is_required_hotspot_connected, hotspot_wait_reason


def _env_bool(name: str, default: bool = False) -> bool:
    raw = os.getenv(name, "").strip().lower()
    if not raw:
        return default
    return raw in ("1", "true", "yes", "on")


def _env_int(name: str, default: int, *, minimum: int = 0) -> int:
    try:
        value = int(os.getenv(name, str(default)).strip())
    except (TypeError, ValueError):
        value = default
    return max(minimum, value)


def _status_json_path(script_dir: str) -> str:
    for sub in ("KCH", "PEG"):
        folder = os.path.join(script_dir, sub)
        if os.path.isdir(folder):
            return os.path.join(folder, ".data_pc_watch_status.json")
    return os.path.join(script_dir, ".data_pc_watch_status.json")


def _state_json_path(script_dir: str) -> str:
    for sub in ("KCH", "PEG"):
        folder = os.path.join(script_dir, sub)
        if os.path.isdir(folder):
            return os.path.join(folder, ".data_pc_watch_state.json")
    return os.path.join(script_dir, ".data_pc_watch_state.json")


def load_watch_config(script_dir: str) -> dict:
    """gc_automation.env 에서 Wi-Fi·감시·쿨다운 설정 로드."""
    try:
        from dotenv import load_dotenv
    except ImportError:
        print("[오류] python-dotenv 미설치: pip install python-dotenv")
        return {}

    env_path = os.path.join(script_dir, "gc_automation.env")
    if os.path.isfile(env_path):
        load_dotenv(env_path)

    required = (
        os.getenv("REQUIRED_HOTSPOT", "").strip()
        or os.getenv("REQUIRED_HOTSPOT_SSID", "").strip()
        or "iptime,iptime 2,iptime_5G"
    )
    cooldown_hours = _env_int("DATA_PC_AUTO_MAIL_COOLDOWN_HOURS", 1, minimum=0)
    # 구 env 호환: DATA_PC_HOTSPOT_DELAY_SEC=3600 도 1시간 쿨다운으로 인식
    legacy_delay = _env_int("DATA_PC_HOTSPOT_DELAY_SEC", 0, minimum=0)
    cooldown_sec = cooldown_hours * 3600
    if legacy_delay >= 3600 and cooldown_sec < legacy_delay:
        cooldown_sec = legacy_delay

    return {
        "required_ssid": required,
        "cooldown_sec": cooldown_sec,
        "cooldown_hours": cooldown_hours,
        "interval_sec": _env_int("DATA_PC_WATCH_INTERVAL_SEC", 15, minimum=5),
        "reconnect_min_sec": _env_int("DATA_PC_HOTSPOT_RECONNECT_MIN_SEC", 90, minimum=0),
        "skip_wifi_check": _env_bool("DATA_PC_SKIP_WIFI_CHECK"),
        "boot_mail_check": _env_bool("DATA_PC_BOOT_MAIL_CHECK", True),
        "boot_network_wait_sec": _env_int("DATA_PC_BOOT_NETWORK_WAIT_SEC", 90, minimum=10),
        # G: 잠금 시 재시도 간격 — 작업 스케줄러 Ensure(15분)와 동일
        "gdrive_retry_sec": _env_int("DATA_PC_GDRIVE_RETRY_SEC", 900, minimum=60),
        "status_json": _status_json_path(script_dir),
        "state_json": _state_json_path(script_dir),
    }


def _write_json(path: str, payload: dict) -> None:
    try:
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(payload, f, ensure_ascii=False, indent=2)
    except OSError:
        pass


def _load_state(state_path: str) -> dict:
    if not os.path.isfile(state_path):
        return {}
    try:
        with open(state_path, encoding="utf-8") as f:
            data = json.load(f)
        return data if isinstance(data, dict) else {}
    except (OSError, json.JSONDecodeError):
        return {}


def _save_state(state_path: str, patch: dict) -> None:
    data = _load_state(state_path)
    data.update(patch)
    _write_json(state_path, data)


def _parse_epoch(raw: Optional[str]) -> Optional[float]:
    if not raw:
        return None
    try:
        return datetime.strptime(str(raw), "%Y-%m-%d %H:%M:%S").timestamp()
    except ValueError:
        return None


def _read_last_pipeline_epoch(state_path: str) -> Optional[float]:
    return _parse_epoch(_load_state(state_path).get("last_pipeline_at"))


def _mark_pipeline_success(state_path: str) -> None:
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    _save_state(
        state_path,
        {
            "last_pipeline_at": now,
            "gdrive_retry_pending": False,
        },
    )


def _mark_gdrive_retry(state_path: str) -> None:
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    _save_state(
        state_path,
        {
            "last_gdrive_attempt_at": now,
            "gdrive_retry_pending": True,
        },
    )


def _parse_pipeline_result(result: Any) -> tuple[int, bool]:
    if hasattr(result, "workflow_count"):
        return int(result.workflow_count), bool(getattr(result, "gdrive_retry_needed", False))
    return int(result), False


class DataPcWatchRunner:
    """Wi-Fi 연결 유지 중 poll + 쿨다운(기본 1시간)마다 파이프라인 1회."""

    def __init__(
        self,
        script_dir: str,
        config: dict,
        process_callback: Callable[[], Any],
        g_drive_check: Optional[Callable[[], bool]] = None,
    ):
        self.script_dir = script_dir
        self.config = config
        self.process_callback = process_callback
        self._g_drive_check = g_drive_check
        self._wifi_was_connected = False
        self._wifi_lost_at: Optional[float] = None
        self._pipeline_running = False
        self._started_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self._last_status: dict = {}
        self._heartbeat_stop = threading.Event()
        (
            self._get_ssid,
            self._is_connected,
            self._wait_reason,
        ) = _import_gc_wifi()

    def _cooldown_remaining(self) -> int:
        state_path = self.config["state_json"]
        state = _load_state(state_path)
        if state.get("gdrive_retry_pending"):
            if self._g_drive_check and self._g_drive_check():
                return 0
            last = _parse_epoch(state.get("last_gdrive_attempt_at"))
            if last is None:
                return 0
            retry_sec = self.config["gdrive_retry_sec"]
            return max(0, int(retry_sec - (time.time() - last)))

        last = _read_last_pipeline_epoch(state_path)
        if last is None:
            return 0
        return max(0, int(self.config["cooldown_sec"] - (time.time() - last)))

    def _publish(self, code: str, message: str, **extra) -> None:
        wifi_ssid = self._get_ssid()
        wifi_ready = self._is_connected(
            self.config["required_ssid"],
            self.config["skip_wifi_check"],
        )
        payload = {
            "alive": True,
            "status_code": code,
            "message": message,
            "wifi_ssid": wifi_ssid,
            "wifi_ready": wifi_ready,
            "required_ssid": self.config["required_ssid"],
            "cooldown_sec": self.config["cooldown_sec"],
            "cooldown_remaining_sec": self._cooldown_remaining(),
            "started_at": self._started_at,
            "updated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "last_heartbeat": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "pid": os.getpid(),
            **extra,
        }
        self._last_status = payload
        _write_json(self.config["status_json"], payload)

    def _wait_for_network(self, max_sec: int) -> bool:
        import socket

        host, port = "imap.naver.com", 993
        attempts = max(1, max_sec // 5)
        for i in range(attempts):
            try:
                with socket.create_connection((host, port), timeout=5):
                    return True
            except OSError:
                if i == 0:
                    print(f"[부팅] 네트워크 대기 중 (IMAP {host})...")
                time.sleep(5)
        return False

    def _run_pipeline(self, reason: str) -> None:
        if self._pipeline_running:
            return
        self._pipeline_running = True
        try:
            print(f"\n[실행] {reason}")
            self._publish("running_pipeline", reason)
            result = self.process_callback()
            count, gdrive_retry = _parse_pipeline_result(result)
            state_path = self.config["state_json"]
            if gdrive_retry:
                _mark_gdrive_retry(state_path)
                retry_min = self.config["gdrive_retry_sec"] // 60
                msg = (
                    f"G: 잠금 — {retry_min}분 후 재시도 "
                    f"(1시간 쿨다운 미적용, 미처리 메일 유지)"
                )
                print(f"[완료] {msg}")
                self._publish("gdrive_retry", msg, workflow_count=count)
            else:
                _mark_pipeline_success(state_path)
                msg = f"파이프라인 완료 - {count}건 시료 반영"
                print(f"[완료] {msg}")
                self._publish("pipeline_done", msg, workflow_count=count)
        except Exception as exc:
            print(f"[오류] 파이프라인 실패: {exc}")
            self._publish("error", str(exc))
        finally:
            self._pipeline_running = False

    def _run_boot_mail_check(self) -> None:
        if not self.config.get("boot_mail_check", True):
            return
        wait = self.config.get("boot_network_wait_sec", 90)
        print("[부팅] 미처리 메일 확인 (PC 꺼진 동안 수신분)")
        self._publish("boot_mail_check", "부팅 후 미처리 메일 확인 중")
        if not self._wait_for_network(wait):
            print("[부팅] 네트워크 미준비 - Wi-Fi 감시는 계속됩니다")
            self._publish("boot_network_wait", "네트워크 대기 중")
            return
        self._run_pipeline("부팅 후 미처리 메일 → 계산 → Origin")

    def run_forever(self) -> None:
        interval = self.config["interval_sec"]
        cooldown_h = self.config["cooldown_hours"]
        reconnect = self.config["reconnect_min_sec"]
        ssid = self.config["required_ssid"]

        print(f"[안내] 데이터 PC Wi-Fi 감시 - {interval}초 간격, SSID: {ssid}")
        print(
            f"       Wi-Fi 연결 유지 중 자동 파이프라인 "
            f"({cooldown_h}시간 쿨다운, G: 잠금 시 {self.config['gdrive_retry_sec'] // 60}분 재시도)"
        )
        print(f"       순간 끊김({reconnect}초 미만 재연결) - 동일 세션")
        print("       종료: Ctrl+C")
        self._publish("starting", "데이터 PC Wi-Fi 감시 시작")
        hb = threading.Thread(target=self._heartbeat_worker, name="data-pc-watch-hb", daemon=True)
        hb.start()
        self._run_boot_mail_check()

        try:
            while True:
                self._tick()
                time.sleep(interval)
        except KeyboardInterrupt:
            print("\n[안내] Wi-Fi 감시 종료 (Ctrl+C)")
        finally:
            self._heartbeat_stop.set()
            _write_json(
                self.config["status_json"],
                {
                    "alive": False,
                    "status_code": "stopped",
                    "message": "감시 종료됨",
                    "updated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                },
            )

    def _heartbeat_worker(self) -> None:
        """IMAP·Origin 처리 중에도 watchdog heartbeat 유지."""
        interval = max(15, self.config["interval_sec"])
        while not self._heartbeat_stop.wait(interval):
            snap = dict(self._last_status)
            if not snap:
                continue
            snap["last_heartbeat"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            snap["alive"] = True
            _write_json(self.config["status_json"], snap)

    def _tick(self) -> None:
        ssid = self.config["required_ssid"]
        skip = self.config["skip_wifi_check"]
        reconnect = self.config["reconnect_min_sec"]

        if not self._is_connected(ssid, skip):
            if self._wifi_was_connected:
                self._wifi_lost_at = time.monotonic()
            self._wifi_was_connected = False
            reason = self._wait_reason(ssid)
            self._publish("waiting_wifi", reason)
            print(f"[대기] {reason}")
            return

        if not self._wifi_was_connected:
            if self._wifi_lost_at is not None:
                gap = time.monotonic() - self._wifi_lost_at
                if gap < reconnect:
                    self._wifi_was_connected = True
                    msg = (
                        f"Wi-Fi 순간 끊김 ({int(gap)}초) - "
                        f"동일 세션 ({reconnect}초 미만)"
                    )
                    print(f"[안내] {msg}")
                    self._publish("wifi_ok", msg)
                    return
            print("\n[감지] Wi-Fi 연결됨")
            self._wifi_was_connected = True

        remaining = self._cooldown_remaining()
        if remaining > 0:
            state = _load_state(self.config["state_json"])
            code = "gdrive_retry_wait" if state.get("gdrive_retry_pending") else "cooldown"
            label = "G: 재시도" if state.get("gdrive_retry_pending") else "쿨다운"
            self._publish(
                code,
                f"{label} 대기 - {remaining}초 남음",
                remaining_sec=remaining,
            )
            if remaining % 300 < self.config["interval_sec"]:
                print(f"[대기] 자동 파이프라인 쿨다운 - {remaining // 60}분 {remaining % 60}초 남음")
            return

        if self._pipeline_running:
            self._publish("processing", "파이프라인 실행 중")
            return

        self._run_pipeline("메일 확인 → 계산 → G: → Origin (자동)")


def run_data_pc_watch(
    script_dir: str,
    *,
    opju_path: Optional[str] = None,
    auto_archive: bool = True,
    skip_wifi_check: bool = False,
) -> None:
    """촉매 반응 계산.py --watch 진입점."""
    config = load_watch_config(script_dir)
    if not config:
        sys.exit(1)
    if skip_wifi_check:
        config["skip_wifi_check"] = True

    calc_path = os.path.join(script_dir, "촉매 반응 계산.py")
    import importlib.util

    spec = importlib.util.spec_from_file_location("gc_calc_watch", calc_path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"스크립트 로드 실패: {calc_path}")
    calc_mod = importlib.util.module_from_spec(spec)
    sys.modules["gc_calc_watch"] = calc_mod
    spec.loader.exec_module(calc_mod)

    def _process():
        return calc_mod.process_new_gc_emails(
            opju_path=opju_path,
            auto_archive=auto_archive,
        )

    DataPcWatchRunner(
        script_dir,
        config,
        _process,
        g_drive_check=calc_mod._is_g_drive_available,
    ).run_forever()


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="데이터 PC Wi-Fi 감시 → 자동 파이프라인")
    parser.add_argument(
        "--script-dir",
        default=os.path.join(os.path.expanduser("~"), "Desktop", ".cursor"),
        help="Desktop\\.cursor (gc_automation.env 위치)",
    )
    parser.add_argument("--no-archive", action="store_true")
    parser.add_argument("--no-wifi-check", action="store_true", help="테스트용 Wi-Fi 검사 생략")
    args = parser.parse_args()
    run_data_pc_watch(
        args.script_dir,
        auto_archive=not args.no_archive,
        skip_wifi_check=args.no_wifi_check,
    )
