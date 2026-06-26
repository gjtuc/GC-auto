# -*- coding: utf-8
"""O8-J — sample job orchestration (O5→O6→O7)."""

from __future__ import annotations

from dataclasses import dataclass
from types import ModuleType
from typing import Any, Callable, List, Optional, Tuple

from data_pc_origin.o0_types import OriginWarning, ProbeResult
from data_pc_origin.o2_gate_chain import GateVerdict, evaluate_origin_gate
from data_pc_origin.o3_session import OriginSession
from data_pc_origin.o4_project import open_project, save_project
from data_pc_origin.o8_save import resolve_save_path
from data_pc_origin.o5_match import report_missing, resolve_worksheets
from data_pc_origin.o6_resolve import resolve_target_column
from data_pc_origin.o7_write import write_column
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
) -> Tuple[int, Optional[int], List[OriginWarning]]:
    """O8-J-04/05 — resolve col once · per-mapping write."""
    hits, misses = resolve_worksheets(op, ctx.mapping, ctx.df)
    warnings = list(report_missing(misses))
    col_idx: Optional[int] = None
    updated = 0
    cols = set(getattr(ctx.df, "columns", []))

    for df_col, origin_kw in ctx.mapping.items():
        if df_col not in cols:
            continue
        wks = hits.get(origin_kw)
        if wks is None:
            continue
        if col_idx is None:
            col_idx = resolve_target_column(
                wks,
                ctx.sample_name,
                ctx.identity_key,
                lt_execute=lt_execute,
            )
        write_column(wks, col_idx, ctx.df[df_col], ctx.sample_name)
        updated += 1

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
            return _run_with_op(op, ctx, n_rows=n_rows, lt_execute=lt_execute)
        finally:
            exit_fn = getattr(op, "exit", None)
            if callable(exit_fn):
                exit_fn()

    sess = session or OriginSession()
    with sess as live_op:
        return _run_with_op(live_op, ctx, n_rows=n_rows, lt_execute=lt_execute)


def _run_with_op(
    op: Any,
    ctx: SampleContext,
    *,
    n_rows: int,
    lt_execute: LtExecute | None,
) -> SampleJobResult:
    open_project(op, ctx.opju_path)  # type: ignore[arg-type]
    updated, col_idx, warnings = run_writes(op, ctx, lt_execute=lt_execute)
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
