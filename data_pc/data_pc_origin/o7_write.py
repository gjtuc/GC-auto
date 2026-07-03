# -*- coding: utf-8 -*-
"""O7-W — worksheet column write (촉매 L1720)."""

from __future__ import annotations

from typing import Any, Iterable, List, Mapping, Optional, Tuple

from data_pc_origin.o0_mapping import DEFAULT_ORIGIN_MAPPING
from data_pc_origin.o0_series import GapPolicy
from data_pc_origin.o7_policy import prepare_column_list, select_gap_policy

WriteRecord = Tuple[int, List[Any], str]


def write_column(
    wks: Any,
    col_idx: int,
    values: Iterable[Any],
    sample_name: str,
    *,
    gap_policy: GapPolicy | None = None,
    environ: Optional[Mapping[str, str]] = None,
) -> WriteRecord:
    """``wks.from_list(col, prepared, comments=sample_name)`` — 열 통째 1회 쓰기(start=0).

    갭 정책으로 빈 문자열이 들어간 행은 Origin에서 ``--`` 로 보일 수 있음.
    행 단위 희소 패치 부작용은 ``live_patch_row109`` 모듈 docstring 참고.
    """
    prepared = prepare_column_list(values, gap_policy=gap_policy, environ=environ)
    from_list = getattr(wks, "from_list", None)
    if from_list is None:
        raise AttributeError("wks.from_list required")
    from_list(col_idx, prepared, comments=sample_name)
    return col_idx, prepared, sample_name


def write_h2_column(
    wks: Any,
    col_idx: int,
    h2_values: Iterable[Any],
    sample_name: str,
    *,
    gap_policy: GapPolicy | None = None,
) -> WriteRecord:
    """O7-W-02 — H2 Yield 열 스모크 (107행 갭 포함)."""
    return write_column(wks, col_idx, h2_values, sample_name, gap_policy=gap_policy)


def write_mapping_columns(
    wks: Any,
    col_idx: int,
    df: Any,
    mapping: Mapping[str, str],
    sample_name: str,
    *,
    gap_policy: GapPolicy | None = None,
) -> List[WriteRecord]:
    """mapping 순회 — df에 있는 열만 write (O7-W-03)."""
    cols = set(getattr(df, "columns", []))
    records: List[WriteRecord] = []
    for df_col in mapping:
        if df_col not in cols:
            continue
        records.append(
            write_column(
                wks,
                col_idx,
                df[df_col],
                sample_name,
                gap_policy=gap_policy,
            )
        )
    return records
