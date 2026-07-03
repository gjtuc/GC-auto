# -*- coding: utf-8 -*-
"""O2 — Origin 진입 gate chain."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from data_pc_origin.o0_types import ProbeResult
from data_pc_origin.o2_env import skip_origin_active
from data_pc_origin.o2_origin_lock import OriginLock
from data_pc_origin.o2_pipeline_lock import pipeline_busy


@dataclass(frozen=True)
class GateVerdict:
    code: str
    detail: str = ""
    reason: str = ""


def evaluate_origin_gate(
    *,
    opju_probe: ProbeResult,
    pipeline_lock_path: str,
    origin_lock_path: str,
    skip_origin: Optional[bool] = None,
    acquire_origin_lock: bool = True,
) -> GateVerdict:
    """
    순서: skip → probe → pipeline busy → origin lock → READY.
    skip_origin=None 이면 env DATA_PC_SKIP_ORIGIN 사용.
    """
    if skip_origin if skip_origin is not None else skip_origin_active():
        return GateVerdict(code="skip_origin", detail="DATA_PC_SKIP_ORIGIN", reason="env")

    if not opju_probe.ok:
        return GateVerdict(
            code="wait",
            detail=opju_probe.detail or "probe failed",
            reason="probe_fail",
        )

    if pipeline_busy(pipeline_lock_path):
        return GateVerdict(code="wait", detail=pipeline_lock_path, reason="pipeline_busy")

    if acquire_origin_lock:
        lock = OriginLock(origin_lock_path, timeout_sec=0.0)
        if not lock.try_acquire():
            return GateVerdict(code="wait", detail=origin_lock_path, reason="origin_lock")
        lock.release()

    return GateVerdict(code="ready", detail="ok", reason="")
