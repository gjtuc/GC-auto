"""
data_pc_origin — Origin .opju 연동 (파이프라인과 분리)

레이어 (아래만 의존):

  O0 pure     — originpro 없음 (키·Comments·Series·Mapping)
  O1 probes   — (잠금) 읽기만
  O2 gates    — (잠금)
  O3 session  — (잠금)
  ...

검증: python -m data_pc_origin.verify --o0

[O0] 2026-06-26 — verify --o0 PASS (다음 층 O1 은 사용자 승인 후)
"""

from data_pc_origin.o0_comments import comment_matches_identity, parse_comment_date
from data_pc_origin.o0_identity import identity_match_tokens
from data_pc_origin.o0_keys import normalize_origin_key
from data_pc_origin.o0_mapping import (
    DEFAULT_ORIGIN_MAPPING,
    MappingValidationError,
    validate_mapping,
)
from data_pc_origin.o0_series import GapPolicy, column_to_origin_list

from data_pc_origin.o9_facade import OriginUpdateResult, update_from_dataframe
from data_pc_origin.pipeline_bridge import run_origin_update

__all__ = [
    "DEFAULT_ORIGIN_MAPPING",
    "GapPolicy",
    "MappingValidationError",
    "OriginUpdateResult",
    "column_to_origin_list",
    "comment_matches_identity",
    "identity_match_tokens",
    "normalize_origin_key",
    "parse_comment_date",
    "run_origin_update",
    "update_from_dataframe",
    "validate_mapping",
]
