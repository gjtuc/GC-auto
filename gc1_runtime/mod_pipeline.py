# -*- coding: utf-8 -*-
"""
gc1_runtime.mod_pipeline — MOD 전체 파이프라인 점검 (T87)

T70~T86 도구를 한 번에 실행 검증 (atom 패치 제외).

순서:
  1) registry validate (정적)
  2) queue summary
  3) ready 슬롯 apply plan (실행·dry-run)
  4) 미완료 슬롯 안내

CLI: ``scripts/run_gc1_mod_pipeline.py``
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional

from gc1_runtime.mod_apply import ModApplyBatchResult, plan_ready_mods, load_known_atom_ids
from gc1_runtime.mod_lifecycle import (
    ModQueueSummary,
    all_user_mods_resolved,
    summarize_mod_queue,
)
from gc1_runtime.mod_registry import (
    DEFAULT_MOD_SLOTS_PATH,
    ModSlot,
    load_mod_slots,
    validate_mod_registry,
)


@dataclass
class PipelineStep:
    """파이프라인 1단계 결과."""

    name: str
    ok: bool
    detail: str = ""


@dataclass
class ModPipelineReport:
    """MOD 파이프라인 전체 보고."""

    ok: bool
    steps: List[PipelineStep] = field(default_factory=list)
    summary: Optional[ModQueueSummary] = None
    apply: Optional[ModApplyBatchResult] = None
    ready_mod_ids: List[str] = field(default_factory=list)
    pending_mod_ids: List[str] = field(default_factory=list)
    implemented_mod_ids: List[str] = field(default_factory=list)
    hints: List[str] = field(default_factory=list)


def _classify_slots(slots: List[ModSlot]) -> tuple[list[str], list[str], list[str]]:
    ready: List[str] = []
    pending: List[str] = []
    implemented: List[str] = []
    for s in slots:
        if s.status == "implemented":
            implemented.append(s.mod_id)
        elif s.is_ready_for_impl and s.status in ("ready", "pending"):
            ready.append(s.mod_id)
        else:
            pending.append(s.mod_id)
    return ready, pending, implemented


def run_mod_pipeline(
    path: str = DEFAULT_MOD_SLOTS_PATH,
    *,
    run_apply_plan: bool = True,
) -> ModPipelineReport:
    """
    MOD 파이프라인 점검 — 파일 I/O + plan (atom 코드 변경 없음).

    ``run_apply_plan=False`` 이면 1~2단계만 (정적+집계).
    """
    steps: List[PipelineStep] = []
    hints: List[str] = []

    try:
        slots = load_mod_slots(path)
    except (OSError, ValueError) as exc:
        return ModPipelineReport(
            ok=False,
            steps=[PipelineStep("load_json", False, str(exc))],
        )

    validation = validate_mod_registry(slots)
    steps.append(
        PipelineStep(
            "validate_registry",
            validation.ok,
            "ok" if validation.ok else "; ".join(validation.errors[:3]),
        )
    )

    summary = summarize_mod_queue(slots)
    ready_ids, pending_ids, impl_ids = _classify_slots(slots)
    steps.append(
        PipelineStep(
            "queue_summary",
            True,
            f"total={summary.total} ready={len(ready_ids)} pending={len(pending_ids)} impl={len(impl_ids)}",
        )
    )

    apply_result: Optional[ModApplyBatchResult] = None
    if run_apply_plan and validation.ok:
        apply_result = plan_ready_mods(slots, load_known_atom_ids())
        steps.append(
            PipelineStep(
                "apply_plan_dry_run",
                apply_result.ok,
                f"plans={len(apply_result.plans)} errors={len(apply_result.errors)}",
            )
        )
        if apply_result.plans:
            for plan in apply_result.plans:
                hints.append(
                    f"{plan.mod_id}: patch atoms {', '.join(plan.atom_ids)} then close_gc1_mod.py"
                )
        elif ready_ids:
            hints.append("ready slots exist but plan empty - check atom IDs")
    elif not run_apply_plan:
        steps.append(PipelineStep("apply_plan_dry_run", True, "skipped"))

    if not ready_ids and pending_ids and not all_user_mods_resolved(slots):
        hints.append("pending: use intake_gc1_mod.py --mod MOD-N --title ... --summary ... --leaf ...")

    if validation.warnings:
        for w in validation.warnings[:5]:
            hints.append(f"warn: {w}")

    ok = validation.ok and (apply_result.ok if apply_result is not None else True)
    return ModPipelineReport(
        ok=ok,
        steps=steps,
        summary=summary,
        apply=apply_result,
        ready_mod_ids=ready_ids,
        pending_mod_ids=pending_ids,
        implemented_mod_ids=impl_ids,
        hints=hints,
    )
