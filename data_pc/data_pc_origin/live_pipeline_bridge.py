# -*- coding: utf-8 -*-
"""Phase 8 live harness — 촉매 `update_origin` → `pipeline_bridge` 실행 위임 검증.

코드 검증(O9-P mock)과 별도로, 실제 촉매 스크립트를 importlib 로 로드한 뒤
`run_origin_update` 호출 여부를 patch 로 확인한다.
"""

from __future__ import annotations

import inspect
import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional
from unittest import mock

from data_pc_origin.o8_fixtures import OPJU_FX, SAMPLE_JOB, fx_job_df_full
from data_pc_origin.o9_facade import OriginUpdateResult
from data_pc_origin.p6_catalyst_adapter import CatalystLoadError, default_catalyst_path, load_catalyst_module
from data_pc_origin.pipeline_bridge import run_origin_update

ARTIFACT_NAME = "live_pipeline_bridge_result.json"


@dataclass
class PipelineBridgePlan:
    """Phase 8 사전 조건 — 촉매 스크립트·위임 함수 존재."""

    ready: bool
    reason: str
    catalyst_path: str
    has_update_origin: bool
    delegates_to_bridge: bool
    checks: List[str] = field(default_factory=list)
    failures: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "ready": self.ready,
            "reason": self.reason,
            "catalyst_path": self.catalyst_path,
            "has_update_origin": self.has_update_origin,
            "delegates_to_bridge": self.delegates_to_bridge,
            "checks": list(self.checks),
            "failures": list(self.failures),
        }


def _update_origin_delegates_to_bridge(module: Any) -> bool:
    """소스·import 문자열 — `pipeline_bridge.run_origin_update` 위임 여부."""
    fn = getattr(module, "update_origin", None)
    if not callable(fn):
        return False
    try:
        src = inspect.getsource(fn)
    except (OSError, TypeError):
        return False
    return "pipeline_bridge" in src and "run_origin_update" in src


def plan_pipeline_bridge(script_dir: Optional[str] = None) -> PipelineBridgePlan:
    """촉매 스크립트 존재·update_origin 정의·bridge 위임(정적) 확인."""
    root = Path(script_dir or Path(__file__).resolve().parent.parent)
    catalyst = root / "촉매 반응 계산.py"
    checks: List[str] = []
    failures: List[str] = []

    if catalyst.is_file():
        checks.append("catalyst_script")
    else:
        failures.append(f"missing:{catalyst}")

    has_fn = False
    delegates = False
    if catalyst.is_file():
        try:
            mod = load_catalyst_module(catalyst)
            has_fn = callable(getattr(mod, "update_origin", None))
            if has_fn:
                checks.append("update_origin_callable")
            else:
                failures.append("no update_origin")
            delegates = _update_origin_delegates_to_bridge(mod)
            if delegates:
                checks.append("delegates_to_bridge")
            else:
                failures.append("update_origin not wired to pipeline_bridge")
        except CatalystLoadError as exc:
            failures.append(str(exc))

    ready = not failures
    return PipelineBridgePlan(
        ready=ready,
        reason="pipeline_bridge_ready" if ready else "; ".join(failures),
        catalyst_path=str(catalyst),
        has_update_origin=has_fn,
        delegates_to_bridge=delegates,
        checks=checks,
        failures=failures,
    )


