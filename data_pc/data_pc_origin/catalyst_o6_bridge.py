# -*- coding: utf-8 -*-
"""촉매 반응 계산.py ↔ O6 column resolve 단일 소스 연결.

legacy `_find_worksheet_column_for_sample` → `o6_resolve.resolve_target_column`
(exact Comments → identity 재전송 → 날짜순 삽입). 운영 경로는 O9 facade 가 동일 O6 를 사용.
"""

from __future__ import annotations

from typing import Any, Optional, Tuple

from data_pc_origin.o6_resolve import resolve_target_column

IdentityKey = Tuple[str, str]


def catalyst_resolve_target_column(
    wks: Any,
    sample_name: str,
    identity_key: IdentityKey | None = None,
    *,
    skip_equipment_day_guard: bool = True,
) -> int:
    """워크시트 대상 열 — O6-F/R 위임. legacy 는 장비·날짜 가드 생략(구 동작 유지)."""
    lt_execute = None
    try:
        from originpro.config import po

        lt_execute = po.LT_execute
    except ImportError:
        # originpro 미설치 환경(단위 테스트) — insert 시 lt_execute 주입 필요
        pass
    return resolve_target_column(
        wks,
        sample_name,
        identity_key,
        lt_execute=lt_execute,
        skip_equipment_day_guard=skip_equipment_day_guard,
    )
