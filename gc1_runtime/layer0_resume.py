# -*- coding: utf-8 -*-
"""
gc1_runtime.layer0_resume — PART6 §Resume 정책 로드·검증 (T93)

설계: ``deploy/GC1_RUNTIME_DESIGN_PART6_RETRY.md`` §Resume
데이터: ``deploy/gc1_resume_policy.json``
실행: ``layer4_job.apply_resume_from`` 와 대조

정적: JSON·atom_id 유효성
실행: StateStore 에 skip 마킹 결과 검증 (unittest)
"""
from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from typing import List, Optional, Sequence, Set

_REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEFAULT_RESUME_POLICY_PATH = os.path.join(_REPO_ROOT, "deploy", "gc1_resume_policy.json")

_BUILTIN_RULES: tuple[tuple[str, str], ...] = (
    ("Ω.A.L4.P4.03", "P0-P3 ok, run from P4.03"),
    ("Ω.A.L4.P9.02", "P0-P8 ok, run P9 from P9.02"),
)


@dataclass(frozen=True)
class ResumeRule:
    """``resume_from`` 1행 — 이 atom 부터 재실행, 앞 atom 은 skip."""

    resume_from: str
    description: str = ""
    skip_phases: tuple[str, ...] = ()


@dataclass
class ResumePolicyDocument:
    schema_version: int
    rules: List[ResumeRule]


@dataclass
class ResumeValidationResult:
    ok: bool
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)


def load_resume_policy(path: str = DEFAULT_RESUME_POLICY_PATH) -> ResumePolicyDocument:
    """JSON → ``ResumePolicyDocument``."""
    if not os.path.isfile(path):
        return ResumePolicyDocument(
            schema_version=1,
            rules=[
                ResumeRule(resume_from=rf, description=desc)
                for rf, desc in _BUILTIN_RULES
            ],
        )
    with open(path, encoding="utf-8") as fh:
        raw = json.load(fh)
    rules: List[ResumeRule] = []
    seen: Set[str] = set()
    for item in raw.get("rules") or []:
        rf = str(item.get("resume_from", "")).strip()
        if not rf:
            continue
        if rf in seen:
            raise ValueError(f"duplicate resume_from: {rf}")
        seen.add(rf)
        phases = tuple(str(p) for p in (item.get("skip_phases") or []))
        rules.append(
            ResumeRule(
                resume_from=rf,
                description=str(item.get("description", "")),
                skip_phases=phases,
            )
        )
    return ResumePolicyDocument(
        schema_version=int(raw.get("schema_version", 1)),
        rules=rules,
    )


def atoms_before_resume(
    resume_from: str,
    atom_order: Sequence[str],
) -> tuple[str, ...]:
    """``resume_from`` 직전까지 atom_id (``apply_resume_from`` 와 동일)."""
    if resume_from not in atom_order:
        return ()
    idx = atom_order.index(resume_from)
    return tuple(atom_order[:idx])


def validate_resume_policy(
    doc: ResumePolicyDocument,
    atom_order: Optional[Sequence[str]] = None,
) -> ResumeValidationResult:
    """
    정책 검증 — ``resume_from`` 이 L4 atom 레지스트리에 존재하는지.

    ``skip_phases`` 는 문서용; 실행 검증은 unittest ``apply_resume_from``.
    """
    result = ResumeValidationResult(ok=True)
    if atom_order is None:
        from gc1_runtime.layer4_atoms_p8_p9 import P0_P9_ATOM_IDS

        atom_order = P0_P9_ATOM_IDS

    order_set = set(atom_order)
    for rule in doc.rules:
        if rule.resume_from not in order_set:
            result.errors.append(f"{rule.resume_from}: not in P0_P9_ATOM_IDS")
            result.ok = False
            continue
        if not atoms_before_resume(rule.resume_from, atom_order):
            result.warnings.append(f"{rule.resume_from}: no prior atoms to skip")

    for expected, _ in _BUILTIN_RULES:
        if not any(r.resume_from == expected for r in doc.rules):
            result.errors.append(f"missing builtin resume rule: {expected}")
            result.ok = False

    return result
