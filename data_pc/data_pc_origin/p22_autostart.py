# -*- coding: utf-8
"""P22 — autostart / watch bat·VBS integration smoke."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from data_pc_origin.p16_watch_bridge import (
    LEGACY_WATCH_ENV,
    describe_watch_mode,
    should_use_runtime_watch,
)
from data_pc_origin.p17_env_config import load_script_env

AUTOSTART_FILES: Dict[str, List[str]] = {
    "gc_data_pc_watch_loop.bat": ["data_pc_watchdog.py"],
    "gc_data_pc_ensure_watch.bat": ["gc_data_pc_ensure_watch_hidden.vbs"],
    "gc_data_pc_ensure_watch_hidden.vbs": ["data_pc_runtime", "ensure-once"],
    "gc_data_pc_start_watch_hidden.vbs": ["data_pc_runtime", "--script-dir"],
    "data_pc_watchdog.py": ["data_pc_runtime", "_redirect_to_runtime"],
    "data_pc_watch.py": ["run_watch_via_runtime", "should_use_runtime_watch"],
    "촉매 반응 계산.py": ["--watch", "run_data_pc_watch"],
}

LEGACY_FORBIDDEN: Dict[str, List[str]] = {
    "gc_data_pc_start_watch_hidden.vbs": ["data_pc_watch.py", "DataPcWatchRunner"],
    "gc_data_pc_ensure_watch_hidden.vbs": ["data_pc_watch.py", "DataPcWatchRunner"],
}


@dataclass
class AutostartCheck:
    name: str
    ok: bool
    detail: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {"name": self.name, "ok": self.ok, "detail": self.detail}


@dataclass
class AutostartManifest:
    ready: bool
    reason: str
    script_dir: str
    artifacts: Dict[str, bool] = field(default_factory=dict)
    checks: List[AutostartCheck] = field(default_factory=list)
    watch_mode: str = ""
    runtime_watch: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return {
            "ready": self.ready,
            "reason": self.reason,
            "script_dir": self.script_dir,
            "artifacts": dict(self.artifacts),
            "checks": [c.to_dict() for c in self.checks],
            "watch_mode": self.watch_mode,
            "runtime_watch": self.runtime_watch,
        }


def _read_text(path: Path) -> str:
    for enc in ("utf-8", "cp949", "latin-1"):
        try:
            return path.read_text(encoding=enc)
        except UnicodeDecodeError:
            continue
    return path.read_text(encoding="utf-8", errors="replace")


def _check_markers(text: str, markers: List[str]) -> Tuple[bool, str]:
    missing = [m for m in markers if m not in text]
    if missing:
        return False, f"missing: {', '.join(missing)}"
    return True, "ok"


def _check_forbidden(text: str, forbidden: List[str]) -> Tuple[bool, str]:
    found = [f for f in forbidden if f in text]
    if found:
        return False, f"legacy marker: {', '.join(found)}"
    return True, "ok"


def scan_autostart_artifact(script_dir: str, filename: str) -> AutostartCheck:
    path = Path(script_dir) / filename
    if not path.is_file():
        return AutostartCheck(name=filename, ok=False, detail="missing file")

    text = _read_text(path)
    ok, detail = _check_markers(text, AUTOSTART_FILES[filename])
    if ok and filename in LEGACY_FORBIDDEN:
        ok2, detail2 = _check_forbidden(text, LEGACY_FORBIDDEN[filename])
        if not ok2:
            ok, detail = ok2, detail2
    return AutostartCheck(name=filename, ok=ok, detail=detail)


def verify_watchdog_delegation(script_dir: str) -> AutostartCheck:
    path = Path(script_dir) / "data_pc_watchdog.py"
    if not path.is_file():
        return AutostartCheck(name="watchdog_delegation", ok=False, detail="missing watchdog")
    text = _read_text(path)
    if "_redirect_to_runtime" not in text:
        return AutostartCheck(name="watchdog_delegation", ok=False, detail="no _redirect_to_runtime")
    if not re.search(r"def main\(\).*?_redirect_to_runtime", text, re.DOTALL):
        return AutostartCheck(name="watchdog_delegation", ok=False, detail="main does not delegate")
    return AutostartCheck(name="watchdog_delegation", ok=True, detail="main → data_pc_runtime")


def verify_vbs_runtime_entry(script_dir: str) -> AutostartCheck:
    checks = [
        scan_autostart_artifact(script_dir, "gc_data_pc_start_watch_hidden.vbs"),
        scan_autostart_artifact(script_dir, "gc_data_pc_ensure_watch_hidden.vbs"),
    ]
    failed = [c for c in checks if not c.ok]
    if failed:
        return AutostartCheck(
            name="vbs_runtime_entry",
            ok=False,
            detail="; ".join(f"{c.name}: {c.detail}" for c in failed),
        )
    return AutostartCheck(name="vbs_runtime_entry", ok=True, detail="both VBS → data_pc_runtime")


def build_autostart_manifest(
    script_dir: str,
    *,
    environ: Optional[Dict[str, str]] = None,
) -> AutostartManifest:
    """bat/VBS/watchdog/--watch 체인 스캔."""
    load_script_env(script_dir)
    artifacts: Dict[str, bool] = {}
    checks: List[AutostartCheck] = []

    for filename in AUTOSTART_FILES:
        chk = scan_autostart_artifact(script_dir, filename)
        artifacts[filename] = chk.ok
        checks.append(chk)

    checks.append(verify_watchdog_delegation(script_dir))
    checks.append(verify_vbs_runtime_entry(script_dir))

    env = dict(environ or {})
    env.setdefault("DATA_PC_ORIGIN_PIPELINE", "1")
    env.setdefault(LEGACY_WATCH_ENV, "0")
    runtime_watch = should_use_runtime_watch(env)
    watch_mode = describe_watch_mode(env)

    chain_ok = runtime_watch and watch_mode == "runtime_origin"
    checks.append(
        AutostartCheck(
            name="origin_watch_chain",
            ok=chain_ok,
            detail=watch_mode if chain_ok else f"expected runtime_origin, got {watch_mode}",
        )
    )

    failures = [c for c in checks if not c.ok]
    ready = not failures
    return AutostartManifest(
        ready=ready,
        reason="ready" if ready else failures[0].name,
        script_dir=script_dir,
        artifacts=artifacts,
        checks=checks,
        watch_mode=watch_mode,
        runtime_watch=runtime_watch,
    )


def validate_autostart_artifact(payload: Dict[str, Any]) -> bool:
    if payload.get("status") != "ok":
        return False
    manifest = payload.get("manifest")
    if not isinstance(manifest, dict):
        return False
    if "ready" not in manifest or "checks" not in manifest:
        return False
    if not isinstance(manifest["checks"], list):
        return False
    return True
