# -*- coding: utf-8 -*-
"""
gc1_runtime.mod_lifecycle — MOD 슬롯 상태 전이·큐 요약 (T72)

흐름: ``validate_gc1_mod_slots`` → ``apply_gc1_mod --dry-run`` → atom 패치 → ``close_gc1_mod``

``status`` 값:
  pending → ready → implemented
  blocked (사용자 보류)

CLI: ``scripts/status_gc1_mod.py`` · ``scripts/close_gc1_mod.py``
"""
from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from typing import List, Optional, Sequence

from gc1_runtime.mod_registry import (
    DEFAULT_MOD_SLOTS_PATH,
    ModSlot,
    load_mod_slots,
    validate_mod_registry,
)

_VALID_TRANSITIONS = {
    "pending": frozenset({"ready", "blocked"}),
    "ready": frozenset({"implemented", "blocked", "pending"}),
    "implemented": frozenset(),
    "blocked": frozenset({"pending", "ready"}),
}


@dataclass
class ModQueueSummary:
    """MOD 슬롯 집계 — 에이전트 큐·운영 보고용."""

    total: int
    pending: int
    ready: int
    implemented: int
    blocked: int
    awaiting_user: int
    ready_for_atom_patch: int
    mod_ids: List[str] = field(default_factory=list)


@dataclass
class ModTransitionResult:
    ok: bool
    mod_id: str
    old_status: str
    new_status: str
    message: str = ""


def summarize_mod_queue(slots: Sequence[ModSlot]) -> ModQueueSummary:
    """정적 집계 — 슬롯 목록만으로 상태 카운트."""
    pending = ready = implemented = blocked = 0
    awaiting = ready_patch = 0
    ids: List[str] = []
    for s in slots:
        ids.append(s.mod_id)
        st = s.status
        if st == "pending":
            pending += 1
            if not s.is_ready_for_impl:
                awaiting += 1
            else:
                ready_patch += 1
        elif st == "ready":
            ready += 1
            if s.is_ready_for_impl:
                ready_patch += 1
        elif st == "implemented":
            implemented += 1
        elif st == "blocked":
            blocked += 1
    return ModQueueSummary(
        total=len(slots),
        pending=pending,
        ready=ready,
        implemented=implemented,
        blocked=blocked,
        awaiting_user=awaiting,
        ready_for_atom_patch=ready_patch,
        mod_ids=ids,
    )


def all_user_mods_resolved(slots: Sequence[ModSlot]) -> bool:
    """
    사용자 MOD 처리 완료 여부.

    ``implemented`` 또는 ``blocked`` 만 남으면 True.
    ``pending``/``ready``(내용 있음) 는 미완료.
    """
    for s in slots:
        if s.status in ("implemented", "blocked"):
            continue
        if s.is_ready_for_impl:
            return False
        if s.status == "ready":
            return False
        if s.status == "pending":
            return False
    return True


def slots_to_json_dict(slots: Sequence[ModSlot], *, version: int = 1) -> dict:
    """``ModSlot`` → ``gc1_mod_slots.json`` 직렬화."""
    return {
        "version": version,
        "slots": [
            {
                "mod_id": s.mod_id,
                "queue_task": s.queue_task,
                "status": s.status,
                "title": s.title,
                "summary": s.summary,
                "leaf_ids": list(s.leaf_ids),
                "atom_ids": list(s.atom_ids),
                "r_change": s.r_change,
                "notes": s.notes,
            }
            for s in slots
        ],
    }


def save_mod_slots(
    slots: Sequence[ModSlot],
    path: str = DEFAULT_MOD_SLOTS_PATH,
    *,
    version: int = 1,
) -> None:
    """실행 검증 — JSON 파일 갱신 (``close_gc1_mod`` 후 status=implemented)."""
    payload = slots_to_json_dict(slots, version=version)
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(payload, fh, ensure_ascii=False, indent=2)
        fh.write("\n")


def _find_slot_index(slots: List[ModSlot], mod_id: str) -> int:
    for i, s in enumerate(slots):
        if s.mod_id == mod_id:
            return i
    return -1


def transition_status(
    slot: ModSlot,
    new_status: str,
    *,
    mod_id: str = "",
) -> ModTransitionResult:
    """상태 전이 규칙 검증 (파일 쓰기 없음)."""
    mid = mod_id or slot.mod_id
    allowed = _VALID_TRANSITIONS.get(slot.status, frozenset())
    if new_status not in allowed and slot.status != new_status:
        return ModTransitionResult(
            ok=False,
            mod_id=mid,
            old_status=slot.status,
            new_status=new_status,
            message=f"transition {slot.status!r} -> {new_status!r} not allowed",
        )
    if new_status == "implemented" and not slot.is_ready_for_impl:
        return ModTransitionResult(
            ok=False,
            mod_id=mid,
            old_status=slot.status,
            new_status=new_status,
            message="implemented requires title/summary/leaf_ids (ready content)",
        )
    return ModTransitionResult(
        ok=True,
        mod_id=mid,
        old_status=slot.status,
        new_status=new_status,
        message="ok",
    )


def mark_implemented(
    mod_id: str,
    path: str = DEFAULT_MOD_SLOTS_PATH,
) -> ModTransitionResult:
    """
    실행 검증 — atom 패치 완료 후 ``status=implemented`` 저장.

    슬롯이 ``ready`` 이거나 내용이 채워진 ``pending`` 이어야 함.
    """
    slots = load_mod_slots(path)
    idx = _find_slot_index(slots, mod_id)
    if idx < 0:
        return ModTransitionResult(
            ok=False,
            mod_id=mod_id,
            old_status="",
            new_status="implemented",
            message=f"unknown mod_id: {mod_id}",
        )
    slot = slots[idx]
    check = transition_status(slot, "implemented", mod_id=mod_id)
    if not check.ok:
        return check
    slots[idx] = ModSlot(
        mod_id=slot.mod_id,
        queue_task=slot.queue_task,
        status="implemented",
        title=slot.title,
        summary=slot.summary,
        leaf_ids=list(slot.leaf_ids),
        atom_ids=list(slot.atom_ids),
        r_change=slot.r_change,
        notes=slot.notes,
    )
    validation = validate_mod_registry(slots)
    if not validation.ok:
        return ModTransitionResult(
            ok=False,
            mod_id=mod_id,
            old_status=slot.status,
            new_status="implemented",
            message="; ".join(validation.errors),
        )
    save_mod_slots(slots, path)
    return ModTransitionResult(
        ok=True,
        mod_id=mod_id,
        old_status=slot.status,
        new_status="implemented",
        message="saved",
    )


def load_queue_summary(path: Optional[str] = None) -> ModQueueSummary:
    slots = load_mod_slots(path) if path else load_mod_slots()
    return summarize_mod_queue(slots)
