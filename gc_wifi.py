# -*- coding: utf-8 -*-
"""
gc_wifi.py — Windows Wi-Fi SSID, SMTP 준비, 실행 허용 게이트

check_runtime_gate():
  · watch/일반 실행 전 — SSID 일치 (슬롯 한도 없음 — session_based)
  · force=True — SSID·슬롯 모두 생략 (개시 요청·--force)

wait_for_smtp_internet(): Android/iPhone 핫스pot 직후 DNS 지연 대비
"""

from __future__ import annotations

import socket
import subprocess
import sys
import time
from typing import Tuple

from gc_config import (
    NAVER_SMTP_HOST,
    NAVER_SMTP_PORT,
    SMTP_INTERNET_POLL_SEC,
    SMTP_INTERNET_WAIT_MAX_SEC,
    SMTP_SOCKET_TIMEOUT_SEC,
)
from gc_state import can_auto_send_for_mode

_SUBPROCESS_FLAGS = 0
if sys.platform == "win32" and hasattr(subprocess, "CREATE_NO_WINDOW"):
    _SUBPROCESS_FLAGS = subprocess.CREATE_NO_WINDOW


def get_connected_wifi_ssid() -> str | None:
    """Windows netsh 로 현재 Wi-Fi SSID. 미연결·오류 시 None."""
    if sys.platform != "win32":
        return None
    try:
        result = subprocess.run(
            ["netsh", "wlan", "show", "interfaces"],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=15,
            creationflags=_SUBPROCESS_FLAGS,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        print(f"[경고] Wi-Fi SSID 조회 실패: {exc}")
        return None
    if result.returncode != 0:
        return None
    for line in result.stdout.splitlines():
        stripped = line.strip()
        if stripped.startswith("SSID") and not stripped.startswith("BSSID"):
            _, _, value = stripped.partition(":")
            ssid = value.strip()
            if ssid:
                return ssid
    return None


def is_required_hotspot_connected(required_ssid: str, skip_wifi_check: bool = False) -> bool:
    if skip_wifi_check:
        return True
    return get_connected_wifi_ssid() == required_ssid


def hotspot_wait_reason(required_ssid: str) -> str:
    """핫스팟 미연결 시 사용자용 메시지."""
    connected = get_connected_wifi_ssid()
    if connected:
        return f"필수 핫스팟({required_ssid}) 미연결 — 현재: {connected}"
    return f"필수 핫스팟({required_ssid}) 미연결 — Wi-Fi 없음"


def check_smtp_dns_resolvable(host: str = NAVER_SMTP_HOST) -> bool:
    """smtp.naver.com 등 SMTP 호스트 DNS 조회 가능 여부."""
    try:
        socket.getaddrinfo(host, NAVER_SMTP_PORT, type=socket.SOCK_STREAM)
        return True
    except OSError:
        return False


def check_smtp_port_reachable(
    host: str = NAVER_SMTP_HOST,
    port: int = NAVER_SMTP_PORT,
    timeout: float = SMTP_SOCKET_TIMEOUT_SEC,
) -> bool:
    """SMTP 포트 TCP 연결 가능 여부 (DNS 성공 후)."""
    if not check_smtp_dns_resolvable(host):
        return False
    try:
        with socket.create_connection((host, port), timeout=timeout):
            return True
    except OSError:
        return False


def smtp_internet_wait_reason(
    host: str = NAVER_SMTP_HOST,
    port: int = NAVER_SMTP_PORT,
) -> str:
    """SMTP 발송 전 인터넷 미준비 사유. 준비됐으면 빈 문자열."""
    if not check_smtp_dns_resolvable(host):
        return f"DNS 미준비 — {host} 주소 확인 불가 (getaddrinfo)"
    if not check_smtp_port_reachable(host, port):
        return f"SMTP 미연결 — {host}:{port} 포트 접속 불가"
    return ""


def wait_for_smtp_internet(
    max_wait_sec: int = SMTP_INTERNET_WAIT_MAX_SEC,
    poll_sec: int = SMTP_INTERNET_POLL_SEC,
    host: str = NAVER_SMTP_HOST,
    port: int = NAVER_SMTP_PORT,
) -> Tuple[bool, str]:
    """
    핫스팟 연결 직후 DNS·SMTP 준비될 때까지 대기.

    Android 핫스팟은 SSID 연결과 모바일 데이터 라우팅/DNS 준비 시차가 있어
    getaddrinfo failed 가 날 수 있음 — 발송 전에 여기서 먼저 확인.
    """
    if max_wait_sec <= 0:
        reason = smtp_internet_wait_reason(host, port)
        return (not reason, reason or "")

    deadline = time.monotonic() + max_wait_sec
    last_reason = "인터넷 미준비"
    while time.monotonic() < deadline:
        reason = smtp_internet_wait_reason(host, port)
        if not reason:
            return True, ""
        last_reason = reason
        remaining = int(deadline - time.monotonic())
        print(f"[대기] {reason} — {min(poll_sec, max(1, remaining))}초 후 재확인")
        time.sleep(min(poll_sec, max(1, remaining)))

    return False, f"{last_reason} — {max_wait_sec}초 대기 후에도 SMTP 미준비"


def check_runtime_gate(
    required_ssid: str,
    send_email: bool,
    state_path: str,
    skip_wifi_check: bool = False,
    force: bool = False,
    chemstation_mode: str = "auto",
) -> Tuple[bool, str]:
    """
    수동 실행 전 허용 여부.

    force=True: 핫스팟·일일 한도 모두 무시 (사용자 수동 요청).
    watch 자동: session_based — 오전/오후 슬롯 없음, 핫스pot 세션당 1회는 gc_watch 가 담당.
    """
    if not skip_wifi_check and not force:
        connected = get_connected_wifi_ssid()
        if connected != required_ssid:
            if connected:
                return False, f"필수 핫스팟({required_ssid}) 미연결 — 현재: {connected}"
            return False, f"필수 핫스팟({required_ssid}) 미연결 — Wi-Fi 없음"

    if send_email and not force:
        allowed, reason = can_auto_send_for_mode(state_path, chemstation_mode)
        if not allowed:
            return False, f"{reason} — 추가 작업은 --force 로 실행"

    return True, ""
