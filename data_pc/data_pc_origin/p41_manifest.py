# -*- coding: utf-8 -*-
"""P41 — O층 정렬 후 스택 manifest (게이트 수·브리지 모듈 검증)."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List

from data_pc_origin.gates.registry import (
    O0_IMPLEMENTATION_ORDER,
    O6_G_GATES,
    O6_IMPLEMENTATION_ORDER,
    P40_EXTENDED_ORDER,
    rollup_gate_ids,
)

# O0-C-04 + O0-I-03 + O6-G 추가 이후 기대 O 층 게이트 수
_EXPECTED_O0 = 71
_EXPECTED_O6 = 22
_EXPECTED_O6_G = 4
# P40-EXT(P층 누적) + P41(8) = 310
_MIN_P40_EXT = 302


@dataclass
class StackManifestPlan:
    ready: bool
    reason: str
    stack_gate_count: int
    p40_extended_gate_count: int
    p41_extended_gate_count: int
    o0_gate_count: int
    o6_gate_count: int
    o6_g_gate_count: int
    checks: List[str] = field(default_factory=list)
    failures: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "ready": self.ready,
            "reason": self.reason,
            "stack_gate_count": self.stack_gate_count,
            "p40_extended_gate_count": self.p40_extended_gate_count,
            "p41_extended_gate_count": self.p41_extended_gate_count,
            "o0_gate_count": self.o0_gate_count,
            "o6_gate_count": self.o6_gate_count,
            "o6_g_gate_count": self.o6_g_gate_count,
            "checks": list(self.checks),
            "failures": list(self.failures),
        }


def _bridge_modules_ok(script_dir: str) -> tuple[bool, List[str]]:
    """촉매↔O0/O6 브리지 파일 존재 — 운영·repo 동기화 확인."""
    root = Path(script_dir)
    names = (
        "data_pc_origin/catalyst_identity_bridge.py",
        "data_pc_origin/catalyst_o6_bridge.py",
    )
    missing = [n for n in names if not (root / n).is_file()]
    return not missing, missing


def plan_stack_manifest_post40(script_dir: str) -> StackManifestPlan:
    """P40 PASS 이후 O층 정렬·게이트 수 manifest (P41-M)."""
    stack_count = len(rollup_gate_ids("P40"))
    p40_ext = len(P40_EXTENDED_ORDER)
    p41_ext = p40_ext + 8  # P41_IMPLEMENTATION_ORDER
    o0_n = len(O0_IMPLEMENTATION_ORDER)
    o6_n = len(O6_IMPLEMENTATION_ORDER)
    o6_g_n = len(O6_G_GATES)

    checks: List[str] = []
    failures: List[str] = []

    if stack_count >= _MIN_P40_EXT:
        checks.append("stack_gate_count")
    else:
        failures.append(f"stack={stack_count}")

    if p40_ext >= _MIN_P40_EXT:
        checks.append("p40_extended")
    else:
        failures.append(f"p40_ext={p40_ext}")

    if o0_n == _EXPECTED_O0:
        checks.append("o0_count")
    else:
        failures.append(f"o0={o0_n} want {_EXPECTED_O0}")

    if o6_n == _EXPECTED_O6:
        checks.append("o6_count")
    else:
        failures.append(f"o6={o6_n} want {_EXPECTED_O6}")

    if o6_g_n == _EXPECTED_O6_G:
        checks.append("o6_g_count")
    else:
        failures.append(f"o6_g={o6_g_n} want {_EXPECTED_O6_G}")

    bridges_ok, missing = _bridge_modules_ok(script_dir)
    if bridges_ok:
        checks.append("catalyst_bridges")
    else:
        failures.append(f"missing:{','.join(missing)}")

    ready = not failures
    return StackManifestPlan(
        ready=ready,
        reason="stack_manifest_ready" if ready else "; ".join(failures),
        stack_gate_count=stack_count,
        p40_extended_gate_count=p40_ext,
        p41_extended_gate_count=p41_ext,
        o0_gate_count=o0_n,
        o6_gate_count=o6_n,
        o6_g_gate_count=o6_g_n,
        checks=checks,
        failures=failures,
    )


def validate_stack_manifest_artifact(payload: Dict[str, Any]) -> bool:
    if payload.get("status") not in ("ok", "partial"):
        return False
    plan = payload.get("plan")
    if not isinstance(plan, dict):
        return False
    return (
        plan.get("stack_gate_count", 0) >= _MIN_P40_EXT
        and plan.get("o0_gate_count") == _EXPECTED_O0
        and "catalyst_bridges" in (plan.get("checks") or [])
    )
