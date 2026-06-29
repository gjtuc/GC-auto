# -*- coding: utf-8 -*-
"""O6-F — worksheet column lookup (촉매 L1658–1666)."""

from __future__ import annotations

from typing import Any, Optional, Tuple

from data_pc_origin.o0_comments import comment_matches_identity
from data_pc_origin.o6_scan import iter_col_comments

IdentityKey = Tuple[str, str]


def find_column_exact_comment(wks: Any, sample_name: str) -> Optional[int]:
    """Comments strip == sample_name — 첫 매칭 열 (촉매 exact pass)."""
    for i, comment in iter_col_comments(wks):
        if comment and comment.strip() == sample_name:
            return i
    return None


def find_column_by_identity(wks: Any, identity_key: IdentityKey | None) -> Optional[int]:
    """O0-C-02 — 재전송 identity 일치 열."""
    if not identity_key:
        return None
    for i, comment in iter_col_comments(wks):
        if comment_matches_identity(comment, identity_key):
            return i
    return None
