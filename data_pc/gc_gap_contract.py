# -*- coding: utf-8 -*-
"""
GC3 장비 PC → 차헌 PC 엑셀 중단(갭) 행 계약.

gc_chem32.gap_marker_cycle() 가 FID/TCD 시트에 삽입하는 표시 행 형식과 동일.
차헌 PC는 Chem32 원본 경로에 접근하지 않고, 메일 첨부 KCH xlsx 만 읽는다.

표시 행 (헤더 # Time … 바로 다음 1행):
  #        = "중단"
  Time     = "약 {N}사이클 미수집"   (N = floor(공백초 / 중앙 주입간격))
  Area     = "공백 {한글 기간}"
  Height   = "잔여 {한글 기간} 버림"
  Width    = 공백 직전 마지막 주입 시각
  Area%    = 공백 직후 첫 주입 시각
  Symmetry = "GC_GAP:N={N}"  (머신 파싱용, 한글 Time 과 동일 N)
  일반 주입 피크 Symmetry = Injection Date (YYYY-MM-DD HH:MM:SS) — 갭 행만 GC_GAP

차헌 PC parse_gc_sheet: ``#`` 헤더 바로 다음 ``중단`` 행을 만나면
  마지막 실측 Cycle 이후 N칸을 gap_cycles 에 넣고, 다음 실측은 last+N+1 로 이어 붙임.
  process_excel(GC3) 가 gap_cycles 행을 NaN 처리 → Origin 열 정렬.

Area 에 ``· 002F0209.D→001F0101.D`` 등 폴더명이 붙어도 N 파싱에는 영향 없음.
"""

from __future__ import annotations

import re
from typing import Any, Optional

GAP_MARKER_FIRST_COL = "중단"
GAP_TIME_RE = re.compile(r"약\s*(\d+)\s*사이클")
GAP_SYMMETRY_RE = re.compile(r"GC_GAP:N=(\d+)")


def is_cycle_header_row(row: Any) -> bool:
    """Chem32/GC2 공통 — # 열 또는 Time 이 문자열인 헤더 행."""
    first = str(row.iloc[0]).strip()
    if first == "#" or first.startswith("#"):
        return True
    return str(row.get("Time", "")).isalpha()


def parse_gap_missing_cycles(row: Any) -> Optional[int]:
    """중단 표시 행이면 미수집 사이클 수 N, 아니면 None."""
    first = str(row.iloc[0]).strip()
    if first != GAP_MARKER_FIRST_COL:
        return None
    time_val = str(row.get("Time", ""))
    match = GAP_TIME_RE.search(time_val)
    if match:
        return int(match.group(1))
    sym = str(row.get("Symmetry", ""))
    match_sym = GAP_SYMMETRY_RE.search(sym)
    if match_sym:
        return int(match_sym.group(1))
    return None
