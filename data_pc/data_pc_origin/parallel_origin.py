# -*- coding: utf-8 -*-
"""병렬 동일반응(다른 장비·다른 시료) — Origin peer 묶음 키.

2시간 창은 **반응기 가동 시각이 아니라 수신 메일 시각** 기준.
같은 반응(DRE 농도·온도)인데 다른 시료 메일이 2시간 이내에 도착하면 peer.
"""

from __future__ import annotations

import re


def _reaction_body_for_key(folder_name: str) -> str:
    """parallel reaction 키용 — yyMMdd 중복·@ 누락 보정."""
    body = folder_sample_body(folder_name)
    body = re.sub(r"^\d{6}\s+", "", body)
    body = re.sub(
        r"^(dre|drm|drme)\(([^)]+)\)(\d{3,4})c?\b",
        r"\1(\2)@\3",
        body,
        flags=re.I,
    )
    return body


def folder_sample_body(folder_name: str) -> str:
    """날짜·Windows (n) 접미사 제외 — 시료 비교용."""
    key = re.sub(r"^\d{8}\s+", "", (folder_name or "").strip())
    key = re.sub(r"\s+\(\d+\)\s*$", "", key)
    return re.sub(r"\s+", " ", key).lower()


def folder_parallel_reaction_key(folder_name: str) -> tuple[str, str, str] | None:
    """
    반응·농도·온도 (시료 제외).

    예) 20260701 DRE(1.5%)@600C Ni5-Al2O3 → ('DRE', '1.5', '600')
    """
    body = _reaction_body_for_key(folder_name)
    m = re.match(r"^(dre|drm)\(([^)]+)\)@(\d+)c?\s", body, re.I)
    if m:
        return (m.group(1).upper(), m.group(2).rstrip("%").strip(), m.group(3))
    m = re.match(r"^(drme)\(([^)]+)\)\s", body, re.I)
    if m:
        return ("DRME", m.group(2).rstrip("%").strip(), "")
    return None


def folders_are_parallel_peers(
    folder_a: str,
    folder_b: str,
    *,
    window_sec: int,
    ts_a: float,
    ts_b: float,
) -> bool:
    """동일 반응·다른 시료·2시간(기본) 창 — 병렬 peer 여부."""
    if folder_a == folder_b:
        return False
    key_a = folder_parallel_reaction_key(folder_a)
    key_b = folder_parallel_reaction_key(folder_b)
    if not key_a or key_a != key_b:
        return False
    if folder_sample_body(folder_a) == folder_sample_body(folder_b):
        return False
    if window_sec <= 0:
        return True
    return abs(ts_a - ts_b) <= window_sec
