# -*- coding: utf-8 -*-
"""촉매 반응 계산.py ↔ O0 identity/Comments 단일 소스 연결.

G: 폴더 중복 판별·Origin 열 매칭(legacy 경로)이 data_pc_origin.o0_* 와 동일 규칙을 쓰도록 위임.
실행 경로(update_origin)는 pipeline_bridge → O9 이지만, 촉매 내부 헬퍼도 O0 와 드리프트 방지.
"""

from __future__ import annotations

from typing import Optional, Tuple

from data_pc_origin.o0_comments import comment_matches_identity, parse_comment_date
from data_pc_origin.o0_identity import identity_match_tokens

IdentityKey = Tuple[str, str]


def catalyst_identity_tokens(sample_key: str) -> set[str]:
    """KCH sample_key → G:/Origin 매칭 토큰 (O0-I-01·O0-I-03)."""
    return identity_match_tokens(sample_key)


def catalyst_comment_matches_identity(
    comment: str | None,
    identity_key: IdentityKey | None,
) -> bool:
    """Origin Comments ↔ (날짜, 시료) 동일 실험 여부 (O0-C, 장비 접미사 strip 포함)."""
    return comment_matches_identity(comment, identity_key)


def catalyst_comment_sort_date(text: str | None) -> Optional[str]:
    """Comments/시료명 선두 YYYYMMDD — 워크시트 열 날짜순 정렬용 (O0-C)."""
    return parse_comment_date(text)
