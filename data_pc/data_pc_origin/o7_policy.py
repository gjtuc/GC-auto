# -*- coding: utf-8 -*-
"""O7-P — gap policy selection (O0-S 위임)."""

from __future__ import annotations

import os
from typing import Mapping

from data_pc_origin.o0_series import GapPolicy

GAP_POLICY_ENV = "DATA_PC_ORIGIN_GAP_POLICY"

_ENV_TO_POLICY: dict[str, GapPolicy] = {
    "empty": GapPolicy.AS_EMPTY,
    "nan": GapPolicy.AS_NAN,
    "skip": GapPolicy.SKIP_ROWS,
}


def read_gap_policy_env(*, environ: Mapping[str, str] | None = None) -> str:
    env = environ if environ is not None else os.environ
    return (env.get(GAP_POLICY_ENV) or "").strip().lower()


def select_gap_policy(*, environ: Mapping[str, str] | None = None) -> GapPolicy:
    """기본 AS_EMPTY — env `DATA_PC_ORIGIN_GAP_POLICY` 로 override."""
    raw = read_gap_policy_env(environ=environ)
    if not raw:
        return GapPolicy.AS_EMPTY
    return _ENV_TO_POLICY.get(raw, GapPolicy.AS_EMPTY)


def prepare_column_list(
    values,
    *,
    gap_policy: GapPolicy | None = None,
    environ: Mapping[str, str] | None = None,
) -> list:
    """O0-S-05 — df 열 → from_list 인자."""
    from data_pc_origin.o0_series import column_to_origin_list

    policy = gap_policy if gap_policy is not None else select_gap_policy(environ=environ)
    return column_to_origin_list(values, gap_policy=policy)
