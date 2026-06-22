# -*- coding: utf-8 -*-
"""
data_pc_watch.py — 은규 PC iPhone 핫스팟 감시 → GC1 메일 대기 → 자동 파이프라인

[흐름]
  GC1 장비 PC: iPhone 핫스팟 edge → Autochro PDF → xlsx → SMTP (약 5분)
  은규 PC (본 모듈): 동일 iPhone 핫스팟 연결 감지 → 5분 대기 → IMAP 메일 → 계산 → Origin

[설정] gc-data-pc\\gc_automation.env
  REQUIRED_HOTSPOT=iPhone
  DATA_PC_HOTSPOT_DELAY_SEC=300
  DATA_PC_WATCH_INTERVAL_SEC=15
  DATA_PC_HOTSPOT_RECONNECT_MIN_SEC=90

[실행]
  python "촉매 반응 계산.py" --watch
  deploy\\gc_data_pc_start_watch.bat
"""

from __future__ import annotations

import json
import os
import sys
import time
from datetime import datetime
from typing import Callable, Optional


def _repo_root() -> str:
    return os.path.join(os.path.expanduser("~"), "chemstation-gc-automation")


def _import_gc_wifi():
    repo = _repo_root()
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


def _env_int(name: str, default: int, *, minimum: int = 1) -> int:
    try:
        value = int(os.getenv(name, str(default)).strip())
    except (TypeError, ValueError):
        value = default
    return max(minimum, value)


def load_watch_config(script_dir: str) -> dict:
    """gc_automation.env 에서 핫스팟·감시 설정 로드."""
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
        or "iPhone"
    )
    return {
        "required_ssid": required,
        "delay_sec": _env_int("DATA_PC_HOTSPOT_DELAY_SEC", 300, minimum=0),
        "interval_sec": _env_int("DATA_PC_WATCH_INTERVAL_SEC", 15, minimum=5),
        "reconnect_min_sec": _env_int("DATA_PC_HOTSPOT_RECONNECT_MIN_SEC", 90, minimum=0),
        "skip_wifi_check": _env_bool("DATA_PC_SKIP_WIFI_CHECK"),
        "boot_mail_check": _env_bool("DATA_PC_BOOT_MAIL_CHECK", True),
        "boot_network_wait_sec": _env_int("DATA_PC_BOOT_NETWORK_WAIT_SEC", 90, minimum=10),
        "status_json": os.path.join(
            script_dir, "PEG", ".data_pc_watch_status.json"
        ),
    }


def _write_status(path: str, payload: dict) -> None:
    try:
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(payload, f, ensure_ascii=False, indent=2)
    except OSError:
        pass


