# -*- coding: utf-8 -*-
"""O4 — .opju open / save (originpro session 위)."""

from __future__ import annotations

from types import ModuleType

from data_pc_origin.o0_types import ProbeResult
from data_pc_origin.o1_opju_path import probe_opju_path
from data_pc_origin.o4_errors import OriginOpenError


def validate_opju_path(path: str) -> ProbeResult:
    """O1-P-07 위임."""
    return probe_opju_path(path)


def try_open_project(op: ModuleType, path: str) -> bool:
    """op.open — bool 반환 (촉매 update_origin 동일)."""
    return bool(op.open(path))


def open_project(op: ModuleType, path: str) -> None:
    if not try_open_project(op, path):
        raise OriginOpenError(f"Origin open failed: {path}")


def open_project_with_retry(op: ModuleType, path: str, *, max_retries: int = 1) -> None:
    """실패 시 max_retries 회 재시도 (기본 1회 = 총 2번 open)."""
    attempts = max(1, max_retries + 1)
    last = False
    for _ in range(attempts):
        last = try_open_project(op, path)
        if last:
            return
    raise OriginOpenError(f"Origin open failed after {attempts} tries: {path}")


def save_project(op: ModuleType, path: str) -> None:
    op.save(path)


def save_project_as(op: ModuleType, path: str) -> None:
    op.save(path)
