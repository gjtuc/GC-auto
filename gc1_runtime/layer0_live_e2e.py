# -*- coding: utf-8 -*-
"""
gc1_runtime.layer0_live_e2e — Step 8.3a/8.3b 실장비 E2E 계획 (T97)

8.3d (``run_gc1_runtime_e2e.py``) 와 구분:
  · 8.3d = ``AUTOCHRO_DRY_RUN=1`` + unittest mock, **Autochro·메일 없음**
  · 8.3b = ``AUTOCHRO_DRY_RUN=0`` + ``gc_automation.py --force``, **실 UI·SMTP**

8.3a = 8.3b 와 동일하나 ``--no-email`` (엑셀만).

본 모듈은 **실행 계획·사전조건 판정** 만 담당. 실제 subprocess 는
``scripts/run_gc1_step8_live.py`` 가 수행.
"""
from __future__ import annotations

import os
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Mapping, Optional, Sequence

# TYPE_CHECKING avoid circular - IdentSnapshot from layer0_ident at runtime


class Step83Mode(str, Enum):
    """Step 8.3 하위 단계."""

    EXCEL_ONLY = "8.3a"
    MAIL = "8.3b"


@dataclass(frozen=True)
class LiveE2ePlan:
    """한 번의 live E2E 실행 계획."""

    step_ref: str
    mode: Step83Mode
    description: str
    env: Dict[str, str]
    argv: List[str]
    requires_hotspot: bool
    requires_autochro_ui: bool
    contrasts_with: str = "8.3d"
    use_runtime: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return {
            "step_ref": self.step_ref,
            "mode": self.mode.value,
            "description": self.description,
            "env": self.env,
            "argv": self.argv,
            "requires_hotspot": self.requires_hotspot,
            "requires_autochro_ui": self.requires_autochro_ui,
            "contrasts_with": self.contrasts_with,
            "use_runtime": self.use_runtime,
        }


@dataclass
class LivePreflightResult:
    """사전조건 검사 — hardware 없이 실행 가능."""

    ok: bool
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {"ok": self.ok, "errors": self.errors, "warnings": self.warnings}


def _truthy_env(name: str, default: str = "0") -> str:
    return os.getenv(name, default).strip() or default


def build_live_e2e_env(
    *,
    use_runtime: bool,
    dry_run: bool = False,
) -> Dict[str, str]:
    """
    live Autochro subprocess 에 merge 할 env.

    ``dry_run=False`` -> ``AUTOCHRO_DRY_RUN=0`` (실 UI).
    """
    env: Dict[str, str] = {
        "AUTOCHRO_DRY_RUN": "1" if dry_run else "0",
        "AUTOCHRO_ENABLED": "1",
    }
    if use_runtime:
        env["GC1_USE_RUNTIME"] = "1"
    else:
        env["GC1_USE_RUNTIME"] = "0"
    # prep 기본 켜기 (환경에 이미 있으면 subprocess 가 OS env 우선)
    if not _truthy_env("GC1_AUTOCHRO_PREP_STEPS", ""):
        env.setdefault("GC1_AUTOCHRO_PREP_STEPS", "1")
    return env


def build_live_e2e_argv(
    repo_root: str,
    mode: Step83Mode,
) -> List[str]:
    """``gc_automation.py`` argv — python 실행 파일은 호출 측이 붙임."""
    script = os.path.join(os.path.normpath(repo_root), "gc_automation.py")
    argv = [script, "--force"]
    if mode is Step83Mode.EXCEL_ONLY:
        argv.append("--no-email")
    return argv


def build_live_e2e_plan(
    repo_root: str,
    mode: Step83Mode,
    *,
    use_runtime: bool = False,
) -> LiveE2ePlan:
    """8.3a 또는 8.3b 실행 계획 조립."""
    if mode is Step83Mode.EXCEL_ONLY:
        desc = "GC1 live E2E - excel only (--force --no-email)"
        hotspot = False
    else:
        desc = "GC1 live E2E - force + SMTP (iPhone hotspot)"
        hotspot = True
    return LiveE2ePlan(
        step_ref=mode.value,
        mode=mode,
        description=desc,
        env=build_live_e2e_env(use_runtime=use_runtime, dry_run=False),
        argv=build_live_e2e_argv(repo_root, mode),
        requires_hotspot=hotspot,
        requires_autochro_ui=True,
        use_runtime=use_runtime,
    )


def evaluate_live_preflight(
    ident: Mapping[str, Any],
    plan: LiveE2ePlan,
) -> LivePreflightResult:
    """
    IDENT 스냅샷 dict (``IdentSnapshot.to_dict()``) 기반 사전조건.

    메일·핫스팟·Autochro 창은 **경고** 만 (본 함수는 네트워크·UI probe 안 함).
    """
    errors: List[str] = []
    warnings: List[str] = []

    if not ident.get("repo_root_exists"):
        errors.append("repo root missing")
    if ident.get("is_not_data_pc") is False:
        errors.append("data_pc - gc_automation.py forbidden on 은규 PC")
    if not ident.get("is_gc1_instance"):
        errors.append("not GC1 instance profile")
    if not ident.get("is_gc1_mode"):
        errors.append("chemstation_mode is not gc1")
    if not ident.get("ok_for_gc1_autochro"):
        errors.append("IDENT ok_for_gc1_autochro is False")
    if not ident.get("gc1_env_exists"):
        warnings.append("Desktop gc_automation.env not found")

    if plan.env.get("AUTOCHRO_DRY_RUN") != "0":
        errors.append("AUTOCHRO_DRY_RUN must be 0 for live E2E (not 8.3d)")

    if plan.requires_autochro_ui:
        warnings.append("Autochro window must be open and unobstructed")
    if plan.requires_hotspot:
        warnings.append("iPhone hotspot required for SMTP (8.3b)")

    if plan.use_runtime:
        warnings.append("GC1_USE_RUNTIME=1 - runtime layer4_job live path")
    else:
        warnings.append("GC1_USE_RUNTIME=0 - legacy gc_autochro path (STEP8 default)")

    return LivePreflightResult(ok=not errors, errors=errors, warnings=warnings)


def contrast_with_83d(plan: LiveE2ePlan) -> Dict[str, str]:
    """8.3b vs 8.3d 차이 요약 (진단 JSON용)."""
    return {
        "this_step": plan.step_ref,
        "dry_run_step": plan.contrasts_with,
        "this_autochro_dry_run": plan.env.get("AUTOCHRO_DRY_RUN", "?"),
        "dry_run_expect": "AUTOCHRO_DRY_RUN=1 via run_gc1_runtime_e2e.py",
        "this_invokes": "gc_automation.py --force",
        "dry_run_invokes": "unittest test_gc1_runtime_e2e (mock)",
    }
