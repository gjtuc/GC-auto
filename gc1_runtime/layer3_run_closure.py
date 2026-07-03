# -*- coding: utf-8 -*-
"""
GC1 런 종료(closure) — 에이전트 전용 저널 + 학습 반영.

런이 끝났다고 보는 조건:
  1) 파이프라인 실행 (Autochro·엑셀·메일)
  2) 케이스 스터디 JSON 수집
  3) overlay 학습 반영
  4) ``run_journal_*.json`` 에 진행·수정·권장 사항 기록

실사용자(은규 등)에게는 ``format_end_user_summary`` 형식적 한 줄만.
"""
from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from gc1_runtime.layer3_ocr_learn import (
    _collect_fail_json_since,
    _current_run_path,
    case_study_dir,
    finalize_ocr_run_session,
    learnings_dir,
    load_overlay,
    begin_ocr_run_session,
    register_failure_report,
)

_PIPELINE_FLAG = "GC1_PIPELINE_RUN_ACTIVE"
_JOURNAL_LATEST = "run_journal_latest.json"


def pipeline_run_active() -> bool:
    from gc1_runtime.layer3_ocr_learn import _pipeline_run_active

    return _pipeline_run_active()


def begin_gc1_run_session(*, mode: str = "gc1") -> str:
    """전체 GC1 파이프라인 런 시작."""
    os.environ[_PIPELINE_FLAG] = "1"
    run_id = begin_ocr_run_session()
    path = _current_run_path()
    if path.is_file():
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            data["pipeline"] = True
            data["mode"] = mode
            data["phases"] = list(data.get("phases") or [])
            path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
        except Exception:
            pass
    try:
        from gc1_runtime.layer3_user_mouse_guard import start_learning_guard
        from gc1_runtime.layer3_ocr_study import review_prior_learning
        from gc1_runtime.layer3_ocr_maturity import snapshot_learning_state

        review_prior_learning()
        snapshot_learning_state(run_id)
        start_learning_guard()
    except ImportError:
        pass
    return run_id


def register_pipeline_phase(phase: str, *, ok: bool = True, detail: str = "") -> None:
    """파이프라인 단계 기록 (에이전트 저널용)."""
    path = _current_run_path()
    if not path.is_file():
        return
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        phases: List[dict] = list(data.get("phases") or [])
        phases.append(
            {
                "ts": datetime.now(timezone.utc).isoformat(),
                "phase": phase,
                "ok": ok,
                "detail": detail[:500],
            }
        )
        data["phases"] = phases
        path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    except Exception:
        pass


def _load_fail_reports(started_iso: str, run_data: dict) -> List[dict]:
    paths = _collect_fail_json_since(started_iso)
    if not paths:
        paths = [Path(p) for p in (run_data.get("fail_reports") or []) if Path(p).is_file()]
    reports: List[dict] = []
    for fp in paths:
        try:
            reports.append(json.loads(fp.read_text(encoding="utf-8")))
        except Exception:
            continue
    return reports


def _agent_recommendations(reports: List[dict], applied: List[str]) -> List[str]:
    rec: List[str] = []
    seen_steps = set()
    for rep in reports:
        sid = rep.get("step_id") or ""
        if sid and sid not in seen_steps:
            seen_steps.add(sid)
            for hint in rep.get("hints") or []:
                rec.append(f"{sid}: {hint}")
    for note in applied:
        rec.append(f"applied: {note}")
    if not reports and not applied:
        rec.append("no OCR failures this run")
    return rec[:40]


