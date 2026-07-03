# -*- coding: utf-8
"""P21 — operational env cutover (SKIP_ORIGIN=0 · production flags)."""

from __future__ import annotations

import os
import re
import shutil
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from data_pc_origin.p14_runtime_bridge import ORIGIN_PIPELINE_ENV
from data_pc_origin.p16_watch_bridge import LEGACY_WATCH_ENV
from data_pc_origin.p17_env_config import SKIP_ORIGIN_ENV, read_env_file_keys
from data_pc_origin.p20_readiness import build_readiness_manifest

CUTOVER_APPLY_ENV = "DATA_PC_CUTOVER_APPLY"
ENV_FILENAME = "gc_automation.env"

PRODUCTION_CUTOVER: Dict[str, str] = {
    ORIGIN_PIPELINE_ENV: "1",
    SKIP_ORIGIN_ENV: "0",
    LEGACY_WATCH_ENV: "0",
}


@dataclass
class CutoverPlan:
    env_path: str
    backup_path: str
    changes: List[Dict[str, str]] = field(default_factory=list)
    already_production: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return {
            "env_path": self.env_path,
            "backup_path": self.backup_path,
            "changes": list(self.changes),
            "already_production": self.already_production,
        }


def env_file_path(script_dir: str) -> str:
    return str(Path(script_dir) / ENV_FILENAME)


def backup_env_path(script_dir: str) -> str:
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    for sub in ("KCH/processed", "KCH"):
        folder = Path(script_dir) / sub.replace("/", os.sep)
        if folder.is_dir():
            return str(folder / f"gc_automation.env.backup-{stamp}")
    return str(Path(script_dir) / f"gc_automation.env.backup-{stamp}")


def _is_production_value(key: str, value: str) -> bool:
    target = PRODUCTION_CUTOVER.get(key)
    if target is None:
        return True
    v = value.strip()
    if key == LEGACY_WATCH_ENV and not v:
        return target == "0"
    return v == target


def _cutover_target(key: str, current: str) -> Optional[str]:
    """변경 필요 시 목표값, 이미 production이면 None."""
    target = PRODUCTION_CUTOVER.get(key)
    if target is None:
        return None
    if _is_production_value(key, current):
        return None
    return target


def plan_cutover(script_dir: str) -> CutoverPlan:
    """현재 env → production 목표 diff."""
    path = env_file_path(script_dir)
    present = read_env_file_keys(path)
    changes: List[Dict[str, str]] = []

    for key in PRODUCTION_CUTOVER:
        current = present.get(key, "")
        target = _cutover_target(key, current)
        if target is not None:
            changes.append({"key": key, "from": current or "(unset)", "to": target})

    already = not changes
    return CutoverPlan(
        env_path=path,
        backup_path=backup_env_path(script_dir),
        changes=changes,
        already_production=already,
    )


def _set_or_replace_line(text: str, key: str, value: str) -> str:
    pattern = re.compile(rf"^{re.escape(key)}=.*$", re.MULTILINE)
    line = f"{key}={value}"
    if pattern.search(text):
        return pattern.sub(line, text)
    return text.rstrip() + f"\n{line}\n"


def apply_cutover(
    script_dir: str,
    *,
    backup: bool = True,
) -> CutoverPlan:
    """production env 적용 — 백업 후 키 갱신."""
    plan = plan_cutover(script_dir)
    if plan.already_production:
        return plan

    src = Path(plan.env_path)
    if not src.is_file():
        raise FileNotFoundError(plan.env_path)

    if backup:
        shutil.copy2(src, plan.backup_path)

    text = src.read_text(encoding="utf-8")
    for ch in plan.changes:
        text = _set_or_replace_line(text, ch["key"], ch["to"])
    src.write_text(text, encoding="utf-8")
    return plan


def cutover_apply_enabled(environ: Optional[Dict[str, str]] = None) -> bool:
    env = environ if environ is not None else os.environ
    return env.get(CUTOVER_APPLY_ENV, "").strip().lower() in ("1", "true", "yes", "on")


def assess_cutover_readiness(script_dir: str) -> Dict[str, Any]:
    """cutover plan + P20 manifest."""
    plan = plan_cutover(script_dir)
    manifest = build_readiness_manifest(script_dir)
    return {
        "plan": plan.to_dict(),
        "manifest": manifest.to_dict(),
        "full_e2e_ready": manifest.full_e2e_ready,
    }


def validate_cutover_artifact(payload: Dict[str, Any]) -> bool:
    if payload.get("status") not in ("ok", "skipped"):
        return False
    if "before" not in payload:
        return False
    before = payload["before"]
    if "plan" not in before or "manifest" not in before:
        return False
    if payload.get("mode") == "apply" and payload.get("status") == "ok":
        after = payload.get("after", {})
        if "full_e2e_ready" not in after:
            return False
    return True
