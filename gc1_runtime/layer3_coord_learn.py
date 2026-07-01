# -*- coding: utf-8 -*-
"""
시료 표·동기화 클릭 좌표 학습 — mouse_only/coord_only 에서도 maturity 규칙 유지.

``GC1_OCR_LEARN=1`` · ``GC1_OCR_MATURITY_RATE``(기본 0.99) 와 동일하게
성공/실패를 누적하고, 성숙한 x_frac 을 overlay 에 저장합니다.

미지시료·시료종류 열(드롭다운)은 **클릭 금지 구간** — 학습값도 clamp.
"""
from __future__ import annotations

import json
import os
from typing import Any, Tuple

from gc1_runtime.layer3_ocr_learn import learnings_enabled, load_overlay, overlay_path
from gc1_runtime.layer3_ocr_maturity import (
    MATURITY_RATE,
    MIN_ATTEMPTS,
    record_outcome,
    skill_key,
    should_learn_skill,
)

# 행번호 열 (Ctrl+A·포커스) — 왼쪽 끝만
ROW_X_FRAC_MIN = 0.03
ROW_X_FRAC_MAX = 0.14

# 시료이름 열 (우클릭) — 미지시료·시료종류(대략 0.08~0.18) 오른쪽만
NAME_X_FRAC_MIN = 0.18
NAME_X_FRAC_MAX = 0.38

# 제어목록 동기화 — 파일이름(.raw) 열
SYNC_RAW_X_FRAC_MIN = 0.45
SYNC_RAW_X_FRAC_MAX = 0.82

_PURPOSE_ENV = {
    "row": "AUTOCHRO_LIST_ROW_X_FRAC",
    "name": "AUTOCHRO_LIST_NAME_X_FRAC",
    "sync_raw": "AUTOCHRO_SYNC_RAW_X_FRAC",
    "tree_name": "AUTOCHRO_TREE_NAME_X_FRAC",
}

_PURPOSE_DEFAULT = {
    "row": 0.06,
    "name": 0.26,
    "sync_raw": 0.62,
    "tree_name": 0.22,
}

_PURPOSE_CLAMP = {
    "row": (ROW_X_FRAC_MIN, ROW_X_FRAC_MAX),
    "name": (NAME_X_FRAC_MIN, NAME_X_FRAC_MAX),
    "sync_raw": (SYNC_RAW_X_FRAC_MIN, SYNC_RAW_X_FRAC_MAX),
    "tree_name": (0.08, 0.45),
}

_STEP_FOR_PURPOSE = {
    "row": "P2.before_ctrl_a",
    "name": "P3.before_right_click",
    "sync_raw": "P1.before_sync",
}


def _clamp_frac(purpose: str, x_frac: float) -> float:
    lo, hi = _PURPOSE_CLAMP[purpose]
    return min(max(float(x_frac), lo), hi)


def _env_default_frac(purpose: str) -> float:
    env_key = _PURPOSE_ENV[purpose]
    raw = os.getenv(env_key, str(_PURPOSE_DEFAULT[purpose])).strip()
    try:
        return _clamp_frac(purpose, float(raw))
    except ValueError:
        return _clamp_frac(purpose, _PURPOSE_DEFAULT[purpose])


def _overlay_coords() -> dict:
    try:
        return dict(load_overlay().get("coords") or {})
    except Exception:
        return {}


