# -*- coding: utf-8 -*-
"""
gc1_runtime.layer0_blocked — PART6 BLOCKED -> agent_queue_state (T96)

설계: ``deploy/GC1_RUNTIME_DESIGN_PART6_RETRY.md`` BLOCKED 절
데이터: ``deploy/gc1_blocked_policy.json``
Hook: ``.cursor/hooks/agent_queue_lib.py`` — ``status=blocked`` 이면 followup 없음

에이전트·스크립트가 실장비·Origin·G: 등 **사람 개입**이 필요할 때
``apply_agent_queue_blocked()`` 로 상태 파일만 갱신 (코드 큐 자동 진행 중단).
"""
from __future__ import annotations

import json
import os
import re
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Mapping, Optional

_REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEFAULT_BLOCKED_POLICY_PATH = os.path.join(_REPO_ROOT, "deploy", "gc1_blocked_policy.json")
DEFAULT_AGENT_QUEUE_STATE_PATH = os.path.join(_REPO_ROOT, ".cursor", "agent_queue_state.json")

_BUILTIN_RULES: tuple[tuple[str, str, str], ...] = (
    ("autochro_live_ui", "Autochro 실장비 UI 필요", "Autochro 창을 열고 force 또는 8.3b"),
    ("origin_gui", "Origin GUI 필요", "은규 PC Origin 실행 후 4단계"),
    ("gdrive_secuyou", "G: SecuYou 수동 unlock", "SecuYouSB 로그인"),
    ("user_credential", "사용자 비밀번호 입력 필요", "env·앱비밀번호 사람 입력"),
)

_CODE_RX = re.compile(r"^[a-z][a-z0-9_]{2,48}$")


class BlockedHookStatus(str, Enum):
    """Hook 이 인식하는 agent_queue status."""

    BLOCKED = "blocked"


@dataclass(frozen=True)
class BlockedRule:
    """정책 1행 — blocked 사유 코드."""

    code: str
    description: str
    operator_hint: str = ""
    tower: str = ""
    step_ref: str = ""


@dataclass
class BlockedPolicyDocument:
    schema_version: int
    hook_status: str
    rules: List[BlockedRule]


@dataclass
class BlockedValidationResult:
    ok: bool
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)


@dataclass(frozen=True)
class BlockedApplyResult:
    """``apply_agent_queue_blocked`` 반환."""

    ok: bool
    code: str
    state_path: str
    state: Dict[str, Any]
    message: str


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def load_blocked_policy(path: str = DEFAULT_BLOCKED_POLICY_PATH) -> BlockedPolicyDocument:
    """JSON -> ``BlockedPolicyDocument``. 파일 없으면 내장 4규칙."""
    if not os.path.isfile(path):
        return BlockedPolicyDocument(
            schema_version=1,
            hook_status=BlockedHookStatus.BLOCKED.value,
            rules=[
                BlockedRule(code=c, description=d, operator_hint=h)
                for c, d, h in _BUILTIN_RULES
            ],
        )
    with open(path, encoding="utf-8") as fh:
        raw = json.load(fh)
    rules: List[BlockedRule] = []
    seen: set[str] = set()
    for item in raw.get("rules") or []:
        code = str(item.get("code", "")).strip()
        if not code:
            continue
        if code in seen:
            raise ValueError(f"duplicate blocked code: {code}")
        seen.add(code)
        rules.append(
            BlockedRule(
                code=code,
                description=str(item.get("description", "")),
                operator_hint=str(item.get("operator_hint", "")),
                tower=str(item.get("tower", "")),
                step_ref=str(item.get("step_ref", "")),
            )
        )
    return BlockedPolicyDocument(
        schema_version=int(raw.get("schema_version", 1)),
        hook_status=str(raw.get("hook_status", BlockedHookStatus.BLOCKED.value)),
        rules=rules,
    )


def validate_blocked_policy(doc: BlockedPolicyDocument) -> BlockedValidationResult:
    """정적 검증 — 코드 형식·중복·hook_status."""
    errors: List[str] = []
    warnings: List[str] = []
    if doc.hook_status != BlockedHookStatus.BLOCKED.value:
        errors.append(f"hook_status must be 'blocked', got {doc.hook_status!r}")
    if not doc.rules:
        errors.append("rules empty")
    codes: set[str] = set()
    for rule in doc.rules:
        if rule.code in codes:
            errors.append(f"duplicate code: {rule.code}")
        codes.add(rule.code)
        if not _CODE_RX.match(rule.code):
            errors.append(f"invalid code format: {rule.code!r}")
        if not rule.description.strip():
            warnings.append(f"empty description: {rule.code}")
    return BlockedValidationResult(ok=not errors, errors=errors, warnings=warnings)


