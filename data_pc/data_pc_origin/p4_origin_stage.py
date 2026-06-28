# -*- coding: utf-8
"""P4 — Stage4 Origin 1회 실행 (pipeline_bridge 위임, mock 주입)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Mapping, Optional

from data_pc_origin.o9_facade import OriginUpdateResult
from data_pc_origin.p0_types import OriginJobPayload, WorkflowOptions
from data_pc_origin.p3_skip import (
    STAGE4_SKIP_MSG,
    should_execute_stage4,
    stage4_skip_reason,
)

OriginRunner = Callable[[OriginJobPayload], OriginUpdateResult]


@dataclass(frozen=True)
class Stage4Result:
    """4단계 실행·skip 결과 — P5 workflow 입력."""

    skipped: bool
    ok: bool
    origin: OriginUpdateResult | None
    skip_reason: str


def bridge_kwargs_from_payload(payload: OriginJobPayload) -> dict[str, object]:
    """`run_origin_update` 인자 — 촉매 L1696–1701 대응."""
    return {
        "opju_path": payload.opju_path,
        "df_data": payload.df,
        "sample_name": payload.sample_name,
        "save_in_place": payload.save_in_place,
        "identity_key": payload.identity_key,
    }


def default_origin_runner(payload: OriginJobPayload) -> OriginUpdateResult:
    from data_pc_origin.pipeline_bridge import run_origin_update

    return run_origin_update(**bridge_kwargs_from_payload(payload))  # type: ignore[arg-type]


def run_stage4_origin(
    payload: OriginJobPayload,
    *,
    runner: OriginRunner | None = None,
) -> Stage4Result:
    """P3 skip 이후 — O9 1회 (mock runner 또는 live bridge)."""
    execute = runner or default_origin_runner
    origin = execute(payload)
    return Stage4Result(
        skipped=False,
        ok=origin.ok,
        origin=origin,
        skip_reason="",
    )


def maybe_run_stage4(
    payload: OriginJobPayload,
    *,
    options: WorkflowOptions | None = None,
    explicit: Optional[bool] = None,
    environ: Optional[Mapping[str, str]] = None,
    runner: OriginRunner | None = None,
) -> Stage4Result:
    """P3 skip + P4 origin — workflow 4단계 진입점."""
    if not should_execute_stage4(
        options=options, explicit=explicit, environ=environ
    ):
        if options is not None and options.skip_stage4:
            reason = STAGE4_SKIP_MSG
        else:
            reason = stage4_skip_reason(explicit=explicit, environ=environ)
        return Stage4Result(
            skipped=True,
            ok=True,
            origin=None,
            skip_reason=reason,
        )
    return run_stage4_origin(payload, runner=runner)
