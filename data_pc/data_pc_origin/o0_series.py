# -*- coding: utf-8 -*-
"""O0 — DataFrame 열 → Origin from_list 입력 (originpro 불필요)."""

from __future__ import annotations

import math
from enum import Enum
from typing import Any, Iterable, List

import pandas as pd


class GapPolicy(str, Enum):
    """GC3 갭(NaN) 행을 Origin 열에 넣는 정책 — O7에서 사용."""

    AS_EMPTY = "empty"  # NaN → 빈 셀 (시간축 유지, 그래프 끊김)
    AS_NAN = "nan"  # NaN 그대로 (originpro 기본에 가깝게)
    SKIP_ROWS = "skip"  # NaN 행 제외 — Cycle 번호 어긋남, 비권장


def _is_missing(value: Any) -> bool:
    if value is None:
        return True
    try:
        return bool(pd.isna(value))
    except (TypeError, ValueError):
        return False


def column_to_origin_list(
    values: Iterable[Any],
    *,
    gap_policy: GapPolicy = GapPolicy.AS_EMPTY,
) -> List[Any]:
    """
    계산완료 xlsx 열 → originpro Worksheet.from_list 인자.

    gap_policy:
      AS_EMPTY — 갭 슬롯은 '' (행 수 = len(df), Origin 시간축 정렬)
      AS_NAN   — float('nan') 유지
      SKIP_ROWS — NaN 행 생략 (행 수 감소)
    """
    out: List[Any] = []
    for value in values:
        if _is_missing(value):
            if gap_policy == GapPolicy.SKIP_ROWS:
                continue
            if gap_policy == GapPolicy.AS_NAN:
                out.append(math.nan)
            else:
                out.append("")
        else:
            out.append(value)
    return out
