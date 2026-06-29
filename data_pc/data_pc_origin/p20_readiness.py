# -*- coding: utf-8
"""P20 — production stack readiness manifest (P14–P19 rollup)."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from data_pc_origin.p14_runtime_bridge import origin_pipeline_enabled, resolve_job_pipeline
from data_pc_origin.p16_watch_bridge import describe_watch_mode, should_use_runtime_watch
from data_pc_origin.p17_env_config import effective_origin_config, load_script_env
from data_pc_origin.p18_production_e2e import PRODUCTION_STACK, prepare_production_e2e
from data_pc_origin.p19_live_assert import assert_no_secrets


@dataclass
class ReadinessManifest:
    ready: bool
    reason: str
    stack: str
    full_e2e_ready: bool
    layers: Dict[str, Any] = field(default_factory=dict)
    checks: List[str] = field(default_factory=list)
    failures: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "ready": self.ready,
            "reason": self.reason,
            "stack": self.stack,
            "full_e2e_ready": self.full_e2e_ready,
            "layers": dict(self.layers),
            "checks": list(self.checks),
            "failures": list(self.failures),
        }


def _runtime_bridge_ok(script_dir: str) -> tuple[bool, str]:
    try:
        cb = resolve_job_pipeline(
            script_dir,
            environ={"DATA_PC_ORIGIN_PIPELINE": "1", "DATA_PC_LEGACY_WATCH": "0"},
        )
        if callable(cb):
            return True, "resolve_job_pipeline"
    except Exception as exc:  # noqa: BLE001
        return False, f"{type(exc).__name__}: {exc}"
    return False, "not callable"


def build_readiness_manifest(
    script_dir: str,
    *,
    dry_tick: bool = False,
    environ: Optional[Dict[str, str]] = None,
) -> ReadinessManifest:
    """P14–P19 wiring + infra prep → single manifest."""
    load_script_env(script_dir)
    env = effective_origin_config(script_dir, environ=environ)
    e2e = prepare_production_e2e(script_dir, environ=environ)
    watch_mode = describe_watch_mode(environ if environ is not None else None)
    runtime_watch = should_use_runtime_watch(environ)

    checks: List[str] = []
    failures: List[str] = []
    layers: Dict[str, Any] = {
        "env": {
            "origin_pipeline": env["origin_pipeline"],
            "watch_mode": env["watch_mode"],
            "skip_origin": env["skip_origin"],
            "full_e2e_ready": env["full_e2e_ready"],
        },
        "production_e2e": e2e.to_dict(),
        "watch": {"runtime_watch": runtime_watch, "mode": watch_mode},
    }

    if env["origin_pipeline"]:
        checks.append("origin_pipeline")
    else:
        failures.append("DATA_PC_ORIGIN_PIPELINE off")

    if runtime_watch and watch_mode == "runtime_origin":
        checks.append("watch_runtime_origin")
    elif runtime_watch:
        checks.append(f"watch={watch_mode}")
    else:
        failures.append("legacy watch path")

    bridge_ok, bridge_detail = _runtime_bridge_ok(script_dir)
    layers["runtime_bridge"] = {"ok": bridge_ok, "detail": bridge_detail}
    if bridge_ok:
        checks.append("runtime_bridge")
    else:
        failures.append(f"runtime_bridge: {bridge_detail}")

    if e2e.imap_ready:
        checks.append("imap_ready")
    else:
        failures.append("IMAP not ready")

    if e2e.g_drive_ok:
        checks.append("g_drive_ok")
    else:
        failures.append("G: unavailable")

    if e2e.originpro_import_ok:
        checks.append("originpro_ok")
    else:
        failures.append("originpro import failed")

    if dry_tick:
        try:
            from data_pc_origin.live_supervisor import build_dry_supervisor_tick

            tick, storage = build_dry_supervisor_tick(
                script_dir,
                origin_pipeline=True,
                dry_run_pipeline=True,
            )
            layers["supervisor_tick"] = {"ok": True, "status_code": tick["status_code"]}
            checks.append("supervisor_dry_tick")
        except Exception as exc:  # noqa: BLE001
            layers["supervisor_tick"] = {"ok": False, "error": str(exc)}
            failures.append(f"supervisor_tick: {exc}")

    stack_ready = not failures
    full_e2e = bool(env["full_e2e_ready"]) and e2e.g_drive_ok and e2e.originpro_import_ok

    return ReadinessManifest(
        ready=stack_ready,
        reason="ready" if stack_ready else "; ".join(failures),
        stack=PRODUCTION_STACK,
        full_e2e_ready=full_e2e,
        layers=layers,
        checks=checks,
        failures=failures,
    )


def validate_readiness_artifact(payload: Dict[str, Any]) -> bool:
    """Artifact schema + no secrets."""
    import json

    if not assert_no_secrets(json.dumps(payload, ensure_ascii=False)):
        return False
    manifest = payload.get("manifest")
    if not isinstance(manifest, dict):
        return False
    return "ready" in manifest and "layers" in manifest
