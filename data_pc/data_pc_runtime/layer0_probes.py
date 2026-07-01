# -*- coding: utf-8 -*-
"""
L0 — 프로브 (probe): 환경을 **읽기만** 한다. JSON·파이프라인·스케줄러 없음.

하위 단계:
  L0-W  Wi-Fi   W1 netsh 실행 → W2 SSID 파싱 → W3 재시도 → W4 캐시 → W5 허용 목록 대조
  L0-G  G:      G1 EXPERIMENT_DATA_ROOT isdir
  L0-N  네트워크 N1 IMAP TCP 연결 (메일 단계 전 네트워크만)
  L0-P  프로세스 P1 PID 생존 (Windows OpenProcess)
"""

from __future__ import annotations

import socket
import subprocess
import sys
import time
from dataclasses import dataclass
from enum import Enum
from typing import Callable, Sequence

_DEFAULT_G_ROOT = r"G:\연구소\실험\실험데이터"

_SUBPROCESS_FLAGS = 0
if sys.platform == "win32" and hasattr(subprocess, "CREATE_NO_WINDOW"):
    _SUBPROCESS_FLAGS = subprocess.CREATE_NO_WINDOW


class WifiProbeKind(str, Enum):
    CONNECTED_OK = "connected_ok"
    WRONG_SSID = "wrong_ssid"
    DISCONNECTED = "disconnected"
    PROBE_FAILED = "probe_failed"
    PROBE_FAILED_CACHED = "probe_failed_cached"


@dataclass(frozen=True)
class WifiProbeResult:
    kind: WifiProbeKind
    ssid: str | None
    allowed: tuple[str, ...]
    detail: str = ""

    @property
    def ready(self) -> bool:
        return self.kind == WifiProbeKind.CONNECTED_OK


@dataclass(frozen=True)
class GDriveProbeResult:
    available: bool
    root: str
    detail: str = ""


@dataclass(frozen=True)
class NetworkProbeResult:
    imap_reachable: bool
    host: str
    port: int
    detail: str = ""


def parse_required_ssids(raw: str) -> tuple[str, ...]:
    return tuple(part.strip() for part in (raw or "").split(",") if part.strip())


def _parse_ssid_from_netsh(stdout: str) -> str | None:
    for line in stdout.splitlines():
        stripped = line.strip()
        if stripped.startswith("SSID") and not stripped.startswith("BSSID"):
            _, _, value = stripped.partition(":")
            ssid = value.strip()
            if ssid:
                return ssid
    return None


class WifiProbe:
    """L0-W: netsh 기반 SSID 조회 (재시도·TTL 캐시)."""

    def __init__(
        self,
        *,
        netsh_runner: Callable[..., subprocess.CompletedProcess] | None = None,
        cache_ttl_sec: float = 180.0,
        timeout_sec: float = 30.0,
        max_attempts: int = 3,
    ) -> None:
        self._netsh = netsh_runner or self._default_netsh
        self._cache_ttl = cache_ttl_sec
        self._timeout = timeout_sec
        self._max_attempts = max_attempts
        self._cache_at: float = 0.0
        self._cache_ssid: str | None = None

    def _default_netsh(self) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            ["netsh", "wlan", "show", "interfaces"],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=self._timeout,
            creationflags=_SUBPROCESS_FLAGS,
        )

    def _read_ssid_once(self) -> tuple[str | None, str]:
        if sys.platform != "win32":
            return None, "non-windows"
        try:
            result = self._netsh()
        except subprocess.TimeoutExpired:
            return None, "netsh timeout"
        except OSError as exc:
            return None, str(exc)
        if result.returncode != 0:
            return None, f"netsh exit {result.returncode}"
        ssid = _parse_ssid_from_netsh(result.stdout)
        if ssid:
            self._cache_at = time.time()
            self._cache_ssid = ssid
        return ssid, "ok"

    def read_ssid(self) -> tuple[str | None, str]:
        """W1~W4: 재시도 후 실패 시 TTL 캐시."""
        last_detail = ""
        for attempt in range(self._max_attempts):
            ssid, detail = self._read_ssid_once()
            if ssid is not None or detail == "ok":
                return ssid, detail
            last_detail = detail
            if attempt + 1 < self._max_attempts:
                time.sleep(1.5)
        if (
            self._cache_ssid
            and (time.time() - self._cache_at) <= self._cache_ttl
        ):
            return self._cache_ssid, f"cache({last_detail})"
        return None, last_detail

    def check(self, allowed: Sequence[str]) -> WifiProbeResult:
        """W5: 허용 SSID 대조."""
        allowed_t = tuple(allowed)
        if not allowed_t:
            return WifiProbeResult(
                WifiProbeKind.PROBE_FAILED,
                None,
                allowed_t,
                "allowed ssid empty",
            )
        ssid, detail = self.read_ssid()
        if ssid is None:
            kind = (
                WifiProbeKind.PROBE_FAILED_CACHED
                if detail.startswith("cache(")
                else WifiProbeKind.PROBE_FAILED
            )
            return WifiProbeResult(kind, None, allowed_t, detail)
        if ssid in allowed_t:
            return WifiProbeResult(WifiProbeKind.CONNECTED_OK, ssid, allowed_t, detail)
        return WifiProbeResult(
            WifiProbeKind.WRONG_SSID,
            ssid,
            allowed_t,
            f"current={ssid}",
        )


class GDriveProbe:
    """L0-G: G: 루트 폴더 존재만 확인 (SecuYouSB 로그인은 사용자 영역)."""

    def __init__(self, root: str = _DEFAULT_G_ROOT) -> None:
        self.root = root

    def check(self) -> GDriveProbeResult:
        try:
            ok = __import__("os").path.isdir(self.root)
        except OSError as exc:
            return GDriveProbeResult(False, self.root, str(exc))
        if ok:
            return GDriveProbeResult(True, self.root, "isdir")
        return GDriveProbeResult(False, self.root, "not visible")


class ImapReachabilityProbe:
    """L0-N: IMAP 포트 TCP (인증 전)."""

    def __init__(
        self,
        host: str = "imap.naver.com",
        port: int = 993,
        timeout_sec: float = 5.0,
    ) -> None:
        self.host = host
        self.port = port
        self.timeout_sec = timeout_sec

    def check(self) -> NetworkProbeResult:
        try:
            with socket.create_connection(
                (self.host, self.port),
                timeout=self.timeout_sec,
            ):
                return NetworkProbeResult(True, self.host, self.port, "tcp ok")
        except OSError as exc:
            return NetworkProbeResult(False, self.host, self.port, str(exc))


class PidProbe:
    """L0-P: PID 생존 (watchdog용)."""

    @staticmethod
    def alive(pid: int) -> bool:
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
            __import__("os").kill(pid, 0)
            return True
        except OSError:
            return False
