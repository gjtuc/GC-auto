# -*- coding: utf-8 -*-
"""
gc_status.py — 감시 상태 표시 (KCH TXT/JSON + 바탕화면 MMDDHHmm.txt)

=============================================================================
[바탕화면 MMDDHHmm.txt — GC 전체 OK 판정]
=============================================================================

  --watch 가 **필수 핫스팟에 연결된 동안만** 바탕화면 파일 이름을 현재 시각으로
  바꿉니다. Wi-Fi 미연결·다른 SSID 이면 파일명은 멈춘 채 유지됩니다.

    예) 2026-06-15 15:13 + 핫스팟 OK → 06151513.txt

  **다른 PC에서 확인할 때는 이것만 보면 됩니다:**

    1) 바탕화면에 8자리.txt (06151513.txt) 가 있는가?
    2) 파일명 시각 ↔ 지금 시각 차이가 ±5분 이내인가?

    OK  → watch + 핫스팟 + 자동화 준비 완료 (Cursor 추가 작업 불필요)
    FAIL → watch 멈춤 또는 핫스팟 미연결 → gc_start_watch.bat / Wi-Fi 확인

  CLI: python gc_automation.py --verify
  bat: gc_verify.bat

[상세 상태 — 선택]
  Desktop\\KCH\\GC_감시_상태.txt, gc_watch_status.bat, --status
"""

from __future__ import annotations

import json
import os
import re
import sys
from dataclasses import dataclass
from datetime import datetime
from typing import Optional

from gc_config import DESKTOP_STOPPED_PREFIX, HEARTBEAT_TOLERANCE_MINUTES
from gc_state import (
    format_today_session_send_status,
    get_today_session_send_count,
    load_send_state,
)

DESKTOP_HEARTBEAT_RE = re.compile(r"^\d{8}\.txt$")
_last_desktop_heartbeat_path: str | None = None


def get_desktop_dir() -> str:
    """Windows 사용자 바탕화면 실제 경로 (OneDrive 등 포함)."""
    if sys.platform == "win32":
        try:
            import ctypes
            from ctypes import wintypes

            CSIDL_DESKTOPDIRECTORY = 0x0010
            buf = ctypes.create_unicode_buffer(wintypes.MAX_PATH)
            if ctypes.windll.shell32.SHGetFolderPathW(None, CSIDL_DESKTOPDIRECTORY, None, 0, buf) == 0:
                path = buf.value
                if path and os.path.isdir(path):
                    return path
        except (OSError, AttributeError):
            pass
    return os.path.join(os.path.expanduser("~"), "Desktop")


def _is_desktop_heartbeat_file(name: str) -> bool:
    return bool(DESKTOP_HEARTBEAT_RE.match(name) or name.startswith(DESKTOP_STOPPED_PREFIX))


def _sync_last_heartbeat_path_from_disk() -> None:
    """프로세스 재시작·날짜 변경 후에도 디스크에 남은 heartbeat 파일을 추적."""
    global _last_desktop_heartbeat_path
    if _last_desktop_heartbeat_path and os.path.isfile(_last_desktop_heartbeat_path):
        return
    latest = find_latest_desktop_heartbeat_file()
    if latest:
        _last_desktop_heartbeat_path = latest


def _cleanup_stale_desktop_heartbeats(desktop: str, keep_path: str) -> None:
    """현재 heartbeat 1개만 남기고 나머지 MMDDHHmm.txt / GC_중지_*.txt 삭제."""
    try:
        for entry in os.scandir(desktop):
            if not entry.is_file():
                continue
            if entry.path == keep_path:
                continue
            if _is_desktop_heartbeat_file(entry.name):
                try:
                    os.remove(entry.path)
                except OSError:
                    pass
    except OSError:
        pass