class DataPcWatchRunner:
    """핫스팟 edge → delay_sec 대기 → process_callback 1회 (세션당)."""

    def __init__(
        self,
        script_dir: str,
        config: dict,
        process_callback: Callable[[], int],
    ):
        self.script_dir = script_dir
        self.config = config
        self.process_callback = process_callback
        self._hotspot_was_connected = False
        self._hotspot_lost_at: Optional[float] = None
        self._run_after_mono: Optional[float] = None
        self._session_processed = False
        self._pipeline_running = False
        self._started_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        (
            self._get_ssid,
            self._is_connected,
            self._wait_reason,
        ) = _import_gc_wifi()

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
            "delay_sec": self.config["delay_sec"],
            "started_at": self._started_at,
            "updated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "last_heartbeat": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "pid": os.getpid(),
            **extra,
        }
        _write_status(self.config["status_json"], payload)

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

    def _run_boot_mail_check(self) -> None:
        """PC 꺼져 있는 동안 도착한 메일을 로그인 직후 1회 처리."""
        if not self.config.get("boot_mail_check", True):
            return
        wait = self.config.get("boot_network_wait_sec", 90)
        print("[부팅] 미처리 메일 확인 (PC 꺼진 동안 수신분)")
        self._publish("boot_mail_check", "부팅 후 미처리 메일 확인 중")
        if not self._wait_for_network(wait):
            print("[부팅] 네트워크 미준비 - 핫스팟 감시는 계속됩니다")
            self._publish("boot_network_wait", "네트워크 대기 중")
            return
        if self._pipeline_running:
            return
        self._pipeline_running = True
        try:
            count = self.process_callback()
            print(f"[부팅] 미처리 메일 반영 완료 - {count}건")
            self._publish("boot_mail_done", f"부팅 메일 확인 완료 - {count}건", workflow_count=count)
        except Exception as exc:
            print(f"[부팅] 메일 확인 실패: {exc}")
            self._publish("boot_mail_error", str(exc))
        finally:
            self._pipeline_running = False

    def run_forever(self) -> None:
        interval = self.config["interval_sec"]
        delay = self.config["delay_sec"]
        reconnect = self.config["reconnect_min_sec"]
        ssid = self.config["required_ssid"]

        print(f"[안내] 은규 PC 핫스팟 감시 - {interval}초 간격, SSID: {ssid}")
        print(
            f"       핫스팟 연결 후 {delay}초 대기 -> 메일 확인 -> 계산 -> Origin (승인 없음)"
        )
        print(f"       순간 끊김({reconnect}초 미만 재연결) - 동일 세션, 중복 없음")
        print("       종료: Ctrl+C")
        self._publish("starting", "은규 PC 핫스팟 감시 시작")
        self._run_boot_mail_check()

        try:
            while True:
                self._tick()
                time.sleep(interval)
        except KeyboardInterrupt:
            print("\n[안내] 핫스팟 감시 종료 (Ctrl+C)")
        finally:
            _write_status(
                self.config["status_json"],
                {
                    "alive": False,
                    "status_code": "stopped",
                    "message": "감시 종료됨",
                    "updated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                },
            )

    def _reset_session(self) -> None:
        self._run_after_mono = None
        self._session_processed = False

    def _on_hotspot_connected(self) -> None:
        delay = self.config["delay_sec"]
        self._run_after_mono = time.monotonic() + delay
        self._session_processed = False
        eta = datetime.now().timestamp() + delay
        eta_str = datetime.fromtimestamp(eta).strftime("%H:%M:%S")
        print(f"\n[감지] iPhone 핫스팟 연결 - GC1 작업 대기 {delay}초 (예상 시작: {eta_str})")
        self._publish(
            "hotspot_connected_waiting",
            f"핫스팟 연결 - {delay}초 후 메일·파이프라인 자동 실행",
            run_after_epoch=eta,
        )

    def _tick(self) -> None:
        ssid = self.config["required_ssid"]
        skip = self.config["skip_wifi_check"]
        reconnect = self.config["reconnect_min_sec"]

        if not self._is_connected(ssid, skip):
            if self._hotspot_was_connected:
                self._hotspot_lost_at = time.monotonic()
            self._hotspot_was_connected = False
            reason = self._wait_reason(ssid)
            self._publish("waiting_wifi", reason)
            print(f"[대기] {reason}")
            return

        if not self._hotspot_was_connected:
            if self._hotspot_lost_at is not None:
                gap = time.monotonic() - self._hotspot_lost_at
                if gap < reconnect:
                    self._hotspot_was_connected = True
                    msg = (
                        f"핫스팟 순간 끊김 ({int(gap)}초) - "
                        f"동일 세션 ({reconnect}초 미만, 재예약 안 함)"
                    )
                    print(f"[안내] {msg}")
                    self._publish("wifi_ok", msg)
                    return
            self._hotspot_was_connected = True
            self._on_hotspot_connected()
            return

        self._hotspot_was_connected = True

        if self._session_processed or self._run_after_mono is None:
            self._publish("wifi_ok", "핫스팟 연결 유지 - 이번 세션 처리 완료 또는 대기 중")
            return

        if self._pipeline_running:
            self._publish("processing", "파이프라인 실행 중")
            return

        remaining = self._run_after_mono - time.monotonic()
        if remaining > 0:
            self._publish(
                "waiting_gc1",
                f"GC1 메일 대기 - {int(remaining)}초 남음",
                remaining_sec=int(remaining),
            )
            if int(remaining) % 30 < self.config["interval_sec"]:
                print(f"[대기] GC1 작업·메일 대기 - {int(remaining)}초 남음")
            return

        self._pipeline_running = True
        try:
            print("\n[실행] 메일 확인 -> 계산 -> 연구노트 -> Origin (자동)")
            self._publish("running_pipeline", "메일·파이프라인 자동 실행 중")
            count = self.process_callback()
            self._session_processed = True
            msg = f"파이프라인 완료 - {count}건 시료 반영"
            print(f"[완료] {msg}")
            self._publish("pipeline_done", msg, workflow_count=count)
        except Exception as exc:
            print(f"[오류] 파이프라인 실패: {exc}")
            self._publish("error", str(exc))
        finally:
            self._pipeline_running = False


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

    def _process() -> int:
        import importlib.util

        calc_path = os.path.join(script_dir, "촉매 반응 계산.py")
        spec = importlib.util.spec_from_file_location("gc_calc_watch", calc_path)
        if spec is None or spec.loader is None:
            raise RuntimeError(f"스크립트 로드 실패: {calc_path}")
        mod = importlib.util.module_from_spec(spec)
        sys.modules["gc_calc_watch"] = mod
        spec.loader.exec_module(mod)
        return mod.process_new_gc_emails(
            opju_path=opju_path,
            auto_archive=auto_archive,
        )

    DataPcWatchRunner(script_dir, config, _process).run_forever()


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="은규 PC 핫스팟 감시 → 자동 파이프라인")
    parser.add_argument(
        "--script-dir",
        default=os.path.dirname(os.path.abspath(__file__)),
        help="gc-data-pc 폴더 (gc_automation.env 위치)",
    )
    parser.add_argument("--no-archive", action="store_true")
    parser.add_argument("--no-wifi-check", action="store_true", help="테스트용 핫스팟 검사 생략")
    args = parser.parse_args()
    run_data_pc_watch(
        args.script_dir,
        auto_archive=not args.no_archive,
        skip_wifi_check=args.no_wifi_check,
    )
