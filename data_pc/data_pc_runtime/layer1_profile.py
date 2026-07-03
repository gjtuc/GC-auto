# -*- coding: utf-8 -*-
"""
L1 — machine_profile.json (PEG/KCH) 로드 — supervisor 게이트·경로 분기.

=============================================================================
[LLM/에이전트 — PC별 게이트 정책]
=============================================================================

  supervisor(data_pc_runtime) 는 15초마다 GateEvaluator 를 호출한다.
  **어떤 조건을 통과해야 파이프라인이 도는지**는 이 모듈 + gc_automation.env 로 결정.

  ┌─────────────────┬──────────────┬──────────────┬─────────────────────────┐
  │ PC              │ storage      │ check_gdrive │ Wi-Fi 게이트            │
  ├─────────────────┼──────────────┼──────────────┼─────────────────────────┤
  │ 차헌 (데이터 PC)│ KCH          │ True (G:)    │ 끔 (DATA_PC_SKIP_WIFI)  │
  │ 은규 (데이터 PC)│ PEG          │ False        │ 끔 (이더넷 상시)        │
  │ GC 장비 PC      │ —            │ —            │ iptime/iPhone (gc_watch)│
  └─────────────────┴──────────────┴──────────────┴─────────────────────────┘

  은규 PC 이식 시:
    PEG\\machine_profile.json → "uses_g_drive": false
    → resolve_check_gdrive() == False
    → layer2_gates L2-3.5 건너뜀 → 15초 IMAP 폴링만 (게이트 없음)

  차헌 PC:
    machine_profile 에 uses_g_drive 없음 → 기본 True
    → G: (SecuYouSB) 열릴 때까지 waiting_gdrive

  env 오버라이드 (테스트·수동):
    DATA_PC_SKIP_GDRIVE_GATE=1  → G: 게이트 끔
    DATA_PC_USES_G_DRIVE=0/1    → profile 보다 env 우선

  문서: docs/은규PC_이식_가이드.md, deploy/DATA_PC_HOME_LAYOUT.md
=============================================================================
"""

from __future__ import annotations

import json
import os


def data_pc_work_subdir(script_dir: str) -> str:
    """
    연구원별 작업 폴더명.

    · PEG — Park Eungyu Gyu (은규 PC, gc-data-pc)
    · KCH — Kim Chaheon (차헌 PC, Desktop\\.cursor)
    """
    for name in ("PEG", "KCH"):
        if os.path.isdir(os.path.join(script_dir, name)):
            return name
    return "KCH"


def load_machine_profile(script_dir: str) -> dict:
    """PEG\\machine_profile.json 또는 KCH\\machine_profile.json (Git 제외)."""
    path = os.path.join(script_dir, data_pc_work_subdir(script_dir), "machine_profile.json")
    if not os.path.isfile(path):
        return {}
    try:
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
        return data if isinstance(data, dict) else {}
    except (OSError, ValueError, TypeError):
        return {}


def _env_bool(name: str) -> bool | None:
    raw = os.getenv(name, "").strip().lower()
    if not raw:
        return None
    if raw in ("1", "true", "yes", "on"):
        return True
    if raw in ("0", "false", "no", "off"):
        return False
    return None


def resolve_check_gdrive(script_dir: str) -> bool:
    """
  G: 가용성 게이트(L2-3.5) 사용 여부.

    True  — 차헌 PC: EXPERIMENT_DATA_ROOT(G:) 없으면 파이프라인 대기
    False — 은규 PC: 게이트 없음, 15초마다 메일·연구노트·Origin 시도

    판정 순서:
      1) DATA_PC_SKIP_GDRIVE_GATE=1 → False
      2) DATA_PC_USES_G_DRIVE=0/1 → env
      3) machine_profile uses_g_drive === false → False
      4) 기본 True (차헌·레거시 호환)
    """
    if _env_bool("DATA_PC_SKIP_GDRIVE_GATE") is True:
        return False
    uses = _env_bool("DATA_PC_USES_G_DRIVE")
    if uses is not None:
        return uses
    prof = load_machine_profile(script_dir)
    if prof.get("uses_g_drive") is False:
        return False
    return True
