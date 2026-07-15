# -*- coding: utf-8 -*-
"""
gc_identity.py — 실험실 GC **이름(표기)** 규칙

=============================================================================
[GC1 → GC4 자리 이동 — 이름만 변경]
=============================================================================

  예전 실험실 배치: GC1, GC2, GC3
  은규 Autochro 장비를 **3번 오른쪽(4번 자리)** 으로 옮김 → 표기 **GC4**
  비운 1번 자리에는 **나중에** 새 GC+새 PC가 들어와 **GC1** 이 됨.

  · PC·Autochro 장비·파이프라인은 **동일** (이름만 GC4)
  · 코드·패키지 경로 ``gc1_runtime/``, ``gc_gc1.py`` 등은 **그대로** (내부 id)
  · env 토큰 ``gc1`` / ``gc4``, role ``gc1_pc`` / ``gc4_pc`` 는 **동의어** (둘 다 Autochro)

  사람·문서 표기: **GC4 장비 PC** — docs/PC_NAMING.md
"""

from __future__ import annotations

from typing import Optional

# Autochro(은규) 장비 — 내부·레거시 토큰 gc1, 공식 표기 gc4
AUTOCHRO_INSTANCE_CODES = frozenset({"gc1", "gc4"})
AUTOCHRO_MODE_CODES = frozenset({"gc1", "gc4"})
AUTOCHRO_EQUIPMENT_ROLES = frozenset({"gc1_pc", "gc4_pc"})

# 실험실·문서·Cursor 에 쓰는 공식 이름
AUTOCHRO_DISPLAY_NAME = "GC4"
AUTOCHRO_DISPLAY_LABEL = "GC4 장비 PC"
AUTOCHRO_FORMER_NAME = "GC1"  # 구칭 (문서 안내용)

# PROFILE_DEFAULTS / 레거시 경로 키 (패키지명과 맞춤)
AUTOCHRO_CANONICAL_CODE = "gc1"


def is_autochro_instance(value: Optional[str]) -> bool:
    return (value or "").strip().lower() in AUTOCHRO_INSTANCE_CODES


def is_autochro_mode(value: Optional[str]) -> bool:
    return (value or "").strip().lower() in AUTOCHRO_MODE_CODES


def is_autochro_equipment_role(role: Optional[str]) -> bool:
    return (role or "").strip().lower() in AUTOCHRO_EQUIPMENT_ROLES


def canonical_autochro_code(value: Optional[str]) -> str:
    """
    PROFILE_DEFAULTS 조회용 — Autochro 면 항상 ``gc1`` 키.

    env 에 ``GC_INSTANCE=gc4`` 여도 기본 프로필 dict 키는 gc1.
    """
    raw = (value or "").strip().lower()
    if raw in AUTOCHRO_INSTANCE_CODES or raw in AUTOCHRO_MODE_CODES:
        return AUTOCHRO_CANONICAL_CODE
    return raw


def preferred_autochro_env_code() -> str:
    """신규 env 템플릿에 넣을 값 — ``gc4``."""
    return "gc4"


def display_name_for_instance(instance: Optional[str]) -> str:
    """show-profile 등 — Autochro 면 GC4."""
    if is_autochro_instance(instance):
        return AUTOCHRO_DISPLAY_NAME
    return (instance or "").strip().upper() or "?"