def _write_agent_journal(
    run_id: str,
    *,
    pipeline_ok: bool,
    fail_reason: str,
    learn_summary: dict,
    run_data: dict,
    reports: List[dict],
    result_fields: dict,
) -> Path:
    journal: Dict[str, Any] = {
        "run_id": run_id,
        "closed_at": datetime.now(timezone.utc).isoformat(),
        "for": "cursor_agent",
        "pipeline_ok": pipeline_ok,
        "fail_reason": fail_reason,
        "phases": run_data.get("phases") or [],
        "ocr_fail_count": learn_summary.get("fail_count", 0),
        "ocr_applied_patches": learn_summary.get("applied") or [],
        "case_study_reports": [
            {
                "path": rep.get("path"),
                "step_id": rep.get("step_id"),
                "kind": rep.get("kind"),
                "reason": rep.get("reason"),
                "hints": rep.get("hints"),
            }
            for rep in reports
        ],
        "agent_recommendations": _agent_recommendations(
            reports, list(learn_summary.get("applied") or [])
        ),
        "study_summary": learn_summary.get("study") or {},
        "overlay_regions": (load_overlay().get("regions") or {}),
        "result": result_fields,
    }
    out_dir = learnings_dir()
    out_path = out_dir / f"run_journal_{run_id}.json"
    out_path.write_text(json.dumps(journal, ensure_ascii=False, indent=2), encoding="utf-8")
    (out_dir / _JOURNAL_LATEST).write_text(
        json.dumps(journal, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    # 한 줄 요약 append (에이전트가 tail 하기 쉽게)
    log_path = out_dir / "agent_run_log.txt"
    status = "OK" if pipeline_ok else "FAIL"
    line = (
        f"{journal['closed_at']} run={run_id} {status} "
        f"ocr_fails={journal['ocr_fail_count']} patches={len(journal['ocr_applied_patches'])}\n"
    )
    with log_path.open("a", encoding="utf-8") as fh:
        fh.write(line)
    return out_path


def close_gc1_run_session(
    *,
    ok: bool,
    fail_reason: str = "",
    log_fn=None,
    **result_fields: Any,
) -> Dict[str, Any]:
    """
    런 종료 — 학습 반영 + 에이전트 저널까지 완료해야 런 closed.

    ``log_fn`` 에는 기술 로그를 남기지 않음 (실사용자 콘솔용).
    """
    os.environ.pop(_PIPELINE_FLAG, None)
    run_data: dict = {}
    run_id = ""
    path = _current_run_path()
    if path.is_file():
        try:
            run_data = json.loads(path.read_text(encoding="utf-8"))
            run_id = str(run_data.get("run_id") or "")
        except Exception:
            pass

    reports = _load_fail_reports(str(run_data.get("started") or ""), run_data)
    if not run_id:
        run_id = datetime.now().strftime("%Y%m%d_%H%M%S")

    study_summary: dict = {}
    try:
        from gc1_runtime.layer3_user_mouse_guard import stop_learning_guard
        from gc1_runtime.layer3_ocr_study import run_post_run_study

        stop_learning_guard()
        study_summary = run_post_run_study(
            run_id,
            run_data=run_data,
            reports=reports,
            pipeline_ok=ok,
        )
        os.environ["GC1_STUDY_APPLIED"] = "1"
    except ImportError:
        study_summary = {}

    learn_summary = finalize_ocr_run_session(
        success=ok,
        message=fail_reason,
        log_fn=lambda _msg: None,
    )
    os.environ.pop("GC1_STUDY_APPLIED", None)
    if study_summary.get("applied_patches"):
        learn_summary["applied"] = study_summary["applied_patches"]
    learn_summary["study"] = study_summary

    journal_path = _write_agent_journal(
        run_id,
        pipeline_ok=ok,
        fail_reason=fail_reason,
        learn_summary=learn_summary,
        run_data=run_data,
        reports=reports,
        result_fields=result_fields,
    )

    return {
        "closed": True,
        "run_id": run_id,
        "journal_path": str(journal_path),
        "learn_summary": learn_summary,
    }


def format_end_user_summary(
    *,
    ok: bool,
    email_sent: bool = False,
    output_basename: str = "",
    fail_reason: str = "",
) -> str:
    """실사용자용 — 형식적 완료 문구만 (기술·케이스 스터디 없음)."""
    if not ok:
        return "처리 중 문제가 있었습니다. 잠시 후 다시 시도해 주세요."
    parts = ["작업이 완료되었습니다."]
    if output_basename:
        parts.append(f"엑셀 파일을 저장했습니다.")
    if email_sent:
        parts.append("메일을 발송했습니다.")
    return " ".join(parts)


# re-export for case study registration
__all__ = [
    "begin_gc1_run_session",
    "close_gc1_run_session",
    "format_end_user_summary",
    "pipeline_run_active",
    "register_failure_report",
    "register_pipeline_phase",
]
