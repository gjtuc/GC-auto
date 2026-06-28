# -*- coding: utf-8
"""P0-T — workflow types (촉매·originpro 금지)."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any, Tuple

IdentityKey = Tuple[str, str]


class WorkflowMode(str, Enum):
    """촉매 `run_workflow_for_file` 분기."""

    OPJU_ONLY = "opju_only"
    CALC_ONLY = "calc_only"
    FULL_ARCHIVE = "full_archive"


@dataclass(frozen=True)
class WorkflowOptions:
    opju_path: str = ""
    auto_archive: bool = True
    skip_stage4: bool = False


@dataclass(frozen=True)
class Stage2Artifacts:
    df: Any
    saved_excel: str
    warnings: Tuple[str, ...] = ()
    feed_source_desc: str = ""


@dataclass(frozen=True)
class OriginJobPayload:
    opju_path: str
    sample_name: str
    identity_key: IdentityKey
    save_in_place: bool
    df: Any


def build_origin_payload(
    artifacts: Stage2Artifacts,
    *,
    opju_path: str,
    sample_name: str,
    identity_key: IdentityKey,
    mode: WorkflowMode,
) -> OriginJobPayload:
    """촉매 L2240/L2255 — OPJU_ONLY 는 save_in_place=False."""
    save_in_place = mode != WorkflowMode.OPJU_ONLY
    return OriginJobPayload(
        opju_path=opju_path,
        sample_name=sample_name,
        identity_key=identity_key,
        save_in_place=save_in_place,
        df=artifacts.df,
    )


def payload_row_count(payload: OriginJobPayload) -> int:
    from data_pc_origin.o8_context import dataframe_row_count

    return dataframe_row_count(payload.df)