class StatusReporter:
    """
    --watch 루프에서 매 tick 마다 상태를 갱신하는 클래스.

    한 곳에서 KCH 상세 TXT, JSON, 바탕화면 시각 파일을 함께 업데이트합니다.
    """

    def __init__(
        self,
        status_json_path: str,
        status_txt_path: str,
        required_ssid: str,
        watch_interval: int,
        send_state_path: str,
        started_at: str,
    ):
        self.status_json_path = status_json_path
        self.status_txt_path = status_txt_path
        self.required_ssid = required_ssid
        self.watch_interval = watch_interval
        self.send_state_path = send_state_path
        self.started_at = started_at

    def _today_send_summary(self) -> str:
        today_str = datetime.now().strftime("%Y%m%d")
        return format_today_session_send_status(load_send_state(self.send_state_path), today_str)

    def _today_send_count(self) -> int:
        today_str = datetime.now().strftime("%Y%m%d")
        return get_today_session_send_count(load_send_state(self.send_state_path), today_str)

    def publish(
        self,
        *,
        alive: bool,
        status_code: str,
        message: str,
        wifi_ssid: str | None = None,
        wifi_ready: bool = False,
        last_action: str | None = None,
        sequence_folder: str | None = None,
    ) -> None:
        """상태 갱신 — JSON/TXT는 매 tick, 바탕화면 heartbeat는 wifi_ready 일 때만."""
        now = datetime.now()
        heartbeat = now.strftime("%Y-%m-%d %H:%M:%S")
        payload = {
            "alive": alive,
            "status_code": status_code,
            "message": message,
            "pid": os.getpid(),
            "started_at": self.started_at,
            "last_heartbeat": heartbeat,
            "required_ssid": self.required_ssid,
            "wifi_ssid": wifi_ssid,
            "today_send_count": self._today_send_count(),
            "today_send_summary": self._today_send_summary(),
            "daily_send_limit": 0,
            "watch_interval_sec": self.watch_interval,
            "last_action": last_action,
            "sequence_folder": sequence_folder,
        }
        os.makedirs(os.path.dirname(self.status_json_path) or ".", exist_ok=True)
        with open(self.status_json_path, "w", encoding="utf-8") as status_file:
            json.dump(payload, status_file, ensure_ascii=False, indent=2)

        state_label = "실행 중" if alive else "중지됨"
        if wifi_ssid:
            if wifi_ssid == self.required_ssid:
                wifi_line = f"{wifi_ssid} (필수 SSID 일치)"
            else:
                wifi_line = f"{wifi_ssid} (필수 SSID와 다름)"
        else:
            wifi_line = f"미연결 (필수: {self.required_ssid})"

        stale_minutes = max(2, (self.watch_interval * 2 + 59) // 60)
        txt_lines = [
            "========================================",
            "  GC 자동 감시 상태",
            "========================================",
            f"상태: {state_label} — {message}",
            f"갱신: {heartbeat}",
            "",
            f"Wi-Fi: {wifi_line}",
            f"오늘 자동 메일: {payload['today_send_summary']}",
            f"감시 주기: {self.watch_interval}초",
            "",
            f"시작 시각: {self.started_at}",
        ]
        if last_action:
            txt_lines.append(f"마지막 처리: {last_action}")
        if sequence_folder:
            txt_lines.append(f"시퀀스 폴더: {sequence_folder}")
        txt_lines.extend(
            [
                "",
                f"※ '갱신' 시각이 {stale_minutes}분 이상 변하지 않으면 감시가 멈춘 것입니다.",
                "※ 핫스팟 연결 중에만 MMDDHHmm.txt 이름이 갱신됩니다.",
                "========================================",
                "",
            ]
        )
        with open(self.status_txt_path, "w", encoding="utf-8") as status_file:
            status_file.write("\n".join(txt_lines))

        if not alive or wifi_ready:
            _update_desktop_heartbeat(alive=alive, message=message, now=now)


def _update_desktop_heartbeat(alive: bool, message: str, now: datetime | None = None) -> None:
    """
    바탕화면 MMDDHHmm.txt — **GC 전체 OK 검증의 유일한 근거**.

    필수 핫스팟 연결 + alive 일 때만 매 tick:
      · 06151513.txt 처럼 파일 **이름**을 현재 시각으로 rename
      · 어제·중복 파일은 갱신 전후에 삭제해 1개만 유지

    Wi-Fi 미연결 → 파일명 갱신 안 함 (마지막 연결 시각에 고정)
    alive=False (--watch 종료) → GC_중지_MMDDHHmm.txt 로 변경

    verify_desktop_heartbeat() 는 이 파일명 시각 ±5분만 검사합니다.
    """
    global _last_desktop_heartbeat_path
    desktop = get_desktop_dir()
    os.makedirs(desktop, exist_ok=True)
    now = now or datetime.now()
    display_time = now.strftime("%m%d%H%M")
    heartbeat_full = now.strftime("%Y-%m-%d %H:%M:%S")

    if alive:
        new_name = f"{display_time}.txt"
        content_lines = [
            "GC 자동 감시 실행 중",
            f"파일 이름 = 컴퓨터 시각 (MMDDHHmm) → 지금은 {display_time}",
            f"갱신: {heartbeat_full}",
            f"상태: {message}",
            "",
            "※ 파일 이름이 지금 시각과 2분 이상 차이 → 감시 멈춤 또는 핫스팟 미연결",
            "※ 핫스팟 연결 중 1분마다 파일 이름이 바뀌면 정상",
        ]
    else:
        new_name = f"{DESKTOP_STOPPED_PREFIX}{display_time}.txt"
        content_lines = [
            "GC 자동 감시 종료됨",
            f"기록 시각: {heartbeat_full}",
            "",
            "gc_start_watch.bat 로 다시 시작하세요.",
        ]

    new_path = os.path.join(desktop, new_name)
    content = "\n".join(content_lines) + "\n"

    _sync_last_heartbeat_path_from_disk()
    _cleanup_stale_desktop_heartbeats(desktop, keep_path=new_path)

    if (
        _last_desktop_heartbeat_path
        and _last_desktop_heartbeat_path != new_path
        and os.path.isfile(_last_desktop_heartbeat_path)
    ):
        try:
            os.replace(_last_desktop_heartbeat_path, new_path)
        except OSError:
            pass

    with open(new_path, "w", encoding="utf-8") as status_file:
        status_file.write(content)

    _last_desktop_heartbeat_path = new_path
    _cleanup_stale_desktop_heartbeats(desktop, keep_path=new_path)


@dataclass
class DesktopHeartbeatCheck:
    """
    verify_desktop_heartbeat() 결과.

    ok=True  … 파일명 시각이 now ± tolerance_minutes 이내
    ok=False … 파일 없음 / 이름 파싱 실패 / 5분 이상 지연
    """

    ok: bool
    filename: Optional[str] = None
    file_time: Optional[datetime] = None
    delta_minutes: Optional[float] = None
    reason: str = ""


def _parse_heartbeat_filename(filename: str) -> Optional[datetime]:
    """
    06151513.txt → datetime(올해, 6, 15, 15, 13)

    연도는 파일명에 없으므로 datetime.now().year 사용.
    """
    if not DESKTOP_HEARTBEAT_RE.match(filename):
        return None
    stem = filename[:-4]
    try:
        month = int(stem[0:2])
        day = int(stem[2:4])
        hour = int(stem[4:6])
        minute = int(stem[6:8])
        now = datetime.now()
        return datetime(now.year, month, day, hour, minute)
    except (ValueError, IndexError):
        return None


def _minute_delta(a: datetime, b: datetime) -> float:
    return abs((a - b).total_seconds()) / 60.0


def find_latest_desktop_heartbeat_file() -> Optional[str]:
    """바탕화면에서 가장 최근 MMDDHHmm.txt (GC_중지_ 제외)."""
    desktop = get_desktop_dir()
    candidates = []
    try:
        for entry in os.scandir(desktop):
            if entry.is_file() and DESKTOP_HEARTBEAT_RE.match(entry.name):
                candidates.append(entry.path)
    except OSError:
        return None
    if not candidates:
        return None
    return max(candidates, key=os.path.getmtime)


def verify_desktop_heartbeat(tolerance_minutes: int = HEARTBEAT_TOLERANCE_MINUTES) -> DesktopHeartbeatCheck:
    """
    GC 자동화 **전체** OK 여부 — 이 함수만으로 판단합니다.

    확인 항목 (이 두 가지뿐):
      · 바탕화면 MMDDHHmm.txt 존재 (GC_중지_ 접두사 파일은 제외)
      · 파일 **이름**에 적힌 시각 vs 현재 시각 → ±tolerance_minutes (기본 5분)

    force 성공 여부·메일 발송 여부·KCH JSON 은 **여기서 보지 않습니다.**
    핫스팟 연결 중 watch 가 돌면 파일 이름이 1분마다 바뀌므로 ±5분이면 정상입니다.
    """
    path = find_latest_desktop_heartbeat_file()
    if not path:
        return DesktopHeartbeatCheck(
            ok=False,
            reason="바탕화면 MMDDHHmm.txt 없음 — --watch 미실행, 멈춤, 또는 아직 핫스팟 미연결",
        )

    filename = os.path.basename(path)
    file_time = _parse_heartbeat_filename(filename)
    if file_time is None:
        return DesktopHeartbeatCheck(
            ok=False,
            filename=filename,
            reason=f"파일명 시각 파싱 실패: {filename}",
        )

    now = datetime.now()
    delta = _minute_delta(file_time, now)

    # 연말·연초 경계 (±1일)
    if delta > tolerance_minutes + 12 * 60:
        for year in (now.year - 1, now.year + 1):
            try:
                alt = file_time.replace(year=year)
                delta = min(delta, _minute_delta(alt, now))
            except ValueError:
                pass

    if delta <= tolerance_minutes:
        return DesktopHeartbeatCheck(
            ok=True,
            filename=filename,
            file_time=file_time,
            delta_minutes=delta,
            reason=f"정상 — {filename} (±{tolerance_minutes}분 이내, 차이 {delta:.1f}분)",
        )

    return DesktopHeartbeatCheck(
        ok=False,
        filename=filename,
        file_time=file_time,
        delta_minutes=delta,
        reason=(
            f"비정상 — {filename} 시각과 현재 시각 차이 {delta:.1f}분 "
            f"(허용 ±{tolerance_minutes}분) — watch 멈춤 또는 핫스팟 미연결"
        ),
    )


def print_verify_result(check: DesktopHeartbeatCheck) -> None:
    if check.ok:
        print(f"[OK] {check.reason}")
    else:
        print(f"[FAIL] {check.reason}")


def is_watch_alive(status_json_path: str, max_stale_sec: int = 150) -> bool:
    """--watch 프로세스가 살아 있는지 (JSON heartbeat 기준)."""
    if not os.path.isfile(status_json_path):
        return False
    try:
        with open(status_json_path, encoding="utf-8") as status_file:
            data = json.load(status_file)
    except (OSError, json.JSONDecodeError):
        return False
    if not data.get("alive"):
        return False
    heartbeat = data.get("last_heartbeat")
    if not heartbeat:
        return False
    try:
        last = datetime.strptime(heartbeat, "%Y-%m-%d %H:%M:%S")
    except ValueError:
        return False
    age = (datetime.now() - last).total_seconds()
    return age <= max_stale_sec


def show_watch_status(status_json_path: str, status_txt_path: str) -> None:
    """--status: 저장된 상태 출력."""
    desktop = get_desktop_dir()
    desktop_files = []
    try:
        for entry in os.scandir(desktop):
            if entry.is_file() and (
                DESKTOP_HEARTBEAT_RE.match(entry.name)
                or entry.name.startswith(DESKTOP_STOPPED_PREFIX)
            ):
                desktop_files.append(entry.path)
    except OSError:
        pass

    if desktop_files:
        latest_desktop = max(desktop_files, key=os.path.getmtime)
        print(f"[바탕화면] {os.path.basename(latest_desktop)}")
        with open(latest_desktop, encoding="utf-8") as status_file:
            print(status_file.read())
        if not os.path.isfile(status_txt_path):
            return

    if os.path.isfile(status_txt_path):
        if desktop_files:
            print("-" * 40)
        with open(status_txt_path, encoding="utf-8") as status_file:
            print(status_file.read())
        return

    if os.path.isfile(status_json_path):
        with open(status_json_path, encoding="utf-8") as status_file:
            data = json.load(status_file)
        print("[안내] GC_감시_상태.txt 없음 — JSON 요약:")
        print(f"  alive: {data.get('alive')}")
        print(f"  message: {data.get('message')}")
        print(f"  last_heartbeat: {data.get('last_heartbeat')}")
        return

    print("[안내] 감시 기록 없음 — --watch 가 한 번도 실행되지 않았거나 상태 파일이 삭제됨.")
