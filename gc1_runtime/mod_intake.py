# -*- coding: utf-8 -*-
"""
gc1_runtime.mod_intake — MOD 슬롯 JSON 갱신 (T86)

사용자 수정사항 텍스트를 ``gc1_mod_slots.json`` 에 기록한 뒤
``validate_mod_registry`` 로 정적 검증.

CLI: ``scripts/intake_gc1_mod.py``
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional, Sequence

from gc1_runtime.mod_apply import plan_ready_mods, load_known_atom_ids
from gc1_runtime.mod_lifecycle import save_mod_slots
from gc1_runtime.mod_registry import (
    DEFAULT_MOD_SLOTS_PATH,
    ModSlot,
    get_slot,
    load_mod_slots,
    validate_mod_registry,
)


@dataclass
class ModIntakeRequest:
    """MOD 슬롯 1건 입력."""

    mod_id: str
    title: str
    summary: str
    leaf_ids: List[str]
    atom_ids: List[str] = field(default_factory=list)
    status: str = "ready"
    r_change: bool = False


@dataclass
class ModIntakeResult:
    ok: bool
    mod_id: str
    message: str = ""
    validation_errors: List[str] = field(default_factory=list)
    plan_atom_count: int = 0


def apply_intake_to_slots(
    slots: List[ModSlot],
    request: ModIntakeRequest,
) -> List[ModSlot]:
    """메모리 상 슬롯 목록 갱신 (파일 쓰기 없음)."""
    idx = next((i for i, s in enumerate(slots) if s.mod_id == request.mod_id), -1)
    if idx < 0:
        raise KeyError(f"unknown mod_id: {request.mod_id}")
    old = slots[idx]
    atom_ids = list(request.atom_ids) if request.atom_ids else []
    slots[idx] = ModSlot(
        mod_id=old.mod_id,
        queue_task=old.queue_task,
        status=request.status,
        title=request.title.strip(),
        summary=request.summary.strip(),
        leaf_ids=list(request.leaf_ids),
        atom_ids=atom_ids,
        r_change=request.r_change,
        notes=old.notes,
    )
    return slots


def intake_mod_slot(
    request: ModIntakeRequest,
    path: str = DEFAULT_MOD_SLOTS_PATH,
    *,
    verify_plan: bool = True,
) -> ModIntakeResult:
    """
    실행 검증 — JSON 저장 + registry 검증 + (선택) apply plan.

    ``verify_plan=True`` 이면 atom ID 가 ``P0_P9_ATOM_IDS`` 에 있는지 확인.
    """
    slots = load_mod_slots(path)
    if get_slot(slots, request.mod_id) is None:
        return ModIntakeResult(ok=False, mod_id=request.mod_id, message="unknown mod_id")

    apply_intake_to_slots(slots, request)
    validation = validate_mod_registry(slots)
    if not validation.ok:
        return ModIntakeResult(
            ok=False,
            mod_id=request.mod_id,
            message="validation failed",
            validation_errors=list(validation.errors),
        )

    plan_count = 0
    if verify_plan and request.status in ("ready", "pending"):
        batch = plan_ready_mods(slots, load_known_atom_ids())
        if not batch.ok:
            return ModIntakeResult(
                ok=False,
                mod_id=request.mod_id,
                message="apply plan failed",
                validation_errors=list(batch.errors),
            )
        plan_count = len([p for p in batch.plans if p.mod_id == request.mod_id])

    save_mod_slots(slots, path)
    return ModIntakeResult(
        ok=True,
        mod_id=request.mod_id,
        message="saved",
        plan_atom_count=plan_count,
    )


def parse_leaf_list(raw: Sequence[str]) -> List[str]:
    """쉼표 구분 leaf ID 목록."""
    out: List[str] = []
    for part in raw:
        for piece in part.split(","):
            piece = piece.strip()
            if piece:
                out.append(piece)
    return out
