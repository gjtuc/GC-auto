# -*- coding: utf-8 -*-
"""
gc1_runtime.mod_registry — MOD 슬롯 수용·검증 (T70 기초)

설계: ``deploy/GC1_RUNTIME_DESIGN.md`` §MOD
데이터: ``deploy/gc1_mod_slots.json``

MOD-1~3 **내용이 채워지기 전** atom 구현은 하지 않음.
본 모듈은 JSON 스키마 검증·pending/ready 판별만 담당 (정적 검증).
CLI: ``scripts/validate_gc1_mod_slots.py``
"""
from __future__ import annotations

import json
import os
import re
from dataclasses import dataclass, field
from typing import List, Optional, Sequence

_REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEFAULT_MOD_SLOTS_PATH = os.path.join(_REPO_ROOT, "deploy", "gc1_mod_slots.json")

_MOD_ID_RE = re.compile(r"^MOD-[1-9]\d*$")
_LEAF_ID_RE = re.compile(r"^Ω\.A\.L\d+\.")
_ATOM_ID_RE = re.compile(r"^Ω\.A\.L4\.P\d+\.\d{2}$")
_VALID_STATUS = frozenset({"pending", "ready", "implemented", "blocked"})


@dataclass
class ModSlot:
    """MOD 슬롯 1개 — 사용자 수정사항 → leaf/atom 매핑."""

    mod_id: str
    queue_task: str
    status: str
    title: str
    summary: str
    leaf_ids: List[str] = field(default_factory=list)
    atom_ids: List[str] = field(default_factory=list)
    r_change: bool = False
    notes: str = ""

    @property
    def is_pending(self) -> bool:
        return self.status == "pending"

    @property
    def is_ready_for_impl(self) -> bool:
        """atom 구현 착수 가능 — title·summary·leaf_ids 최소 1개."""
        if self.status not in ("pending", "ready"):
            return False
        return bool(self.title.strip() and self.summary.strip() and self.leaf_ids)


@dataclass
class ModRegistryValidation:
    ok: bool
    slots: List[ModSlot] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)


def load_mod_slots(path: str = DEFAULT_MOD_SLOTS_PATH) -> List[ModSlot]:
    """JSON → ``ModSlot`` 목록 (구문 검증만, 비즈니스 검증은 ``validate_mod_registry``)."""
    with open(path, encoding="utf-8") as fh:
        raw = json.load(fh)
    if "slots" not in raw or not isinstance(raw["slots"], list):
        raise ValueError(f"invalid mod slots file (missing slots[]): {path}")
    out: List[ModSlot] = []
    for item in raw["slots"]:
        out.append(
            ModSlot(
                mod_id=str(item["mod_id"]),
                queue_task=str(item.get("queue_task", "")),
                status=str(item.get("status", "pending")),
                title=str(item.get("title", "")),
                summary=str(item.get("summary", "")),
                leaf_ids=list(item.get("leaf_ids") or []),
                atom_ids=list(item.get("atom_ids") or []),
                r_change=bool(item.get("r_change", False)),
                notes=str(item.get("notes", "")),
            )
        )
    return out


def _validate_id_list(
    ids: Sequence[str],
    pattern: re.Pattern[str],
    label: str,
    errors: List[str],
    *,
    mod_id: str,
) -> None:
    for lid in ids:
        if not pattern.search(lid):
            errors.append(f"{mod_id}: invalid {label} id {lid!r}")


def validate_mod_registry(slots: Sequence[ModSlot]) -> ModRegistryValidation:
    """
    정적 검증 — MOD JSON 스키마·ID 형식.

  ``status=ready`` 이면 title/summary/leaf_ids 필수.
    """
    errors: List[str] = []
    warnings: List[str] = []
    seen: set[str] = set()

    for slot in slots:
        if not _MOD_ID_RE.match(slot.mod_id):
            errors.append(f"invalid mod_id: {slot.mod_id!r}")
        if slot.mod_id in seen:
            errors.append(f"duplicate mod_id: {slot.mod_id}")
        seen.add(slot.mod_id)

        if slot.status not in _VALID_STATUS:
            errors.append(f"{slot.mod_id}: unknown status {slot.status!r}")

        _validate_id_list(slot.leaf_ids, _LEAF_ID_RE, "leaf", errors, mod_id=slot.mod_id)
        _validate_id_list(slot.atom_ids, _ATOM_ID_RE, "atom", errors, mod_id=slot.mod_id)

        if slot.status == "ready":
            if not slot.title.strip():
                errors.append(f"{slot.mod_id}: ready requires title")
            if not slot.summary.strip():
                errors.append(f"{slot.mod_id}: ready requires summary")
            if not slot.leaf_ids:
                errors.append(f"{slot.mod_id}: ready requires leaf_ids")

        if slot.is_ready_for_impl and slot.status == "pending":
            warnings.append(
                f"{slot.mod_id}: content filled but status still pending — set ready"
            )

        if slot.status == "pending" and not slot.title.strip():
            warnings.append(f"{slot.mod_id}: awaiting user modification text")

    return ModRegistryValidation(
        ok=not errors,
        slots=list(slots),
        errors=errors,
        warnings=warnings,
    )


def get_slot(slots: Sequence[ModSlot], mod_id: str) -> Optional[ModSlot]:
    for s in slots:
        if s.mod_id == mod_id:
            return s
    return None


def pending_slots(slots: Sequence[ModSlot]) -> List[ModSlot]:
    return [s for s in slots if s.is_pending and not s.is_ready_for_impl]


def ready_for_impl(slots: Sequence[ModSlot]) -> List[ModSlot]:
    return [s for s in slots if s.is_ready_for_impl and s.status in ("pending", "ready")]
