# -*- coding: utf-8 -*-
"""O7-W — worksheet column write (촉매 L1720)."""

from __future__ import annotations

import math
from typing import Any, Iterable, List, Mapping, Optional, Sequence, Tuple

from data_pc_origin.o0_mapping import DEFAULT_ORIGIN_MAPPING
from data_pc_origin.o0_series import GapPolicy
from data_pc_origin.o7_policy import prepare_column_list, select_gap_policy

WriteRecord = Tuple[int, List[Any], str]


def _is_gap_slot(value: Any) -> bool:
    if value is None or value == "":
        return True
    try:
        return isinstance(value, float) and math.isnan(value)
    except (TypeError, ValueError):
        return False


def _value_segments(prepared: Sequence[Any]) -> List[Tuple[int, List[Any]]]:
    """연속 숫자 구간 → (Origin 1-based start row, values). 갭 슬롯은 건너뜀."""
    segments: List[Tuple[int, List[Any]]] = []
    i = 0
    n = len(prepared)
    while i < n:
        if _is_gap_slot(prepared[i]):
            i += 1
            continue
        j = i + 1
        while j < n and not _is_gap_slot(prepared[j]):
            j += 1
        segments.append((i + 1, list(prepared[i:j])))
        i = j
    return segments


def last_non_gap_index(prepared: Sequence[Any]) -> int | None:
    """0-based — 갭이 아닌 마지막 슬롯. 전부 갭이면 None."""
    for i in range(len(prepared) - 1, -1, -1):
        if not _is_gap_slot(prepared[i]):
            return i
    return None


def verify_written_column(
    wks: Any,
    col_idx: int,
    prepared: Sequence[Any],
) -> str | None:
    """쓰기 후 ``to_list`` 로 갭 이후 값이 살아 있는지 확인.

    Returns:
        None = 통과 또는 검증 불가(to_list 없음) · str = 실패 사유
    """
    to_list = getattr(wks, "to_list", None)
    if not callable(to_list):
        return None
    last_i = last_non_gap_index(prepared)
    if last_i is None:
        return None
    try:
        got = list(to_list(col_idx))
    except Exception as exc:  # noqa: BLE001 — live COM 다양
        return f"to_list 실패: {exc}"
    if len(got) <= last_i:
        return f"행 수 부족: got={len(got)} need_idx={last_i}"
    if _is_gap_slot(got[last_i]):
        return f"갭 이후 값 미반영: row={last_i + 1} empty"
    return None


def write_column(
    wks: Any,
    col_idx: int,
    values: Iterable[Any],
    sample_name: str,
    *,
    gap_policy: GapPolicy | None = None,
    environ: Optional[Mapping[str, str]] = None,
) -> WriteRecord:
    """``wks.from_list`` — 열 쓰기.

    1) 전체 ``prepared`` 1회 기록 (Comments·갭 슬롯 유지)
    2) 갭 **이후** 숫자 구간은 ``start=`` 로 한 번 더 기록 — 일부 Origin
       시트에서 mid-column ``''`` 뒤 값이 잘리는 경우 보강
    """
    prepared = prepare_column_list(values, gap_policy=gap_policy, environ=environ)
    from_list = getattr(wks, "from_list", None)
    if from_list is None:
        raise AttributeError("wks.from_list required")
    from_list(col_idx, prepared, comments=sample_name)

    segments = _value_segments(prepared)
    gap_passed = False
    slot_i = 0
    for start_row, seg_vals in segments:
        # 이 구간 앞에 갭이 있었으면 start= 보강 쓰기
        while slot_i < start_row - 1:
            if _is_gap_slot(prepared[slot_i]):
                gap_passed = True
            slot_i += 1
        slot_i = start_row - 1 + len(seg_vals)
        if not gap_passed:
            continue
        try:
            from_list(col_idx, seg_vals, comments=sample_name, start=start_row)
        except TypeError:
            break
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