def find_blocked_rule(
    code: str,
    doc: BlockedPolicyDocument,
) -> Optional[BlockedRule]:
    key = (code or "").strip().lower()
    for rule in doc.rules:
        if rule.code == key:
            return rule
    return None


def build_agent_queue_blocked_patch(
    rule: BlockedRule,
    *,
    last_task: str = "",
    armed: bool = True,
    hook_status: str = BlockedHookStatus.BLOCKED.value,
) -> Dict[str, Any]:
    """
    ``agent_queue_state.json`` 에 merge 할 필드.

    ``armed`` 기본 True — 큐 세션 중 사람 개입 대기.
    ``request_quit_cursor`` False — blocked 는 Cursor 종료 요청 안 함.
    """
    patch: Dict[str, Any] = {
        "armed": bool(armed),
        "status": hook_status,
        "request_quit_cursor": False,
        "blocked_code": rule.code,
        "blocked_reason": rule.description,
        "operator_hint": rule.operator_hint,
        "updated": _utc_now_iso(),
    }
    if last_task:
        patch["last_task"] = last_task
    if rule.step_ref:
        patch["blocked_step_ref"] = rule.step_ref
    return patch


def merge_agent_queue_state(
    existing: Optional[Mapping[str, Any]],
    patch: Mapping[str, Any],
) -> Dict[str, Any]:
    """기존 상태 위에 blocked patch 병합."""
    merged = dict(existing or {})
    merged.update(patch)
    return merged


def read_agent_queue_state(path: str) -> Optional[Dict[str, Any]]:
    if not os.path.isfile(path):
        return None
    try:
        with open(path, encoding="utf-8-sig") as fh:
            return json.load(fh)
    except (json.JSONDecodeError, OSError):
        return None


def write_agent_queue_state(path: str, state: Mapping[str, Any]) -> None:
    folder = os.path.dirname(path)
    if folder:
        os.makedirs(folder, exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(state, fh, ensure_ascii=False, indent=2)
        fh.write("\n")


def apply_agent_queue_blocked(
    code: str,
    *,
    policy_path: str = DEFAULT_BLOCKED_POLICY_PATH,
    state_path: str = DEFAULT_AGENT_QUEUE_STATE_PATH,
    last_task: str = "",
    armed: bool = True,
    dry_run: bool = False,
) -> BlockedApplyResult:
    """
    blocked 정책 조회 후 agent_queue_state 갱신.

    ``dry_run=True`` 이면 파일 쓰지 않고 patch 만 반환.
    """
    doc = load_blocked_policy(policy_path)
    validation = validate_blocked_policy(doc)
    if not validation.ok:
        return BlockedApplyResult(
            ok=False,
            code=code,
            state_path=state_path,
            state={},
            message="; ".join(validation.errors),
        )
    rule = find_blocked_rule(code, doc)
    if rule is None:
        known = ", ".join(r.code for r in doc.rules)
        return BlockedApplyResult(
            ok=False,
            code=code,
            state_path=state_path,
            state={},
            message=f"unknown blocked code {code!r} (known: {known})",
        )
    existing = read_agent_queue_state(state_path)
    patch = build_agent_queue_blocked_patch(
        rule,
        last_task=last_task,
        armed=armed,
        hook_status=doc.hook_status,
    )
    merged = merge_agent_queue_state(existing, patch)
    if not dry_run:
        write_agent_queue_state(state_path, merged)
    return BlockedApplyResult(
        ok=True,
        code=rule.code,
        state_path=state_path,
        state=merged,
        message=rule.operator_hint or rule.description,
    )


_KEYWORD_TO_CODE: tuple[tuple[str, str], ...] = (
    ("autochro", "autochro_live_ui"),
    ("origin", "origin_gui"),
    ("originpro", "origin_gui"),
    ("secuyou", "gdrive_secuyou"),
    ("g:\\", "gdrive_secuyou"),
    ("password", "user_credential"),
    ("credential", "user_credential"),
)


def infer_blocked_code_from_text(text: str) -> Optional[str]:
    """
    운영 메시지에서 blocked 코드 추론 (휴리스틱).

    확실하지 않으면 None — 명시 code 사용 권장.
    """
    blob = (text or "").lower()
    if not blob:
        return None
    for keyword, code in _KEYWORD_TO_CODE:
        if keyword in blob:
            return code
    return None


def is_hook_followup_suppressed(state: Mapping[str, Any]) -> bool:
    """``agent_queue_lib.evaluate_stop`` 과 동일 — blocked/complete 면 followup 없음."""
    return str(state.get("status", "")) in ("complete", "blocked")
