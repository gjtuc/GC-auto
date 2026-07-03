# -*- coding: utf-8 -*-
"""
gc1_runtime.layer0_gpost — PART6 §G-POST eye verify retry (T91)

설계: ``deploy/GC1_RUNTIME_DESIGN_PART6_RETRY.md`` §G-POST retry
데이터: ``deploy/gc1_atom_retry_policy.json`` → ``g_post_retry[]``

TASK 실패 시 **1회** 선행 atom 재시도(또는 추가 대기) 후 재판별.
정적: plan 로드·스키마
실행: ``run_gpost_eye_verify()`` — L4 P1.11 / P3.06 / P4.08 / P6.06 / P7.05 에서 호출
"""
from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional

_REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEFAULT_RETRY_POLICY_PATH = os.path.join(_REPO_ROOT, "deploy", "gc1_atom_retry_policy.json")

EvaluateFn = Callable[[], tuple[bool, dict[str, Any]]]
RetryFn = Callable[[], None]
SleepFn = Callable[[float], None]


@dataclass(frozen=True)
class GPostRetryPlan:
    """G-POST retry 1행 — eye TASK 실패 시 선행 조치."""

    task_id: str
    retry_atom_id: Optional[str] = None
    extra_wait_sec: float = 0.0
    fail_code: str = "E_VERIFY_PEAK"
    description: str = ""


@dataclass
class GPostVerifyResult:
    """``run_gpost_eye_verify`` 실행 결과."""

    task_id: str
    passed: bool
    retried: bool = False
    fail_code: Optional[str] = None
    detail: str = ""
    probe_snapshot: dict[str, Any] = field(default_factory=dict)


# JSON 없을 때 PART6 기본
_BUILTIN_GPOST_PLANS: Dict[str, GPostRetryPlan] = {
    "verify_peak_table_cleared": GPostRetryPlan(
        task_id="verify_peak_table_cleared",
        retry_atom_id="Ω.A.L4.P3.04",
        fail_code="E_VERIFY_PEAK",
        description="retry P3.04 once, then E_VERIFY_PEAK",
    ),
    "verify_peak_table_has_data": GPostRetryPlan(
        task_id="verify_peak_table_has_data",
        retry_atom_id="Ω.A.L4.P4.07",
        extra_wait_sec=2.0,
        fail_code="E_VERIFY_PEAK",
        description="retry P4.07 wait +2s, then E_VERIFY_PEAK",
    ),
    "verify_active_tab_analysis": GPostRetryPlan(
        task_id="verify_active_tab_analysis",
        retry_atom_id="Ω.A.L4.P1.09",
        fail_code="E_VERIFY_TAB",
        description="retry P1.09 once",
    ),
}


def load_gpost_plans(path: str = DEFAULT_RETRY_POLICY_PATH) -> Dict[str, GPostRetryPlan]:
    """
    ``g_post_retry[]`` → task_id 키 dict.

    JSON 필드: task, retry_atom_id, extra_wait_sec, fail_code, action(설명).
    """
    if not os.path.isfile(path):
        return dict(_BUILTIN_GPOST_PLANS)

    with open(path, encoding="utf-8") as fh:
        raw = json.load(fh)
    rows = raw.get("g_post_retry") or []
    out: Dict[str, GPostRetryPlan] = {}
    for item in rows:
        task_id = str(item.get("task", "")).strip()
        if not task_id:
            continue
        extra = item.get("extra_wait_sec", 0.0)
        try:
            extra_f = float(extra) if extra is not None else 0.0
        except (TypeError, ValueError):
            extra_f = 0.0
        out[task_id] = GPostRetryPlan(
            task_id=task_id,
            retry_atom_id=item.get("retry_atom_id") or None,
            extra_wait_sec=extra_f,
            fail_code=str(item.get("fail_code") or "E_VERIFY_PEAK"),
            description=str(item.get("action") or ""),
        )
    return out if out else dict(_BUILTIN_GPOST_PLANS)


def get_gpost_plan(
    task_id: str,
    plans: Optional[Dict[str, GPostRetryPlan]] = None,
) -> Optional[GPostRetryPlan]:
    """task_id 에 대한 plan — 없으면 None."""
    table = plans if plans is not None else load_gpost_plans()
    return table.get(task_id)


def run_gpost_eye_verify(
    *,
    task_id: str,
    evaluate: EvaluateFn,
    retry_fn: Optional[RetryFn],
    sleep_fn: SleepFn,
    plan: Optional[GPostRetryPlan] = None,
) -> GPostVerifyResult:
    """
    G-POST retry 실행 검증 루프.

    1. ``evaluate()`` → (passed, snapshot)
    2. 실패 + plan 있으면 ``retry_fn`` + ``extra_wait_sec`` sleep 후 1회 재평가
    3. 최종 실패 시 ``plan.fail_code`` (없으면 E_VERIFY_PEAK)
    """
    resolved = plan or get_gpost_plan(task_id)
    passed, snapshot = evaluate()
    if passed:
        return GPostVerifyResult(
            task_id=task_id,
            passed=True,
            probe_snapshot={**snapshot, "gpost_retried": False},
            detail="ok",
        )

    if resolved is None or retry_fn is None:
        return GPostVerifyResult(
            task_id=task_id,
            passed=False,
            fail_code=resolved.fail_code if resolved else "E_VERIFY_PEAK",
            probe_snapshot={**snapshot, "gpost_retried": False},
            detail=f"TASK {task_id} failed (no retry)",
        )

    retry_fn()
    if resolved.extra_wait_sec > 0:
        sleep_fn(resolved.extra_wait_sec)

    passed2, snapshot2 = evaluate()
    merged = {
        **snapshot,
        **snapshot2,
        "gpost_retried": True,
        "gpost_retry_atom": resolved.retry_atom_id,
        "gpost_extra_wait_sec": resolved.extra_wait_sec,
    }
    if passed2:
        return GPostVerifyResult(
            task_id=task_id,
            passed=True,
            retried=True,
            probe_snapshot=merged,
            detail="ok after gpost retry",
        )

    return GPostVerifyResult(
        task_id=task_id,
        passed=False,
        retried=True,
        fail_code=resolved.fail_code,
        probe_snapshot=merged,
        detail=f"TASK {task_id} failed after gpost retry",
    )


def validate_gpost_plans(plans: Dict[str, GPostRetryPlan]) -> List[str]:
    """정적 검증 — 필수 TASK 3건·retry_atom_id."""
    errors: List[str] = []
    for required in _BUILTIN_GPOST_PLANS:
        if required not in plans:
            errors.append(f"missing g_post_retry task: {required}")
    for task_id, plan in plans.items():
        if not plan.retry_atom_id and plan.extra_wait_sec <= 0:
            errors.append(f"{task_id}: need retry_atom_id or extra_wait_sec")
    return errors
