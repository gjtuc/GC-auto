# -*- coding: utf-8
"""O9 — pipeline facade (촉매 update_origin 대응)."""

from __future__ import annotations

import inspect
import logging
import os
import sys
from dataclasses import dataclass
from typing import Any, Callable, Optional, Tuple

from data_pc_origin.o0_equipment_day import EquipmentDayGuardResult
from data_pc_origin.o0_types import OriginWarning
from data_pc_origin.o6_guard import ColumnGuardConfirm
from data_pc_origin.o1_opju_path import probe_opju_path
from data_pc_origin.o8_context import build_context
from data_pc_origin.o8_job import SampleJobResult, run_sample_job
from data_pc_origin.o8_save import resolve_save_path

IdentityKey = Tuple[str, str]
PrintFn = Callable[[str], None]
LogFn = Callable[[str], None]

LOG_PREFIX = "[Origin]"
_LOGGER = logging.getLogger("data_pc_origin")


@dataclass(frozen=True)
class OriginUpdateResult:
    ok: bool
    sheets_updated: int
    row_count: int
    warnings: Tuple[OriginWarning, ...]
    opju_path: str
    sample_name: str


def origin_log(message: str, *, log_fn: LogFn | None = None) -> str:
    """O9-F-04 — `[Origin]` 접두 로그."""
    line = f"{LOG_PREFIX} {message}"
    if log_fn is not None:
        log_fn(line)
    else:
        _LOGGER.info("%s", line)
    return line


def print_stage4_ux(
    *,
    sample_name: str,
    job: SampleJobResult,
    opju_path: str,
    save_in_place: bool,
    printer: PrintFn,
) -> None:
    """O9-F-05 — 촉매 L1695–1733 UX."""
    printer(f"\n[4단계] Origin 워크시트 — Comments: '{sample_name}'")
    if job.updated_count > 0:
        printer(f"  → 워크시트 {job.updated_count}개 · {job.row_count}행 반영")
        save_path = job.saved_path or resolve_save_path(opju_path, save_in_place)
        if save_in_place:
            printer(f" ✅ Origin 저장 완료: {save_path}")
        else:
            printer(f" ✅ Origin 파일 업데이트 완료! 저장 위치: {save_path}")
    else:
        printer(" ⚠️ Origin에서 일치하는 데이터 시트를 하나도 찾지 못했습니다.")


def default_interactive_column_guard_confirm(
    guard: EquipmentDayGuardResult,
    *,
    printer: PrintFn = print,
) -> bool:
    """터미널 대화형 — 장비·날짜 규칙 위반 시 사용자 확인."""
    printer("\n" + "?" * 65)
    printer(" ❓ [Origin 열 추가 확인] 같은 장비·날짜 규칙")
    printer(guard.question)
    printer("?" * 65)
    try:
        ans = input("Origin에 새 열을 추가할까요? (y/N): ").strip().lower()
    except EOFError:
        return False
    return ans in ("y", "yes")


def _skip_equipment_day_guard_from_env() -> bool:
    return os.getenv("DATA_PC_SKIP_EQUIPMENT_DAY_GUARD", "").strip().lower() in (
        "1",
        "true",
        "yes",
        "on",
    )


def update_from_dataframe(
    opju_path: str,
    df_data: Any,
    sample_name: str,
    save_in_place: bool = True,
    identity_key: IdentityKey | None = None,
    *,
    op: Any | None = None,
    skip_gate: bool = False,
    printer: PrintFn | None = None,
    log_fn: LogFn | None = None,
    job_runner: Callable[..., SampleJobResult] | None = None,
    column_guard_confirm: ColumnGuardConfirm | None = None,
    skip_equipment_day_guard: bool | None = None,
) -> OriginUpdateResult:
    """
    파이프라인 유일 진입 — O8 job 위임.

    시그니처: 촉매 `update_origin(opju_path, df_data, sample_name, …)` 와 동일 인자.
    """
    _print = printer if printer is not None else print
    skip_guard = (
        skip_equipment_day_guard
        if skip_equipment_day_guard is not None
        else _skip_equipment_day_guard_from_env()
    )
    confirm = column_guard_confirm
    if confirm is None and sys.stdin.isatty() and not skip_guard:
        confirm = lambda g: default_interactive_column_guard_confirm(g, printer=_print)

    ctx = build_context(
        opju_path,
        df_data,
        sample_name,
        identity_key=identity_key,
        save_in_place=save_in_place,
    )
    origin_log(f"job start opju={opju_path!r}", log_fn=log_fn)
    probe = probe_opju_path(opju_path) if not skip_gate else None
    runner = job_runner if job_runner is not None else run_sample_job
    job = runner(
        ctx,
        op=op,
        opju_probe=probe,
        skip_gate=skip_gate,
        column_guard_confirm=confirm,
        skip_equipment_day_guard=bool(skip_guard),
    )
    if not job.ok and any(w.code == "equipment_day_guard" for w in job.warnings):
        for w in job.warnings:
            if w.code == "equipment_day_guard":
                _print(f"\n[4단계] Origin 건너뜀 — 사용자 확인 필요")
                _print(w.detail)
                break
    else:
        print_stage4_ux(
            sample_name=sample_name,
            job=job,
            opju_path=opju_path,
            save_in_place=save_in_place,
            printer=_print,
        )
    origin_log(
        f"done sheets={job.updated_count} rows={job.row_count} ok={job.ok}",
        log_fn=log_fn,
    )
    return OriginUpdateResult(
        ok=job.ok,
        sheets_updated=job.updated_count,
        row_count=job.row_count,
        warnings=job.warnings,
        opju_path=opju_path,
        sample_name=sample_name,
    )


def facade_signature_param_names() -> tuple[str, ...]:
    """O9-F-01 — 공개 positional/kw-only 이름 (촉매 대응)."""
    sig = inspect.signature(update_from_dataframe)
    names: list[str] = []
    for name, param in sig.parameters.items():
        if param.kind in (
            inspect.Parameter.VAR_KEYWORD,
            inspect.Parameter.VAR_POSITIONAL,
        ):
            continue
        if name in ("op", "skip_gate", "printer", "log_fn", "job_runner"):
            continue
        names.append(name)
    return tuple(names)
