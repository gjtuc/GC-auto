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


def _origin_evidence(step: str, ok: bool, **fields) -> None:
    try:
        from gc_run_evidence import origin_step

        origin_step(step, ok, **fields)
    except Exception:
        pass


def open_project_with_retry(op: ModuleType, path: str, *, max_retries: int = 1) -> None:
    """실패 시 max_retries 회 재시도 (기본 1회 = 총 2번 open)."""
    attempts = max(1, max_retries + 1)
    last = False
    for attempt in range(1, attempts + 1):
        try:
            last = try_open_project(op, path)
        except Exception as exc:
            _origin_evidence("open", False, opju=path, attempt=attempt, attempts=attempts, exc=exc)
            raise
        if last:
            _origin_evidence("open", True, opju=path, attempt=attempt, attempts=attempts)
            return
        _origin_evidence(
            "open",
            False,
            opju=path,
            attempt=attempt,
            attempts=attempts,
            detail="op.open returned false",
        )
    raise OriginOpenError(f"Origin open failed after {attempts} tries: {path}")


def save_project(op: ModuleType, path: str) -> None:
    try:
        op.save(path)
    except Exception as exc:
        _origin_evidence("save", False, opju=path, exc=exc)
        raise
    _origin_evidence("save", True, opju=path)


def save_project_as(op: ModuleType, path: str) -> None:
    op.save(path)
