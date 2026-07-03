# -*- coding: utf-8
"""P26 — watch resident smoke (native env · --watch entry)."""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Any, Dict, Optional

from data_pc_origin.p16_watch_bridge import describe_watch_mode, should_use_runtime_watch
from data_pc_origin.p17_env_config import effective_origin_config, load_script_env
from data_pc_origin.p22_autostart import build_autostart_manifest, verify_watchdog_delegation


@dataclass
class WatchResidentPrep:
    ready: bool
    reason: str
    watch_mode: str
    runtime_watch: bool
    autostart_ready: bool
    skip_origin: bool

    def to_dict(self) -> Dict[str, Any]:
        return {
            "ready": self.ready,
            "reason": self.reason,
            "watch_mode": self.watch_mode,
            "runtime_watch": self.runtime_watch,
            "autostart_ready": self.autostart_ready,
            "skip_origin": self.skip_origin,
        }


def prep_watch_resident_smoke(script_dir: str) -> WatchResidentPrep:
    """gc_automation.env + P22 autostart — override 없음."""
    load_script_env(script_dir)
    cfg = effective_origin_config(script_dir)
    autostart = build_autostart_manifest(script_dir)
    mode = describe_watch_mode()
    runtime = should_use_runtime_watch()

    failures: list[str] = []
    if not autostart.ready:
        failures.append(f"autostart: {autostart.reason}")
    if not runtime:
        failures.append("legacy watch path")
    if mode != "runtime_origin":
        failures.append(f"watch_mode={mode}")
    if cfg["skip_origin"]:
        failures.append("SKIP_ORIGIN=1")

    ready = not failures
    return WatchResidentPrep(
        ready=ready,
        reason="ready" if ready else "; ".join(failures),
        watch_mode=mode,
        runtime_watch=runtime,
        autostart_ready=autostart.ready,
        skip_origin=bool(cfg["skip_origin"]),
    )


def run_watch_resident_delegate(script_dir: str, *, skip_wifi_check: bool = True) -> Dict[str, Any]:
    """
    `run_data_pc_watch` 1회 — 호출 측에서 `run_supervisor` patch 필요.

    native env만 로드; harness env override 없음.
    """
    load_script_env(script_dir)
    from data_pc_watch import run_data_pc_watch

    run_data_pc_watch(script_dir, skip_wifi_check=skip_wifi_check)
    return {
        "delegated": True,
        "watch_mode": describe_watch_mode(),
        "native_env": True,
    }


def inspect_watchdog_runtime_command(script_dir: str) -> Dict[str, Any]:
    chk = verify_watchdog_delegation(script_dir)
    return {"ok": chk.ok, "detail": chk.detail}


def validate_watch_resident_artifact(payload: Dict[str, Any]) -> bool:
    if payload.get("status") not in ("ok", "partial"):
        return False
    prep = payload.get("prep")
    if not isinstance(prep, dict):
        return False
    return prep.get("runtime_watch") is True and prep.get("skip_origin") is False
