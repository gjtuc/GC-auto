# -*- coding: utf-8 -*-
"""Phase 8 #154 — `DATA_PC_SKIP_ORIGIN=0` 경로 검증 (코드 + 실행).

#153(pipeline_bridge 위임) 다음 단계.
· **코드 검증**: O2 env · 촉매 `_skip_origin_enabled` · live prep 조건
· **실행 검증**: mock op 로 O9 `update_from_dataframe` 8 sheets (originpro 불필요)
· **live prep**: G: · originpro · opju — 실연동 차단 사유 기록 (COM live 는 #155)
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Mapping, Optional

from data_pc_origin.o2_env import SKIP_ORIGIN_ENV, origin_feature_enabled, skip_origin_active
from data_pc_origin.o8_fixtures import OPJU_FX, SAMPLE_JOB, fx_job_df_full, fx_job_op_full
from data_pc_origin.o9_facade import update_from_dataframe
from data_pc_origin.live_run import LIVE_OPJU_ENV, prepare_live_e2e, run_live_e2e
from data_pc_origin.p6_catalyst_adapter import default_catalyst_path, load_catalyst_module

ARTIFACT_NAME = "live_phase8_origin_result.json"
# fixture 실행 검증 시 기대 시트 수 (O8 job mock op)
_EXPECTED_SHEETS = 8
_EXPECTED_ROWS = 107


@dataclass
class Phase8OriginPlan:
    """SKIP_ORIGIN=0 일 때 Origin 경로가 열려 있는지 — 정적·env 검증."""

    ready: bool
    reason: str
    skip_origin_active: bool
    origin_feature_enabled: bool
    catalyst_skip_origin: bool
    pipeline_bridge_importable: bool
    checks: List[str] = field(default_factory=list)
    failures: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "ready": self.ready,
            "reason": self.reason,
            "skip_origin_active": self.skip_origin_active,
            "origin_feature_enabled": self.origin_feature_enabled,
            "catalyst_skip_origin": self.catalyst_skip_origin,
            "pipeline_bridge_importable": self.pipeline_bridge_importable,
            "checks": list(self.checks),
            "failures": list(self.failures),
        }


def _phase8_env(environ: Mapping[str, str] | None = None) -> Dict[str, str]:
    """검증용 env — Origin 활성 (`DATA_PC_SKIP_ORIGIN=0`)."""
    base = dict(os.environ)
    if environ:
        base.update(environ)
    base[SKIP_ORIGIN_ENV] = "0"
    return base


def plan_phase8_origin(*, environ: Mapping[str, str] | None = None) -> Phase8OriginPlan:
    """코드 검증 — O2·촉매·bridge 가 SKIP_ORIGIN=0 을 Origin 허용으로 해석."""
    env = _phase8_env(environ)
    checks: List[str] = []
    failures: List[str] = []

    skip = skip_origin_active(environ=env)
    origin_on = origin_feature_enabled(environ=env)

    if not skip:
        checks.append("o2_skip_origin_inactive")
    else:
        failures.append("o2:skip_origin_still_active")

    if origin_on:
        checks.append("o2_origin_feature_enabled")
    else:
        failures.append("o2:origin_feature_disabled")

    catalyst_skip = True
    try:
        path = default_catalyst_path()
        prior = os.environ.get(SKIP_ORIGIN_ENV)
        os.environ[SKIP_ORIGIN_ENV] = "0"
        try:
            mod = load_catalyst_module(path)
            fn = getattr(mod, "_skip_origin_enabled", None)
            if callable(fn):
                catalyst_skip = bool(fn())
                if not catalyst_skip:
                    checks.append("catalyst_skip_origin_false")
                else:
                    failures.append("catalyst:skip_origin_true")
            else:
                failures.append("catalyst:no _skip_origin_enabled")
        finally:
            if prior is None:
                os.environ.pop(SKIP_ORIGIN_ENV, None)
            else:
                os.environ[SKIP_ORIGIN_ENV] = prior
    except OSError as exc:
        failures.append(f"catalyst_load:{exc}")

    bridge_ok = False
    try:
        from data_pc_origin.pipeline_bridge import run_origin_update as _rou  # noqa: F401

        bridge_ok = callable(_rou)
        if bridge_ok:
            checks.append("pipeline_bridge_callable")
        else:
            failures.append("pipeline_bridge:not_callable")
    except ImportError as exc:
        failures.append(f"pipeline_bridge:{exc}")

    ready = not failures
    return Phase8OriginPlan(
        ready=ready,
        reason="phase8_origin_ready" if ready else "; ".join(failures),
        skip_origin_active=skip,
        origin_feature_enabled=origin_on,
        catalyst_skip_origin=catalyst_skip,
        pipeline_bridge_importable=bridge_ok,
        checks=checks,
        failures=failures,
    )


def verify_fixture_o9_e2e() -> Dict[str, Any]:
    """실행 검증 — mock op · fixture df 로 O9 facade 8 sheets (COM 없음)."""
    op, _ = fx_job_op_full()
    res = update_from_dataframe(
        OPJU_FX,
        fx_job_df_full(),
        SAMPLE_JOB,
        save_in_place=False,
        op=op,
        skip_gate=True,
        skip_equipment_day_guard=True,
        printer=lambda _m: None,
        log_fn=lambda _m: None,
    )
    ok = res.ok and res.sheets_updated >= _EXPECTED_SHEETS and res.row_count >= _EXPECTED_ROWS
    return {
        "ok": ok,
        "reason": "fixture_o9_ok" if ok else "fixture_o9_incomplete",
        "sheets_updated": res.sheets_updated,
        "row_count": res.row_count,
        "warning_codes": [w.code for w in res.warnings],
    }


def verify_pipeline_bridge_fixture() -> Dict[str, Any]:
    """실행 검증 — pipeline 경로와 동일 인자로 facade + mock op (COM 없음)."""
    op, _ = fx_job_op_full()

    def _job_runner(ctx, **kwargs):
        kwargs.setdefault("op", op)
        kwargs.setdefault("skip_gate", True)
        kwargs.setdefault("skip_equipment_day_guard", True)
        from data_pc_origin.o8_job import run_sample_job

        return run_sample_job(ctx, **kwargs)

    res = update_from_dataframe(
        OPJU_FX,
        fx_job_df_full(),
        SAMPLE_JOB,
        save_in_place=False,
        op=op,
        skip_gate=True,
        skip_equipment_day_guard=True,
        job_runner=_job_runner,
        printer=lambda _m: None,
        log_fn=lambda _m: None,
    )
    ok = res.ok and res.sheets_updated >= _EXPECTED_SHEETS
    return {
        "ok": ok,
        "reason": "bridge_fixture_ok" if ok else "bridge_fixture_incomplete",
        "sheets_updated": res.sheets_updated,
        "row_count": res.row_count,
        "via": "update_from_dataframe+job_runner",
    }


def validate_phase8_origin_artifact(payload: Dict[str, Any]) -> bool:
    """artifact 스키마 — plan + fixture 실행 결과."""
    if payload.get("status") not in ("ok", "partial"):
        return False
    plan = payload.get("plan")
    fixture = payload.get("fixture_o9")
    bridge = payload.get("bridge_fixture")
    if not isinstance(plan, dict) or not isinstance(fixture, dict) or not isinstance(bridge, dict):
        return False
    return (
        plan.get("ready") is True
        and plan.get("origin_feature_enabled") is True
        and fixture.get("ok") is True
        and fixture.get("sheets_updated", 0) >= _EXPECTED_SHEETS
        and bridge.get("ok") is True
    )


def run_live_phase8_origin(
    *,
    artifact_dir: Optional[Path] = None,
    opju_path: Optional[str] = None,
    try_live: bool = False,
) -> Dict[str, Any]:
    """Phase 8 #154 harness — plan + fixture 실행 + (선택) live prep/COM."""
    env = _phase8_env()
    prior_skip = os.environ.get(SKIP_ORIGIN_ENV)
    os.environ[SKIP_ORIGIN_ENV] = "0"
    try:
        plan = plan_phase8_origin(environ=env)
        fixture_o9 = verify_fixture_o9_e2e()
        bridge_fixture = verify_pipeline_bridge_fixture()

        live_prep = prepare_live_e2e(opju_path)
        live_result: Dict[str, Any] | None = None
        if try_live and live_prep.ready:
            live_result = run_live_e2e(
                opju_path or live_prep.opju_path,
                artifact_dir=artifact_dir,
                use_fixture=False,
                save_in_place=False,
            )
        elif try_live:
            live_result = {
                "status": "skipped",
                "reason": live_prep.reason,
                "prep": live_prep.to_dict(),
            }

        exec_ok = fixture_o9.get("ok") and bridge_fixture.get("ok")
        status = "ok" if plan.ready and exec_ok else "partial"
        out: Dict[str, Any] = {
            "status": status,
            "mode": "phase8_skip_origin_zero",
            "env": {SKIP_ORIGIN_ENV: "0"},
            "plan": plan.to_dict(),
            "fixture_o9": fixture_o9,
            "bridge_fixture": bridge_fixture,
            "live_prep": live_prep.to_dict(),
        }
        if live_result is not None:
            out["live_run"] = live_result
        out["live_tier"] = (
            "com_live" if live_result and live_result.get("status") == "ok" else "fixture_only"
        )
        out["artifact_valid"] = validate_phase8_origin_artifact(out)
    finally:
        if prior_skip is None:
            os.environ.pop(SKIP_ORIGIN_ENV, None)
        else:
            os.environ[SKIP_ORIGIN_ENV] = prior_skip

    root = artifact_dir or Path(__file__).resolve().parent
    path = root / ARTIFACT_NAME
    path.write_text(json.dumps(out, indent=2, ensure_ascii=False), encoding="utf-8")
    out["artifact"] = str(path)
    return out


def main() -> int:
    import argparse

    parser = argparse.ArgumentParser(description="Phase 8 #154 — SKIP_ORIGIN=0 검증")
    parser.add_argument("--try-live", action="store_true", help=f"G:·Origin 준비 시 COM live ({LIVE_OPJU_ENV})")
    parser.add_argument("opju", nargs="?", help="optional opju path")
    args = parser.parse_args()
    result = run_live_phase8_origin(opju_path=args.opju, try_live=args.try_live)
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0 if result.get("artifact_valid") else 1


if __name__ == "__main__":
    raise SystemExit(main())
