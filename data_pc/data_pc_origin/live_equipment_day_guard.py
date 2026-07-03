# -*- coding: utf-8 -*-
"""O6-G equipment-day 가드 — 실행 검증 하네스 (live Origin COM 없음).

코드 검증: test_o6_equipment_guard · O6-G gates.
실행 검증: 본 모듈이 시나리오별 artifact JSON 을 생성 — 터미널에서 직접 확인.

시나리오:
  1. O0 순수 평가 (same_date / left_ahead / next_day / diff_equipment)
  2. O6 resolve (차단 / confirm 허용)
  3. O9 facade (O8 job 경로 — guard warning vs 성공 기록)
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional

from data_pc_origin.o0_equipment_day import evaluate_equipment_day_guard
from data_pc_origin.o6_fixtures import MockWks
from data_pc_origin.o6_guard import OriginColumnGuardError
from data_pc_origin.o6_resolve import resolve_target_column
from data_pc_origin.o8_fixtures import (
    OCM_LEFT_COMMENT,
    OCM_NEW_NEXT_DAY,
    OCM_NEW_SAME_DAY,
    OPJU_FX,
    fx_job_df_full,
    fx_job_op_equipment_day_guard,
)
from data_pc_origin.o9_facade import update_from_dataframe

ARTIFACT_NAME = "live_equipment_day_guard_result.json"

# test_o6_equipment_guard 와 동일 상수 — 실행 artifact 재사용
_LEFT = OCM_LEFT_COMMENT
_NEW_SAME_DAY = OCM_NEW_SAME_DAY
_NEW_NEXT_DAY = OCM_NEW_NEXT_DAY
_NEW_OLDER = "20260619 DRE(1.5%)@600°C Ni5/Ce5/Al2O3_OCM 장비"
_LEFT_AHEAD = "20260625 DRE(1.5%)@600°C Ni5/Ce5/Al2O3_OCM 장비"
_LEFT_DRM = "20260620 DRE(1.5%)@600°C Ni5/Ce5/Al2O3_DRM 장비"


@dataclass
class ScenarioResult:
    layer: str
    name: str
    expect_confirm: bool
    needs_user_confirm: bool
    reason_code: str
    passed: bool
    ok: Optional[bool] = None
    detail: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


def _o0_scenarios() -> List[ScenarioResult]:
    """O0 evaluate — 순수 규칙 (worksheet 없음)."""
    cases = [
        ("same_date", _LEFT, _NEW_SAME_DAY, True, "same_date"),
        ("left_date_ahead", _LEFT_AHEAD, _NEW_OLDER, True, "left_date_ahead"),
        ("next_day_ok", _LEFT, _NEW_NEXT_DAY, False, "ok"),
        ("diff_equipment_ok", _LEFT_DRM, _NEW_SAME_DAY, False, ""),
    ]
    out: List[ScenarioResult] = []
    for name, left, new, expect_confirm, expect_code in cases:
        r = evaluate_equipment_day_guard(left, new)
        out.append(
            ScenarioResult(
                layer="O0",
                name=name,
                expect_confirm=expect_confirm,
                needs_user_confirm=r.needs_user_confirm,
                reason_code=r.reason_code,
                passed=(
                    r.needs_user_confirm == expect_confirm
                    and (not expect_confirm or r.reason_code == expect_code)
                ),
                detail=f"left={left[:20]}… new={new[:20]}…",
            )
        )
    return out


def _o6_resolve_scenarios() -> List[ScenarioResult]:
    """O6 resolve — MockWks + LT mock."""
    wks = MockWks({1: {"C": _LEFT}, 2: {"C": ""}}, cols=3)
    lt_cmds: list[str] = []

    blocked = False
    reason = ""
    try:
        resolve_target_column(wks, _NEW_SAME_DAY, lt_execute=lt_cmds.append)
    except OriginColumnGuardError as exc:
        blocked = True
        reason = exc.guard.reason_code

    allowed_col = resolve_target_column(
        wks,
        _NEW_SAME_DAY,
        lt_execute=lt_cmds.append,
        column_guard_confirm=lambda _g: True,
    )
    return [
        ScenarioResult(
            layer="O6",
            name="resolve_blocks_without_confirm",
            expect_confirm=True,
            needs_user_confirm=True,
            reason_code=reason,
            passed=blocked and reason == "same_date",
            detail="OriginColumnGuardError expected",
        ),
        ScenarioResult(
            layer="O6",
            name="resolve_allows_with_confirm",
            expect_confirm=False,
            needs_user_confirm=False,
            reason_code="ok",
            passed=allowed_col == 2,
            ok=allowed_col == 2,
            detail=f"col={allowed_col} lt_calls={len(lt_cmds)}",
        ),
    ]


def _o9_facade_scenarios() -> List[ScenarioResult]:
    """O9 → O8 job — 8 sheet mock op (실행 경로)."""
    op, _ = fx_job_op_equipment_day_guard()
    printed: list[str] = []

    blocked_res = update_from_dataframe(
        OPJU_FX,
        fx_job_df_full(),
        _NEW_SAME_DAY,
        op=op,
        skip_gate=True,
        skip_equipment_day_guard=False,
        column_guard_confirm=None,
        printer=printed.append,
        log_fn=lambda _m: None,
    )
    guard_warn = any(w.code == "equipment_day_guard" for w in blocked_res.warnings)

    op2, sheets = fx_job_op_equipment_day_guard()
    ok_res = update_from_dataframe(
        OPJU_FX,
        fx_job_df_full(),
        _NEW_SAME_DAY,
        op=op2,
        skip_gate=True,
        skip_equipment_day_guard=False,
        column_guard_confirm=lambda _g: True,
        printer=lambda _m: None,
        log_fn=lambda _m: None,
    )
    h2_writes = sheets[0].writes

    return [
        ScenarioResult(
            layer="O9",
            name="facade_blocks_without_confirm",
            expect_confirm=True,
            needs_user_confirm=True,
            reason_code="equipment_day_guard" if guard_warn else "",
            passed=not blocked_res.ok and guard_warn,
            ok=blocked_res.ok,
            detail=f"warnings={[w.code for w in blocked_res.warnings]}",
        ),
        ScenarioResult(
            layer="O9",
            name="facade_writes_with_confirm",
            expect_confirm=False,
            needs_user_confirm=False,
            reason_code="ok",
            passed=ok_res.ok and ok_res.sheets_updated == 8 and len(h2_writes) > 0,
            ok=ok_res.ok and ok_res.sheets_updated == 8,
            detail=f"sheets={ok_res.sheets_updated} h2_writes={len(h2_writes)}",
        ),
    ]


def run_live_equipment_day_guard(
    *,
    artifact_dir: Optional[Path] = None,
) -> Dict[str, Any]:
    """전 시나리오 실행 → artifact JSON (실행 검증용)."""
    scenarios = _o0_scenarios() + _o6_resolve_scenarios() + _o9_facade_scenarios()
    failures = [s.name for s in scenarios if not s.passed]
    ready = not failures

    out: Dict[str, Any] = {
        "status": "ok" if ready else "partial",
        "mode": "equipment_day_guard",
        "ready": ready,
        "reason": "all_scenarios_pass" if ready else f"failed:{','.join(failures)}",
        "scenarios": [s.to_dict() for s in scenarios],
        "sample_left": _LEFT,
        "sample_new_same_day": _NEW_SAME_DAY,
    }
    root = artifact_dir or Path(__file__).resolve().parent
    path = root / ARTIFACT_NAME
    path.write_text(json.dumps(out, indent=2, ensure_ascii=False), encoding="utf-8")
    out["artifact"] = str(path)
    out["artifact_valid"] = ready
    return out


def main() -> int:
    result = run_live_equipment_day_guard()
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0 if result.get("ready") else 1


if __name__ == "__main__":
    raise SystemExit(main())
