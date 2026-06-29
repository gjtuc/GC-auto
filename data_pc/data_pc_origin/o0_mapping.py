# -*- coding: utf-8 -*-
"""O0 — 엑셀 열 → Origin 워크시트 키워드 매핑 (originpro 불필요)."""

from __future__ import annotations

from typing import Dict, Mapping

from data_pc_origin.o0_keys import normalize_origin_key

# 촉매 반응 계산.py ORIGIN_MAPPING 과 동일 (단일 진실 공급원 — 추후 O9에서만 import)
DEFAULT_ORIGIN_MAPPING: Dict[str, str] = {
    "C2H6 Conversion (%)": "C2H6 conversion",
    "CH4 Conversion (%)": "CH4 conversion",
    "CO2 Conversion (%)": "CO2 conversion",
    "H2 Yield (%)": "H2 yield",
    "CO Yield (%)": "CO yield",
    "CH4 (%)": "CH4",
    "C2H4 (%)": "C2H4",
    "C2H6 (%)": "C2H6",
}


class MappingValidationError(ValueError):
    """ORIGIN_MAPPING 구조 오류."""


def validate_mapping(mapping: Mapping[str, str] | None = None) -> Dict[str, str]:
    """매핑 dict 검증 후 복사본 반환."""
    src = dict(mapping if mapping is not None else DEFAULT_ORIGIN_MAPPING)
    if not src:
        raise MappingValidationError("mapping 이 비어 있습니다")

    seen_norm: Dict[str, str] = {}
    for df_col, origin_kw in src.items():
        if not str(df_col).strip():
            raise MappingValidationError("df 열 이름이 비어 있습니다")
        if not str(origin_kw).strip():
            raise MappingValidationError(f"Origin 키워드가 비어 있습니다: {df_col!r}")
        norm = normalize_origin_key(origin_kw)
        if norm in seen_norm and seen_norm[norm] != df_col:
            raise MappingValidationError(
                f"정규화 후 중복 Origin 키워드: {origin_kw!r} vs {seen_norm[norm]!r}"
            )
        seen_norm[norm] = df_col

    return src


def mapping_for_df(
    df_columns: set[str] | frozenset[str],
    mapping: Mapping[str, str] | None = None,
) -> tuple[Dict[str, str], list[str]]:
    """df에 있는 열만 subset; 없는 열은 skipped 목록."""
    src = validate_mapping(mapping)
    skipped = [col for col in src if col not in df_columns]
    subset = {col: src[col] for col in src if col in df_columns}
    return subset, skipped
