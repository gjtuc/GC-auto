# -*- coding: utf-8 -*-
"""
gc1_runtime.layer0_fallback — PART6 ``fallback_channel`` 파싱·검증 (T92)

설계: ``deploy/GC1_RUNTIME_DESIGN_PART1_L2.md`` §L2-G-ATOM FB
데이터: ``deploy/gc1_atom_retry_policy.json`` policies[].fallback_channel

정적: 문자열 → kind 토큰 (실행은 ``layer4_atom_fallback``).
"""
from __future__ import annotations

from typing import Dict, Optional

# 설계 표기 → 내부 kind (대소문자 무시 lookup)
_NORM_MAP: Dict[str, str] = {
    "h re-click neutral": "h_reclick_neutral",
    "h resend ^a": "h_resend_ctrl_a",
    "e eye click 초기화": "e_eye_menu_init",
    "f send_keys path": "f_send_keys_open",
    "send_keys enter": "send_keys_enter",
    "%s": "send_keys_alt_s",
}


def parse_fallback_channel(raw: Optional[str]) -> Optional[str]:
    """
    Ω.A.L2.GAT.FB.01 — ``fallback_channel`` 문자열 → 실행 kind.

    미지원·null → None.
    """
    if not raw or not str(raw).strip():
        return None
    return _NORM_MAP.get(str(raw).strip().lower())


def fallback_kind_label(kind: Optional[str]) -> str:
    """로그용 — kind → 설계 문자열 역매핑 (근사)."""
    rev = {v: k for k, v in _NORM_MAP.items()}
    return rev.get(kind or "", kind or "")
