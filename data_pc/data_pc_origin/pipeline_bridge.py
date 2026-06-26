# -*- coding: utf-8 -*-
"""Phase 8 — 촉매 반응 계산.py ↔ data_pc_origin 연결."""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any, Tuple

from data_pc_origin.o9_facade import OriginUpdateResult, update_from_dataframe

IdentityKey = Tuple[str, str] | None

_BRIDGE_ROOT = Path(__file__).resolve().parent.parent


def ensure_import_path() -> Path:
    """`.cursor` 루트를 sys.path 에 보장."""
    root = str(_BRIDGE_ROOT)
    if root not in sys.path:
        sys.path.insert(0, root)
    return _BRIDGE_ROOT


def run_origin_update(
    opju_path: str,
    df_data: Any,
    sample_name: str,
    save_in_place: bool = True,
    identity_key: IdentityKey = None,
) -> OriginUpdateResult:
    """
    촉매 `update_origin()` 대체 진입 — O9 facade 위임.

    `DATA_PC_SKIP_ORIGIN=1` 은 호출 전(촉매 3~4단계)에서 처리; 여기서는 실행만.
    """
    ensure_import_path()
    return update_from_dataframe(
        opju_path,
        df_data,
        sample_name,
        save_in_place=save_in_place,
        identity_key=identity_key,
    )
