# -*- coding: utf-8 -*-
"""O6-R — target column resolution (촉매 _find_worksheet_column_for_sample)."""

from __future__ import annotations

from typing import Any, Optional, Tuple

from data_pc_origin.o6_find import find_column_by_identity, find_column_exact_comment
from data_pc_origin.o6_insert import LtExecute, insert_column_if_needed
from data_pc_origin.o6_plan import plan_insert_index, sample_sort_date
from data_pc_origin.o6_scan import dated_columns

IdentityKey = Tuple[str, str]


def resolve_target_column(
    wks: Any,
    sample_name: str,
    identity_key: IdentityKey | None = None,
    *,
    lt_execute: LtExecute | None = None,
) -> int:
    """exact → identity → dated insert (촉매 L1651–1683)."""
    col = find_column_exact_comment(wks, sample_name)
    if col is not None:
        return col

    if identity_key:
        col = find_column_by_identity(wks, identity_key)
        if col is not None:
            return col

    dated = dated_columns(wks)
    new_date = sample_sort_date(sample_name)
    insert_at = plan_insert_index(dated, new_date)
    insert_column_if_needed(wks, insert_at, lt_execute=lt_execute)
    return insert_at
