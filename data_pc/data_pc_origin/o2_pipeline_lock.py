# -*- coding: utf-8 -*-
"""O2 — PID·파이프라인 락 조회 (읽기만)."""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class PipelineLockStatus:
    path: str
    exists: bool
    pid: Optional[int]
    pid_alive: bool

    @property
    def busy(self) -> bool:
        return self.exists and self.pid_alive


def pid_alive(pid: int) -> bool:
    if pid <= 0:
        return False
    try:
        os.kill(pid, 0)
    except OSError:
        return False
    return True


def read_pipeline_lock(lock_path: str) -> PipelineLockStatus:
    exists = os.path.isfile(lock_path)
    pid: Optional[int] = None
    alive = False
    if exists:
        try:
            with open(lock_path, encoding="ascii") as f:
                raw = f.read().strip()
            pid = int(raw)
            alive = pid_alive(pid)
        except (OSError, ValueError):
            pid = None
            alive = False
    return PipelineLockStatus(
        path=lock_path,
        exists=exists,
        pid=pid,
        pid_alive=alive,
    )


def pipeline_busy(lock_path: str) -> bool:
    return read_pipeline_lock(lock_path).busy
