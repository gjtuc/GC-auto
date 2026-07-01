# -*- coding: utf-8 -*-
"""
gc1_runtime.layer0_retry — PART6 on_fail 정책 로드·L4 코드 대조 (T90)

설계: ``deploy/GC1_RUNTIME_DESIGN_PART6_RETRY.md`` §RETRY-Policy
데이터: ``deploy/gc1_atom_retry_policy.json``

정적: JSON 스키마·중복 atom_id 검사
실행: ``merge_l4_atom_specs()`` 와 max_attempt / fail_code / delay 대조

fallback_channel 은 ``AtomOnFail`` + ``layer4_atom_fallback`` (T92).
"""
from __future__ import annotations

import json
import os
import re
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Sequence

_REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEFAULT_RETRY_POLICY_PATH = os.path.join(_REPO_ROOT, "deploy", "gc1_atom_retry_policy.json")

_L4_ATOM_RE = re.compile(r"^Ω\.A\.L4\.P\d+\.\d{2}$")


@dataclass(frozen=True)
class RetryPolicyEntry:
    """PART6 표 1행 — tower A L4 atom on_fail."""

    atom_id: str
    max_attempt: int
    retry_delay_ms: Optional[int]
    fail_code: Optional[str]
    fallback_channel: Optional[str] = None
    delay_kind: str = "sleep"
    notes: str = ""

    @property
    def is_poll_delay(self) -> bool:
        return self.delay_kind == "poll"

    @property
    def has_retry(self) -> bool:
        return self.max_attempt > 1 or (
            self.retry_delay_ms is not None and self.retry_delay_ms > 0 and not self.is_poll_delay
        )


@dataclass
class RetryPolicyDocument:
    schema_version: int
    policies: List[RetryPolicyEntry]
    g_post_retry: List[dict[str, Any]] = field(default_factory=list)
    externals: List[dict[str, Any]] = field(default_factory=list)


@dataclass
class RetryValidationResult:
    ok: bool
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    checked: int = 0


def _parse_delay_ms(raw: Any) -> Optional[int]:
    if raw is None:
        return None
    if isinstance(raw, bool):
        return None
    if isinstance(raw, int):
        return raw
    if isinstance(raw, float):
        return int(raw)
    return None


def load_retry_policy(path: str = DEFAULT_RETRY_POLICY_PATH) -> RetryPolicyDocument:
    """JSON → ``RetryPolicyDocument`` (구문 검증)."""
    with open(path, encoding="utf-8") as fh:
        raw = json.load(fh)
    if "policies" not in raw or not isinstance(raw["policies"], list):
        raise ValueError(f"invalid retry policy (missing policies[]): {path}")

    policies: List[RetryPolicyEntry] = []
    seen: set[str] = set()
    for item in raw["policies"]:
        atom_id = str(item["atom_id"])
        if atom_id in seen:
            raise ValueError(f"duplicate atom_id in policy: {atom_id}")
        seen.add(atom_id)
        max_attempt = int(item.get("max_attempt", 1))
        policies.append(
            RetryPolicyEntry(
                atom_id=atom_id,
                max_attempt=max_attempt,
                retry_delay_ms=_parse_delay_ms(item.get("retry_delay_ms")),
                fail_code=item.get("fail_code") if item.get("fail_code") else None,
                fallback_channel=item.get("fallback_channel"),
                delay_kind=str(item.get("delay_kind", "sleep")),
                notes=str(item.get("notes", "")),
            )
        )

    return RetryPolicyDocument(
        schema_version=int(raw.get("schema_version", 1)),
        policies=policies,
        g_post_retry=list(raw.get("g_post_retry") or []),
        externals=list(raw.get("externals") or []),
    )


def merge_l4_atom_specs() -> Dict[str, Any]:
    """
    L4 모듈 ``*_ATOM_SPECS`` 병합 — 실행 검증 시 import.

    ``AtomSpec`` — ``on_fail.max_attempt``, ``on_fail.retry_delay_ms``, ``on_fail.code``.
    """
    from gc1_runtime.layer4_atoms_p0_p1 import ATOM_SPECS
    from gc1_runtime.layer4_atoms_p2_p3 import P2_P3_ATOM_SPECS
    from gc1_runtime.layer4_atoms_p4 import P4_ATOM_SPECS
    from gc1_runtime.layer4_atoms_p5_p7 import P5_P7_ATOM_SPECS
    from gc1_runtime.layer4_atoms_p8_p9 import P8_P9_ATOM_SPECS

    merged: Dict[str, Any] = {}
    for block in (ATOM_SPECS, P2_P3_ATOM_SPECS, P4_ATOM_SPECS, P5_P7_ATOM_SPECS, P8_P9_ATOM_SPECS):
        merged.update(block)
    return merged


