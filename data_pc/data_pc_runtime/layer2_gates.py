# -*- coding: utf-8 -*-
"""
L2 — 게이트: L0 프로브 + L1 상태 + 설정 → **파이프라인 1회 실행 허용?**

하위 단계 (순서 고정 — 앞에서 막히면 뒤는 평가 안 함):
  L2-0  skip_wifi_check (테스트·수동)
  L2-1  Wi-Fi 게이트     (L0-W)
  L2-2  IMAP TCP 게이트  (L0-N, 선택)
  L2-3  파이프라인 락   (L2-lock)
  L2-4  쿨다운 / G:재시도 (L1 state)
  L2-5  READY → 실행

status_code 는 기존 data_pc_watch 와 호환되는 이름 유지.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from data_pc_runtime.layer0_probes import (
    GDriveProbe,
    ImapReachabilityProbe,
    WifiProbe,
    WifiProbeKind,
)
from data_pc_runtime.layer1_state import RuntimePaths, StateStore


class GateAction(str, Enum):
    RUN = "run"
    WAIT = "wait"


@dataclass(frozen=True)
class GateConfig:
    required_hotspot: str = "iptime,iptime 2,iptime_5G"
    cooldown_sec: int = 3600
    gdrive_retry_sec: int = 900
    skip_wifi_check: bool = False
    check_imap_tcp: bool = False
    pipeline_locked: bool = False


@dataclass(frozen=True)
class GateVerdict:
    action: GateAction
    status_code: str
    message: str
    wifi_ssid: str | None = None
    wifi_ready: bool = False
    cooldown_remaining_sec: int = 0
    detail: str = ""


class GateEvaluator:
    def __init__(
        self,
        paths: RuntimePaths,
        *,
        wifi: WifiProbe | None = None,
        gdrive: GDriveProbe | None = None,
        imap: ImapReachabilityProbe | None = None,
        store: StateStore | None = None,
    ) -> None:
        self.paths = paths
        self.wifi = wifi or WifiProbe()
        self.gdrive = gdrive or GDriveProbe()
        self.imap = imap or ImapReachabilityProbe()
        self.store = store or StateStore(paths)

    def evaluate(self, config: GateConfig) -> GateVerdict:
        allowed = tuple(
            s.strip()
            for s in config.required_hotspot.split(",")
            if s.strip()
        )

        # L2-0 / L2-1
        if config.skip_wifi_check:
            wifi_ready = True
            ssid = None
            wifi_detail = "skip"
        else:
            wifi_result = self.wifi.check(allowed)
            ssid = wifi_result.ssid
            wifi_ready = wifi_result.ready
            wifi_detail = wifi_result.detail
            if not wifi_ready:
                return self._wait(
                    _wifi_status_code(wifi_result.kind),
                    _wifi_message(wifi_result.kind, allowed, ssid),
                    ssid=ssid,
                    detail=wifi_detail,
                )

        # L2-2
        if config.check_imap_tcp:
            net = self.imap.check()
            if not net.imap_reachable:
                return self._wait(
                    "boot_network_wait",
                    f"IMAP TCP 불가 — {net.detail}",
                    ssid=ssid,
                    wifi_ready=wifi_ready,
                    detail=net.detail,
                )

        # L2-3
        if config.pipeline_locked:
            return self._wait(
                "processing",
                "다른 파이프라인 실행 중",
                ssid=ssid,
                wifi_ready=wifi_ready,
                detail="lock held",
            )

        # L2-4
        gdrive_ok = self.gdrive.check().available
        remaining = self.store.cooldown_remaining_sec(
            cooldown_sec=config.cooldown_sec,
            gdrive_retry_sec=config.gdrive_retry_sec,
            gdrive_available=gdrive_ok,
        )
        state = self.store.load_state()
        if remaining > 0:
            if state.gdrive_retry_pending:
                code = "gdrive_retry_wait"
                label = "G: 재시도"
            else:
                code = "cooldown"
                label = "쿨다운"
            return self._wait(
                code,
                f"{label} 대기 — {remaining}초 남음",
                ssid=ssid,
                wifi_ready=wifi_ready,
                cooldown_remaining_sec=remaining,
                detail=wifi_detail,
            )

        # L2-5
        return GateVerdict(
            action=GateAction.RUN,
            status_code="ready",
            message="메일 확인 → 계산 → G: → Origin (자동)",
            wifi_ssid=ssid,
            wifi_ready=wifi_ready,
            cooldown_remaining_sec=0,
            detail=wifi_detail,
        )

    @staticmethod
    def _wait(
        code: str,
        message: str,
        *,
        ssid: str | None = None,
        wifi_ready: bool = False,
        cooldown_remaining_sec: int = 0,
        detail: str = "",
    ) -> GateVerdict:
        return GateVerdict(
            action=GateAction.WAIT,
            status_code=code,
            message=message,
            wifi_ssid=ssid,
            wifi_ready=wifi_ready,
            cooldown_remaining_sec=cooldown_remaining_sec,
            detail=detail,
        )


def _wifi_status_code(kind: WifiProbeKind) -> str:
    if kind in (WifiProbeKind.PROBE_FAILED, WifiProbeKind.PROBE_FAILED_CACHED):
        return "wifi_probe_failed"
    return "waiting_wifi"


def _wifi_message(
    kind: WifiProbeKind,
    allowed: tuple[str, ...],
    ssid: str | None,
) -> str:
    label = " / ".join(allowed) if len(allowed) > 1 else (allowed[0] if allowed else "?")
    if kind == WifiProbeKind.WRONG_SSID:
        return f"필수 Wi-Fi({label}) 미연결 — 현재: {ssid}"
    if kind == WifiProbeKind.PROBE_FAILED_CACHED:
        return f"필수 Wi-Fi({label}) — SSID 조회 실패, 캐시 사용 중"
    if kind == WifiProbeKind.PROBE_FAILED:
        return f"필수 Wi-Fi({label}) 미연결 — Wi-Fi 없음 (netsh 실패)"
    return f"필수 Wi-Fi({label}) 미연결 — Wi-Fi 없음"