def _save_overlay_coords(coords: dict) -> None:
    if not learnings_enabled():
        return
    overlay = load_overlay()
    overlay["coords"] = coords
    overlay_path().write_text(
        json.dumps(overlay, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def get_learned_x_frac(purpose: str) -> float:
    """
    학습된 x_frac — 미성숙이면 env 기본값.

    purpose: ``row`` | ``name`` | ``sync_raw``
    """
    default = _env_default_frac(purpose)
    entry = _overlay_coords().get(purpose) or {}
    if not entry.get("mature"):
        return default
    try:
        return _clamp_frac(purpose, float(entry.get("x_frac") or default))
    except (TypeError, ValueError):
        return default


def list_rel_from_purpose(sample_list, purpose: str) -> Tuple[int, int]:
    """ListView 상대 (rel_x, rel_y) — 학습·env·안전 clamp."""
    x_frac = get_learned_x_frac(purpose)
    rect = sample_list.rectangle()
    width = max(rect.width(), 400)
    height = max(rect.height(), 80)
    rel_x = max(8, int(width * x_frac))
    rel_y = max(16, min(32, height // 10))
    return rel_x, rel_y


def list_rel_from_x_frac(sample_list, x_frac: float, *, purpose: str) -> Tuple[int, int]:
    """주어진 x_frac 을 안전 구간으로 clamp 후 rel 좌표."""
    safe = _clamp_frac(purpose, x_frac)
    rect = sample_list.rectangle()
    width = max(rect.width(), 400)
    height = max(rect.height(), 80)
    rel_x = max(8, int(width * safe))
    rel_y = max(16, min(32, height // 10))
    return rel_x, rel_y


def rel_x_is_safe(sample_list, rel_x: int, *, purpose: str) -> bool:
    """미지시료·시료종류 열 등 금지 구간 여부."""
    rect = sample_list.rectangle()
    width = max(rect.width(), 400)
    x_frac = rel_x / width
    lo, hi = _PURPOSE_CLAMP[purpose]
    return lo <= x_frac <= hi


def ocr_rel_is_safe(sample_list, rel_x: int, rel_y: int, token_text: str = "") -> bool:
    """
    OCR 앵커가 시료 표에서 안전한 열인지.

    ``미지``·``시료종류`` 토큰이면 거부. x_frac 이 드롭다운 구간이면 거부.
    """
    tok = (token_text or "").replace(" ", "")
    if "미지시료" in tok or tok.startswith("미지"):
        return False
    if "시료종류" in tok:
        return False
    rect = sample_list.rectangle()
    width = max(rect.width(), 400)
    x_frac = rel_x / width
    if x_frac > ROW_X_FRAC_MAX and x_frac < NAME_X_FRAC_MIN:
        return False
    return True


def record_coord_click(
    purpose: str,
    x_frac: float,
    *,
    success: bool,
    step_id: str = "",
) -> None:
    """좌표 클릭 결과 — maturity + overlay coords 갱신."""
    if not learnings_enabled():
        return
    sid = step_id or _STEP_FOR_PURPOSE.get(purpose, purpose)
    key = skill_key(sid, "list_coords", purpose)
    safe_frac = _clamp_frac(purpose, x_frac)
    record_outcome(
        key,
        success=success,
        confidence=1.0 if success else 0.0,
        method="coord_click",
    )
    if not should_learn_skill(key):
        return
    coords = _overlay_coords()
    entry: dict[str, Any] = dict(coords.get(purpose) or {})
    current = float(entry.get("x_frac") or _env_default_frac(purpose))
    att = int(entry.get("attempts") or 0) + 1
    succ = int(entry.get("successes") or 0) + (1 if success else 0)
    if success:
        entry["x_frac"] = round(current * 0.85 + safe_frac * 0.15, 4)
    else:
        entry["x_frac"] = current
    entry["attempts"] = att
    entry["successes"] = succ
    entry["rate"] = round(succ / att, 6) if att else 0.0
    entry["mature"] = att >= MIN_ATTEMPTS and entry["rate"] >= MATURITY_RATE
    coords[purpose] = entry
    _save_overlay_coords(coords)


def record_tree_screen_click(
    tree,
    screen_x: int,
    screen_y: int,
    *,
    success: bool,
    step_id: str = "P4.tree_ocr",
) -> None:
    """트리 OCR 우클릭 성공 — maturity 기록 (Y 는 참고용, 매번 OCR 우선)."""
    if not learnings_enabled():
        return
    try:
        rect = tree.rectangle()
        w = max(int(rect.width()), 200)
        x_frac = (int(screen_x) - int(rect.left)) / w
        x_frac = min(max(x_frac, 0.05), 0.45)
        record_coord_click("tree_name", x_frac, success=success, step_id=step_id)
    except Exception:
        pass


def sync_double_click_rel(width: int, height: int) -> Tuple[int, int]:
    """제어목록 동기화 더블클릭 — 학습 x_frac 반영."""
    x_frac = get_learned_x_frac("sync_raw")
    rel_y = max(18, min(40, height // 6))
    rel_x = max(20, int(width * x_frac))
    return rel_x, rel_y