def atoms_with_runtime_retry(specs: Dict[str, Any]) -> List[str]:
    """코드에서 max_attempt>1 또는 retry_delay_ms>0 인 atom_id."""
    out: List[str] = []
    for aid, spec in specs.items():
        on_fail = spec.on_fail
        if on_fail.max_attempt > 1 or on_fail.retry_delay_ms > 0:
            out.append(aid)
    return sorted(out)


def validate_retry_policy(
    doc: RetryPolicyDocument,
    specs: Optional[Dict[str, Any]] = None,
) -> RetryValidationResult:
    """
    정책 JSON ↔ L4 ``AtomSpec.on_fail`` 대조.

    - policies[] 각 행: atom 존재, max_attempt·fail_code 일치
    - retry_delay_ms: ``delay_kind=poll`` 이면 코드 delay 검사 생략
    - 코드에 retry 있는 L4 atom 은 policies[] 에 있어야 함
    """
    result = RetryValidationResult(ok=True)
    runtime = specs if specs is not None else merge_l4_atom_specs()
    from gc1_runtime.layer0_fallback import parse_fallback_channel

    policy_ids = {p.atom_id for p in doc.policies}
    for entry in doc.policies:
        if not _L4_ATOM_RE.match(entry.atom_id):
            result.warnings.append(f"{entry.atom_id}: not L4 atom id pattern (skipped code check)")
            continue

        spec = runtime.get(entry.atom_id)
        if spec is None:
            result.errors.append(f"{entry.atom_id}: missing in L4 ATOM_SPECS")
            result.ok = False
            continue

        result.checked += 1
        on_fail = spec.on_fail

        if on_fail.max_attempt != entry.max_attempt:
            result.errors.append(
                f"{entry.atom_id}: max_attempt policy={entry.max_attempt} code={on_fail.max_attempt}"
            )
            result.ok = False

        code_fail = on_fail.code or None
        if code_fail != entry.fail_code:
            result.errors.append(
                f"{entry.atom_id}: fail_code policy={entry.fail_code!r} code={code_fail!r}"
            )
            result.ok = False

        if not entry.is_poll_delay:
            expected_delay = entry.retry_delay_ms if entry.retry_delay_ms is not None else 0
            if on_fail.retry_delay_ms != expected_delay:
                result.errors.append(
                    f"{entry.atom_id}: retry_delay_ms policy={expected_delay} code={on_fail.retry_delay_ms}"
                )
                result.ok = False

        pol_fb = entry.fallback_channel or None
        code_fb = on_fail.fallback_channel or None
        if pol_fb or code_fb:
            if code_fb != pol_fb:
                result.errors.append(
                    f"{entry.atom_id}: fallback_channel policy={pol_fb!r} code={code_fb!r}"
                )
                result.ok = False
            elif pol_fb and not parse_fallback_channel(pol_fb):
                result.warnings.append(
                    f"{entry.atom_id}: fallback_channel not parseable: {pol_fb!r}"
                )

    # 역방향: 코드 retry atom 이 정책에 없으면 오류
    for aid in atoms_with_runtime_retry(runtime):
        if aid not in policy_ids:
            result.errors.append(f"{aid}: has retry in code but missing from policies[]")
            result.ok = False

    if not doc.g_post_retry:
        result.warnings.append("g_post_retry[] empty — eye verify table missing")
    else:
        try:
            from gc1_runtime.layer0_gpost import load_gpost_plans, validate_gpost_plans

            gpost = load_gpost_plans()
            for msg in validate_gpost_plans(gpost):
                result.errors.append(f"g_post: {msg}")
                result.ok = False
        except ImportError:
            result.warnings.append("layer0_gpost not available for g_post validation")

    return result
