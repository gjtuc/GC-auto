# -*- coding: utf-8
"""P1-P — Stage2 산출물 + 메타 → OriginJobPayload (촉매·originpro 금지)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Tuple

from data_pc_origin.o0_mapping import mapping_for_df
from data_pc_origin.p0_types import (
    IdentityKey,
    OriginJobPayload,
    Stage2Artifacts,
    WorkflowMode,
    build_origin_payload,
)

PAYLOAD_SAMPLE_NAME_MIN = 1


class PayloadValidationError(ValueError):
    """Stage2 → payload 조립 오류."""


@dataclass(frozen=True)
class Stage2Metadata:
    """촉매 L2210–2213 — 2단계 후 Origin용 메타."""

    sample_name: str
    identity_key: IdentityKey
    saved_excel: str


def validate_sample_name(name: str) -> str:
    text = (name or "").strip()
    if len(text) < PAYLOAD_SAMPLE_NAME_MIN:
        raise PayloadValidationError("sample_name empty")
    return text


def validate_identity_key(key: IdentityKey) -> IdentityKey:
    if not isinstance(key, tuple) or len(key) != 2:
        raise PayloadValidationError("identity_key must be 2-tuple")
    date, sample_key = key
    if not str(date).strip() or not str(sample_key).strip():
        raise PayloadValidationError("identity_key parts empty")
    return (str(date).strip(), str(sample_key).strip())


def mapping_subset_for_df(df: Any) -> Tuple[Dict[str, str], List[str]]:
    """O0-M subset — df 열 ∩ DEFAULT_ORIGIN_MAPPING."""
    cols = set(getattr(df, "columns", []))
    return mapping_for_df(cols)


def skipped_mapping_columns(df: Any) -> List[str]:
    """df에 없는 DEFAULT_ORIGIN_MAPPING 열."""
    _subset, skipped = mapping_subset_for_df(df)
    return list(skipped)


def assemble_stage2_metadata(
    *,
    sample_name: str,
    identity_key: IdentityKey,
    saved_excel: str,
) -> Stage2Metadata:
    return Stage2Metadata(
        sample_name=validate_sample_name(sample_name),
        identity_key=validate_identity_key(identity_key),
        saved_excel=(saved_excel or "").strip(),
    )


def build_payload_from_stage2(
    artifacts: Stage2Artifacts,
    metadata: Stage2Metadata,
    *,
    opju_path: str,
    mode: WorkflowMode,
) -> OriginJobPayload:
    """P1 → P0 `build_origin_payload` — 4단계 O9 인자."""
    return build_origin_payload(
        artifacts,
        opju_path=(opju_path or "").strip(),
        sample_name=metadata.sample_name,
        identity_key=metadata.identity_key,
        mode=mode,
    )


def payload_mapping_col_count(df: Any) -> int:
    subset, _ = mapping_subset_for_df(df)
    return len(subset)
