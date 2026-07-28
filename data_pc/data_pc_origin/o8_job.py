# -*- coding: utf-8
"""O8-J — sample job orchestration (O5→O6→O7)."""

from __future__ import annotations

from dataclasses import dataclass
from types import ModuleType
from typing import Any, Callable, List, Optional, Tuple

from data_pc_origin.o0_types import OriginWarning, ProbeResult
from data_pc_origin.o2_gate_chain import GateVerdict, evaluate_origin_gate
from data_pc_origin.o3_session import OriginSession
from data_pc_origin.o4_project import open_project_with_retry, save_project
from data_pc_origin.o8_save import resolve_save_path
from data_pc_origin.o5_match import (
    find_all_worksheets_for_keyword,
    report_missing,
    resolve_worksheets,
)
from data_pc_origin.o6_guard import ColumnGuardConfirm, OriginColumnGuardError
from data_pc_origin.o6_resolve import resolve_target_column
from data_pc_origin.o7_write import verify_written_column, write_column
from data_pc_origin.o8_context import SampleContext, dataframe_row_count

LtExecute = Callable[[str], None]
GateFn = Callable[..., GateVerdict]


@dataclass(frozen=True)
class SampleJobResult:
    updated_count: int
    row_count: int
    warnings: Tuple[OriginWarning, ...]
    col_idx: Optional[int]
    ok: bool
    saved_path: Optional[str] = None
    gate: Optional[GateVerdict] = None


def require_origin_ready(
    *,
    opju_probe: ProbeResult,
    pipeline_lock_path: str = ".origin_pipeline.lock",
    origin_lock_path: str = ".origin.lock",
    skip_origin: bool = False,
    gate_fn: GateFn = evaluate_origin_gate,
) -> GateVerdict:
    """O8-J-01 — O2 READY only."""
    return gate_fn(
        opju_probe=opju_probe,
        pipeline_lock_path=pipeline_lock_path,
        origin_lock_path=origin_lock_path,
        skip_origin=skip_origin,
    )


def run_writes(
    op: Any,
    ctx: SampleContext,
    *,
    lt_execute: LtExecute | None = None,
    column_guard_confirm: ColumnGuardConfirm | None = None,
    skip_equipment_day_guard: bool = False,
) -> Tuple[int, Optional[int], List[OriginWarning]]:
    """O8-J-04/05 — resolve col once · per-mapping write."""
    from data_pc_origin.agent_debug_log import agent_dbg

    hits, misses = resolve_worksheets(op, ctx.mapping, ctx.df)
    warnings = list(report_missing(misses))
    # region agent log
    agent_dbg(
        "H1",
        "o8_job.py:run_writes",
        "worksheet_resolve",
        {
            "opju": ctx.opju_path,
            "sample_head": (ctx.sample_name or "")[:100],
            "row_count": dataframe_row_count(ctx.df),
            "df_cols": list(getattr(ctx.df, "columns", [])),
            "hits": list(hits.keys()),
            "misses": misses,
            "mapping_size": len(ctx.mapping),
        },
    )
    # endregion
    col_idx: Optional[int] = None
    updated = 0
    cols = set(getattr(ctx.df, "columns", []))
    seen_dup_kw: set[str] = set()

    for df_col, origin_kw in ctx.mapping.items():
        if df_col not in cols:
            continue
        if hits.get(origin_kw) is None:
            continue
        # 복제 북(CO2conversion / CO2conversioA 등) 전부 — 첫 시트만 쓰면
        # Project Explorer 의 동명 폴더에 갭 이후 행이 비어 보일 수 있음.
        wks_list = find_all_worksheets_for_keyword(op, origin_kw)
        if not wks_list:
            continue
        if len(wks_list) > 1 and origin_kw not in seen_dup_kw:
            seen_dup_kw.add(origin_kw)
            warnings.append(
                OriginWarning(
                    "duplicate_origin_books",
                    f"{origin_kw}: 동명 Origin 북 {len(wks_list)}개 — 전부 갱신",
                )
            )
        for wks in wks_list:
            try:
                sheet_col = resolve_target_column(
                    wks,
                    ctx.sample_name,
                    ctx.identity_key,
                    lt_execute=lt_execute,
                    column_guard_confirm=column_guard_confirm,
                    skip_equipment_day_guard=skip_equipment_day_guard,
                )
            except OriginColumnGuardError as exc:
                # region agent log
                agent_dbg(
                    "H4",
                    "o8_job.py:run_writes",
                    "equipment_day_guard_block",
                    {"detail": str(exc.guard.question)[:200]},
                )
                # endregion
                warnings.append(
                    OriginWarning("equipment_day_guard", exc.guard.question)
                )
                return 0, None, warnings
            if col_idx is None:
                col_idx = sheet_col
            _col, prepared, _name = write_column(
                wks, sheet_col, ctx.df[df_col], ctx.sample_name
            )
            verify_err = verify_written_column(wks, sheet_col, prepared)
            if verify_err:
                wks_name = getattr(wks, "name", "?")
                warnings.append(
                    OriginWarning(
                        "origin_gap_write_verify",
                        f"{origin_kw}/{wks_name}: {verify_err}",
                    )
                )
            updated += 1
            # region agent log
            agent_dbg(
                "H1",
                "o8_job.py:run_writes",
                "wrote_metric",
                {
                    "df_col": df_col,
                    "origin_kw": origin_kw,
                    "col_idx": sheet_col,
                    "sheet_count": len(wks_list),
                    "verify_err": verify_err,
                },
            )
            # endregion

    # region agent log
    agent_dbg(
        "H1",
        "o8_job.py:run_writes",
        "run_writes_done",
        {
            "updated": updated,
            "col_idx": col_idx,
            "warnings": [w.code for w in warnings],
        },
    )
    # endregion
    return updated, col_idx, warnings