def verify_catalyst_delegation(catalyst_path: Optional[Path] = None) -> Dict[str, Any]:
    """실행 검증 — patch `run_origin_update` 후 촉매 `update_origin` 1회 호출."""
    path = (catalyst_path or default_catalyst_path()).resolve()
    mod = load_catalyst_module(path)
    if not callable(getattr(mod, "update_origin", None)):
        return {"ok": False, "reason": "update_origin missing"}

    stub = OriginUpdateResult(
        ok=True,
        sheets_updated=8,
        row_count=107,
        warnings=(),
        opju_path=OPJU_FX,
        sample_name=SAMPLE_JOB,
    )
    with mock.patch(
        "data_pc_origin.pipeline_bridge.run_origin_update",
        return_value=stub,
    ) as spy:
        mod.update_origin(OPJU_FX, fx_job_df_full(), SAMPLE_JOB, save_in_place=True)
        called = spy.call_count == 1
        if not called:
            return {"ok": False, "reason": f"run_origin_update call_count={spy.call_count}"}
        args, kwargs = spy.call_args
        df_arg = args[1] if len(args) > 1 else kwargs.get("df_data")
        row_hint: int | None = None
        if df_arg is not None:
            cols = getattr(df_arg, "columns", None)
            if cols and hasattr(df_arg, "__getitem__"):
                series = df_arg[cols[0]]
                row_hint = len(series) if hasattr(series, "__len__") else None
        return {
            "ok": True,
            "reason": "delegation_ok",
            "opju_path": args[0] if args else kwargs.get("opju_path"),
            "sample_name": args[2] if len(args) > 2 else kwargs.get("sample_name"),
            "save_in_place": kwargs.get("save_in_place", args[3] if len(args) > 3 else None),
            "df_row_count": row_hint,
            "sheets_updated": stub.sheets_updated,
        }


def validate_pipeline_bridge_artifact(payload: Dict[str, Any]) -> bool:
    if payload.get("status") not in ("ok", "partial"):
        return False
    plan = payload.get("plan")
    delegation = payload.get("delegation")
    if not isinstance(plan, dict) or not isinstance(delegation, dict):
        return False
    return (
        plan.get("ready") is True
        and plan.get("delegates_to_bridge") is True
        and delegation.get("ok") is True
        and delegation.get("sheets_updated", 0) >= 1
    )


def run_live_pipeline_bridge(
    *,
    artifact_dir: Optional[Path] = None,
    script_dir: Optional[str] = None,
    run_fixture_bridge: bool = False,
) -> Dict[str, Any]:
    """Phase 8 harness — 정적 plan + 실행 위임 검증 (+ 선택 fixture mock bridge)."""
    root_dir = script_dir or str(Path(__file__).resolve().parent.parent)
    plan = plan_pipeline_bridge(root_dir)
    delegation: Dict[str, Any] = {"ok": False, "reason": "skipped"}

    if plan.ready:
        try:
            delegation = verify_catalyst_delegation(Path(plan.catalyst_path))
        except Exception as exc:  # noqa: BLE001 — harness artifact 에 기록
            delegation = {"ok": False, "reason": f"delegation_error:{exc}"}

    fixture: Dict[str, Any] | None = None
    if run_fixture_bridge:
        # pipeline_bridge 직접 1회 — Origin mock (O9-P 와 동일 fixture)
        with mock.patch(
            "data_pc_origin.pipeline_bridge.update_from_dataframe",
            return_value=OriginUpdateResult(
                ok=True,
                sheets_updated=8,
                row_count=107,
                warnings=(),
                opju_path=OPJU_FX,
                sample_name=SAMPLE_JOB,
            ),
        ):
            res = run_origin_update(OPJU_FX, fx_job_df_full(), SAMPLE_JOB)
        fixture = {"ok": res.ok, "sheets_updated": res.sheets_updated}

    status = "ok" if plan.ready and delegation.get("ok") else "partial"
    out: Dict[str, Any] = {
        "status": status,
        "mode": "pipeline_bridge",
        "plan": plan.to_dict(),
        "delegation": delegation,
    }
    if fixture is not None:
        out["fixture_bridge"] = fixture
    out["artifact_valid"] = validate_pipeline_bridge_artifact(out)

    root = artifact_dir or Path(__file__).resolve().parent
    path = root / ARTIFACT_NAME
    path.write_text(json.dumps(out, indent=2, ensure_ascii=False), encoding="utf-8")
    out["artifact"] = str(path)
    return out


def main() -> int:
    import argparse

    parser = argparse.ArgumentParser(description="Phase 8 — 촉매 ↔ pipeline_bridge 실행 검증")
    parser.add_argument("--fixture-bridge", action="store_true", help="run_origin_update mock 1회 추가")
    args = parser.parse_args()
    result = run_live_pipeline_bridge(run_fixture_bridge=args.fixture_bridge)
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0 if result.get("artifact_valid") else 1


if __name__ == "__main__":
    raise SystemExit(main())
