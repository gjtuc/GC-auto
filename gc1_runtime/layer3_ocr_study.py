# -*- coding: utf-8 -*-
"""
런 전·후 OCR 스터디 — 저널·성숙도·정책을 읽고 overlay 반영.

런 **시작 전**: 지금까지 누적 학습 요약 (에이전트 로그)
런 **종료 후**: 관측·fail JSON 전부 반영, 성숙 스킬은 patch 생략
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

from gc1_runtime.layer3_ocr_learn import (
    _apply_report_to_overlay,
    learnings_dir,
    load_overlay,
    overlay_path,
)
from gc1_runtime.layer3_ocr_maturity import (
    demote_skills_from_failures,
    load_maturity,
    load_policy,
    load_run_observations,
    skill_key,
)
from gc1_runtime.layer3_user_mouse_guard import (
    get_learning_pause_reason,
    is_learning_paused_by_user,
)

_STUDY_LOG = "study_session_log.txt"


def _study_log_path() -> Path:
    return learnings_dir() / _STUDY_LOG


def _append_study_log(line: str) -> None:
    ts = datetime.now(timezone.utc).isoformat()
    with _study_log_path().open("a", encoding="utf-8") as fh:
        fh.write(f"{ts} {line}\n")


def review_prior_learning(*, log_fn: Optional[Callable[[str], None]] = None) -> dict:
    """
    런 **시작 전** — maturity·policy·최근 저널을 읽고 에이전트용 요약.
    사용자 콘솔에는 기본 출력 안 함 (log_fn 으로만).
    """
    _log = log_fn or (lambda _m: None)
    maturity = load_maturity()
    policy = load_policy()
    skills = maturity.get("skills") or {}
    mature = [k for k, v in skills.items() if v.get("mature")]
    learning = [k for k, v in skills.items() if not v.get("mature") and (v.get("attempts") or 0) > 0]

    latest = learnings_dir() / "run_journal_latest.json"
    last_run = {}
    if latest.is_file():
        try:
            last_run = json.loads(latest.read_text(encoding="utf-8"))
        except Exception:
            pass

    summary = {
        "reviewed_at": datetime.now(timezone.utc).isoformat(),
        "mature_skill_count": len(mature),
        "learning_skill_count": len(learning),
        "mature_skills": mature[:30],
        "learning_skills": learning[:30],
        "policy_skill_count": len(policy.get("skills") or {}),
        "last_run_id": last_run.get("run_id"),
        "last_pipeline_ok": last_run.get("pipeline_ok"),
        "last_ocr_fails": last_run.get("ocr_fail_count"),
    }

    _append_study_log(
        f"PRE-RUN mature={len(mature)} learning={len(learning)} "
        f"last={summary.get('last_run_id')} ok={summary.get('last_pipeline_ok')}"
    )
    _log(f"[스터디] 런 전 복습 — 성숙 {len(mature)} · 학습 중 {len(learning)}")
    for k in mature[:5]:
        st = skills[k]
        _log(f"[스터디]   성숙(97%+) {k} rate={st.get('rate')}")
    for k in learning[:5]:
        st = skills[k]
        _log(f"[스터디]   학습 중 {k} rate={st.get('rate')} n={st.get('attempts')}")
    if last_run.get("agent_recommendations"):
        _log("[스터디] 직전 런 권장:")
        for rec in (last_run.get("agent_recommendations") or [])[:5]:
            _log(f"[스터디]   - {rec}")

    return summary


def run_post_run_study(
    run_id: str,
    *,
    run_data: dict,
    reports: List[dict],
    pipeline_ok: bool,
    log_fn: Optional[Callable[[str], None]] = None,
) -> Dict[str, Any]:
    """
    런 **종료 후** — 관측·fail 반영, overlay patch, study journal.

    인간 마우스로 오염된 런은 관측·성숙도·케이스 스터디를 **전부 폐기**.
    """
    _log = log_fn or (lambda _m: None)
    paused = is_learning_paused_by_user()
    pause_reason = get_learning_pause_reason() if paused else ""

    if paused:
        from gc1_runtime.layer3_ocr_maturity import discard_contaminated_run_learning

        discard_info = discard_contaminated_run_learning(
            run_id,
            run_data=run_data,
            reports=reports,
            reason=pause_reason,
        )
        result: Dict[str, Any] = {
            "run_id": run_id,
            "observation_count": 0,
            "fail_report_count": 0,
            "demoted_skills": [],
            "applied_patches": [],
            "skipped_mature": [],
            "user_paused_learning": True,
            "user_pause_reason": pause_reason,
            "learning_discarded": True,
            "discard_detail": discard_info,
            "pipeline_ok": pipeline_ok,
        }
        reason = pause_reason or "unknown"
        _log(
            f"[스터디] 사용자 마우스({reason}) — 이번 런 학습 데이터 전부 폐기 "
            f"(obs={discard_info.get('observations_deleted')} "
            f"case={discard_info.get('case_study_deleted')})"
        )
        _write_study_journal(run_id, result, [], [])
        _append_study_log(
            f"POST-RUN {run_id} discarded reason={reason} "
            f"obs={discard_info.get('observations_deleted')} "
            f"case={discard_info.get('case_study_deleted')}"
        )
        return result

    observations = load_run_observations(run_id)
    demoted = demote_skills_from_failures(reports)

    result = {
        "run_id": run_id,
        "observation_count": len(observations),
        "fail_report_count": len(reports),
        "demoted_skills": demoted,
        "applied_patches": [],
        "skipped_mature": [],
        "user_paused_learning": False,
        "user_pause_reason": "",
        "learning_discarded": False,
        "pipeline_ok": pipeline_ok,
    }

    overlay = load_overlay()
    all_notes: List[str] = []

    for rep in reports:
        sid = str(rep.get("step_id") or "")
        task = str(rep.get("task_id") or rep.get("kind") or "")
        keys: List[str] = []
        for reg in list(rep.get("regions") or []) + list(rep.get("exploration") or []):
            rid = str(reg.get("region") or "")
            if rid:
                keys.append(skill_key(sid, rid, task))
        if not keys:
            keys.append(skill_key(sid, "", task))
        from gc1_runtime.layer3_ocr_maturity import should_learn_skill

        if not any(should_learn_skill(k) for k in keys):
            result["skipped_mature"].extend(keys)
            continue
        notes = _apply_report_to_overlay(overlay, rep)
        all_notes.extend(notes)

    runs = list(overlay.get("runs") or [])
    runs.append(
        {
            "run_id": run_id,
            "finished": datetime.now(timezone.utc).isoformat(),
            "success": pipeline_ok,
            "fail_count": len(reports),
            "observation_count": len(observations),
            "applied_notes": all_notes[:20],
            "study": True,
        }
    )
    overlay["runs"] = runs[-40:]
    overlay_path().write_text(json.dumps(overlay, ensure_ascii=False, indent=2), encoding="utf-8")

    result["applied_patches"] = all_notes
    _write_study_journal(run_id, result, observations, reports)

    _append_study_log(
        f"POST-RUN {run_id} ok={pipeline_ok} obs={len(observations)} "
        f"fails={len(reports)} patches={len(all_notes)} demoted={len(demoted)}"
    )
    _log(f"[스터디] 런 후 공부 — 관측 {len(observations)} · fail {len(reports)} · patch {len(all_notes)}")
    if demoted:
        _log(f"[스터디] 성숙 해제 {len(demoted)}건 (실패로 재학습)")
    for n in all_notes[:6]:
        _log(f"[스터디]   patch {n}")
    if result["skipped_mature"]:
        _log(f"[스터디] 성숙 스킬 patch 생략 {len(result['skipped_mature'])}건")

    return result


def _write_study_journal(
    run_id: str,
    result: dict,
    observations: List[dict],
    reports: List[dict],
) -> Path:
    maturity = load_maturity()
    policy = load_policy()
    journal = {
        "run_id": run_id,
        "studied_at": datetime.now(timezone.utc).isoformat(),
        "for": "cursor_agent",
        "result": result,
        "observation_sample": observations[-50:],
        "fail_steps": [r.get("step_id") for r in reports],
        "mature_skills": [
            k for k, v in (maturity.get("skills") or {}).items() if v.get("mature")
        ],
        "policy_preview": {
            k: v.get("preferred_method")
            for k, v in list((policy.get("skills") or {}).items())[:20]
        },
    }
    out = learnings_dir() / f"study_journal_{run_id}.json"
    out.write_text(json.dumps(journal, ensure_ascii=False, indent=2), encoding="utf-8")
    latest = learnings_dir() / "study_journal_latest.json"
    latest.write_text(json.dumps(journal, ensure_ascii=False, indent=2), encoding="utf-8")
    return out
