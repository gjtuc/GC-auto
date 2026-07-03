# -*- coding: utf-8 -*-
"""
gc1_runtime.mod_apply — MOD → atom 구현 계획 (T71 기초)

``mod_registry`` 에서 ``status=ready`` 슬롯을 읽어
런타임 atom 레지스트리(``P0_P9_ATOM_IDS``)와 대조합니다.

**실제 동작 변경은 하지 않음** — dry-run 계획·검증만 (MOD 내용 입력 후 atom 패치).

CLI: ``scripts/apply_gc1_mod.py --dry-run``
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import List, Optional, Sequence, Set

from gc1_runtime.mod_registry import ModSlot, load_mod_slots, validate_mod_registry

_PHASE_RE = re.compile(r"^Ω\.A\.L4\.(P\d+)\.\d{2}$")


@dataclass
class ModImplementationPlan:
    """ready MOD 1건 — 구현 전 체크리스트."""

    mod_id: str
    title: str
    summary: str
    atom_ids: List[str]
    phases: List[str]
    leaf_ids: List[str]
    r_change: bool
    notes: List[str] = field(default_factory=list)


@dataclass
class ModApplyBatchResult:
    ok: bool
    plans: List[ModImplementationPlan] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)
    skipped_pending: int = 0


def _phase_from_atom_id(atom_id: str) -> Optional[str]:
    m = _PHASE_RE.match(atom_id)
    return m.group(1) if m else None


def resolve_target_atom_ids(slot: ModSlot) -> List[str]:
    """
    atom_ids 가 있으면 우선, 없으면 leaf_ids 중 atom 형식만 사용.

    leaf ``Ω.A.L4.P4.08.xxx`` 는 앞 4 segment 로 atom 축약.
    """
    if slot.atom_ids:
        return list(slot.atom_ids)
    out: List[str] = []
    for lid in slot.leaf_ids:
        parts = lid.split(".")
        if len(parts) >= 5 and parts[0] == "Ω" and parts[1] == "A":
            atom = ".".join(parts[:5])
            if _PHASE_RE.match(atom):
                out.append(atom)
    return sorted(set(out))


def verify_atoms_in_registry(
    atom_ids: Sequence[str],
    known_atoms: Set[str],
    *,
    mod_id: str,
) -> List[str]:
    """정적 검증 — atom ID 가 ``P0_P9_ATOM_IDS`` 에 존재."""
    errors: List[str] = []
    for aid in atom_ids:
        if aid not in known_atoms:
            errors.append(f"{mod_id}: unknown atom {aid!r} (not in P0_P9_ATOM_IDS)")
    return errors


def build_plan(
    slot: ModSlot,
    known_atoms: Set[str],
) -> tuple[Optional[ModImplementationPlan], List[str]]:
    """ready 슬롯 1건 → 계획 + 오류 목록."""
    errors: List[str] = []
    if not slot.is_ready_for_impl:
        return None, [f"{slot.mod_id}: not ready for implementation"]
    if slot.r_change:
        errors.append(f"{slot.mod_id}: r_change=true — manual R review required")

    atom_ids = resolve_target_atom_ids(slot)
    if not atom_ids:
        errors.append(f"{slot.mod_id}: no target atom_ids (set atom_ids or L4 leaf_ids)")

    errors.extend(verify_atoms_in_registry(atom_ids, known_atoms, mod_id=slot.mod_id))
    phases = sorted({p for aid in atom_ids if (p := _phase_from_atom_id(aid))})

    notes: List[str] = []
    if slot.notes.strip():
        notes.append(slot.notes.strip())
    notes.append(f"touch phases: {', '.join(phases) or '?'}")

    if errors:
        return None, errors

    return (
        ModImplementationPlan(
            mod_id=slot.mod_id,
            title=slot.title.strip(),
            summary=slot.summary.strip(),
            atom_ids=atom_ids,
            phases=phases,
            leaf_ids=list(slot.leaf_ids),
            r_change=slot.r_change,
            notes=notes,
        ),
        [],
    )


def plan_ready_mods(
    slots: Sequence[ModSlot],
    known_atoms: Set[str],
) -> ModApplyBatchResult:
    """
    실행 검증 전 단계 — ``ready``·내용 충족 슬롯만 계획 생성.

    pending 슬롯은 ``skipped_pending`` 으로 카운트 (오류 아님).
    """
    registry = validate_mod_registry(slots)
    errors = list(registry.errors)
    plans: List[ModImplementationPlan] = []
    skipped = 0

    for slot in slots:
        if slot.status not in ("ready",) and not (
            slot.is_ready_for_impl and slot.status == "pending"
        ):
            if slot.is_pending and not slot.is_ready_for_impl:
                skipped += 1
            continue
        if slot.status == "implemented":
            continue
        if not slot.is_ready_for_impl:
            skipped += 1
            continue

        plan, plan_errors = build_plan(slot, known_atoms)
        errors.extend(plan_errors)
        if plan is not None:
            plans.append(plan)

    return ModApplyBatchResult(
        ok=not errors,
        plans=plans,
        errors=errors,
        skipped_pending=skipped,
    )


def load_known_atom_ids() -> Set[str]:
    """런타임 L4 atom 레지스트리 — import 시점 로드."""
    from gc1_runtime.layer4_atoms_p8_p9 import P0_P9_ATOM_IDS

    return set(P0_P9_ATOM_IDS)


def plan_from_json(path: Optional[str] = None) -> ModApplyBatchResult:
    slots = load_mod_slots(path) if path else load_mod_slots()
    return plan_ready_mods(slots, load_known_atom_ids())