def run_sample_job(
    ctx: SampleContext,
    *,
    op: Any | None = None,
    opju_probe: ProbeResult | None = None,
    skip_gate: bool = False,
    session: OriginSession | None = None,
    gate_fn: GateFn = evaluate_origin_gate,
    lt_execute: LtExecute | None = None,
    column_guard_confirm: ColumnGuardConfirm | None = None,
    skip_equipment_day_guard: bool = False,
) -> SampleJobResult:
    """Dry/mock or live — session finally exit (O8-J-09)."""
    probe = opju_probe or ProbeResult(ok=True, detail="mock")
    if not skip_gate:
        verdict = require_origin_ready(opju_probe=probe, skip_origin=False, gate_fn=gate_fn)
        if verdict.code != "ready":
            return SampleJobResult(
                updated_count=0,
                row_count=dataframe_row_count(ctx.df),
                warnings=(),
                col_idx=None,
                ok=False,
                gate=verdict,
            )

    n_rows = dataframe_row_count(ctx.df)

    if op is not None:
        try:
            return _run_with_op(
                op,
                ctx,
                n_rows=n_rows,
                lt_execute=lt_execute,
                column_guard_confirm=column_guard_confirm,
                skip_equipment_day_guard=skip_equipment_day_guard,
            )
        finally:
            exit_fn = getattr(op, "exit", None)
            if callable(exit_fn):
                exit_fn()

    sess = session or OriginSession()
    with sess as live_op:
        return _run_with_op(
            live_op,
            ctx,
            n_rows=n_rows,
            lt_execute=lt_execute,
            column_guard_confirm=column_guard_confirm,
            skip_equipment_day_guard=skip_equipment_day_guard,
        )


def _run_with_op(
    op: Any,
    ctx: SampleContext,
    *,
    n_rows: int,
    lt_execute: LtExecute | None,
    column_guard_confirm: ColumnGuardConfirm | None = None,
    skip_equipment_day_guard: bool = False,
) -> SampleJobResult:
    open_project_with_retry(op, ctx.opju_path)  # type: ignore[arg-type]
    updated, col_idx, warnings = run_writes(
        op,
        ctx,
        lt_execute=lt_execute,
        column_guard_confirm=column_guard_confirm,
        skip_equipment_day_guard=skip_equipment_day_guard,
    )
    saved_path: Optional[str] = None
    if updated > 0:
        saved_path = resolve_save_path(ctx.opju_path, ctx.save_in_place)
        save_project(op, saved_path)  # type: ignore[arg-type]
    ok = updated > 0
    return SampleJobResult(
        updated_count=updated,
        row_count=n_rows,
        warnings=tuple(warnings),
        col_idx=col_idx,
        ok=ok,
        saved_path=saved_path,
    )
