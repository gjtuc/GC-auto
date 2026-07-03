# -*- coding: utf-8
"""P3-S — 4단계 Origin skip (O2 env 위임, 촉매 L368–375)."""

from __future__ import annotations

from typing import Mapping, Optional

from data_pc_origin.o2_env import SKIP_ORIGIN_ENV, skip_origin_active
from data_pc_origin.p0_types import WorkflowOptions

STAGE4_SKIP_MSG = "[4단계] Origin 건너뜀 — --no-origin / DATA_PC_SKIP_ORIGIN"


def resolve_skip_stage4(
    *,
    explicit: Optional[bool] = None,
    environ: Optional[Mapping[str, str]] = None,
) -> bool:
    """
    True → 4단계 생략.

    `explicit is not None` 이면 env 무시 (촉매 `--no-origin` / CLI).
    """
    if explicit is not None:
        return bool(explicit)
    return skip_origin_active(environ=environ)


def should_execute_stage4(
    *,
    options: WorkflowOptions | None = None,
    explicit: Optional[bool] = None,
    environ: Optional[Mapping[str, str]] = None,
) -> bool:
    """Origin COM 실행 여부 — options.skip_stage4 또는 env/explicit."""
    if options is not None and options.skip_stage4:
        return False
    return not resolve_skip_stage4(explicit=explicit, environ=environ)


def stage4_skip_reason(
    *,
    explicit: Optional[bool] = None,
    environ: Optional[Mapping[str, str]] = None,
) -> str:
    """촉매 L2238/L2251 출력용."""
    if not resolve_skip_stage4(explicit=explicit, environ=environ):
        return ""
    return STAGE4_SKIP_MSG


def skip_env_key() -> str:
    return SKIP_ORIGIN_ENV
