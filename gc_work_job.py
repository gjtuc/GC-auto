# -*- coding: utf-8 -*-
"""
gc_work_job.py — 핫스pot 작업 세션 (미완료 감지·단계별 재개)

=============================================================================
[어느 PC — GC2/GC3 장비 PC (차헌)]
=============================================================================

  GC2/GC3 **장비** PC merge 시 추가. GC1은 세션당 1회, GC2/GC3는 메일 1시간 쿨다운(핫스pot 무관).
  은규 PC / 차헌 PC 에서는 미사용 (gc_automation.py 미실행).

  GitHub: gjtuc/GC-auto — 다른 PC는 git pull 로 받음.

핫스pot 연결만으로 pipeline 을 돌리지 않습니다.
  · 새 데이터 있을 때만 새 작업 시작
  · 핫스pot 끊김·SMTP 실패 → 미완료 유지
  · 재연결 시 **마지막 진행 단계부터 다시** (끊김 시 엑셀 완료 표시도 신뢰 안 함)
  · 메일만 안정적으로 끝났을 때만 메일 단계만 재시도
  · 메일 발송 성공 시에만 session_complete_log 1회 기록
"""

from __future__ import annotations

import os
from datetime import datetime
from typing import Any, Optional

from gc_state import (
    clear_pending_email_retry,
    get_pending_email_retry,
    load_send_state,
    log_gc_event,
    mark_sequence_processed,
    save_send_state,
    set_pending_email_retry,
)

ACTIVE_JOB_KEY = "active_work_job"
STEP_ORDER = ("prepare", "excel", "mail")
STEP_LABELS = {
    "prepare": "전처리(PDF/데이터)",
    "excel": "엑셀 저장",
    "mail": "메일 발송",
}


def get_active_job(state: dict) -> Optional[dict]:
    job = state.get(ACTIVE_JOB_KEY)
    return job if isinstance(job, dict) else None


def _default_steps() -> dict[str, bool]:
    return {"prepare": False, "excel": False, "mail": False}


def start_active_job(
    state_path: str,
    *,
    sequence_folder: str,
    pipeline_mode: str,
    chemstation_mode: str,
) -> dict:
    job = {
        "started_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "sequence_folder": sequence_folder,
        "pipeline_mode": pipeline_mode,
        "chemstation_mode": chemstation_mode,
        "steps": _default_steps(),
        "interrupted": False,
        "output_path": None,
        "sample_name": None,
        "seq_date": None,
        "email_body": None,
        "latest_mtime": None,
        "fail_reason": None,
        "last_step": None,
    }
    state = load_send_state(state_path)
    state[ACTIVE_JOB_KEY] = job
    save_send_state(state_path, state)
    return job


def ensure_active_job(
    state_path: str,
    *,
    sequence_folder: str,
    pipeline_mode: str,
    chemstation_mode: str,
) -> dict:
    state = load_send_state(state_path)
    job = get_active_job(state)
    if job and job.get("sequence_folder") == sequence_folder:
        job["interrupted"] = False
        job["fail_reason"] = None
        state[ACTIVE_JOB_KEY] = job
        save_send_state(state_path, state)
        return job
    return start_active_job(
        state_path,
        sequence_folder=sequence_folder,
        pipeline_mode=pipeline_mode,
        chemstation_mode=chemstation_mode,
    )


def update_active_job(state_path: str, **fields: Any) -> None:
    state = load_send_state(state_path)
    job = get_active_job(state)
    if not job:
        return
    for key, value in fields.items():
        if key == "steps" and isinstance(value, dict):
            steps = job.setdefault("steps", _default_steps())
            steps.update(value)
        else:
            job[key] = value
    state[ACTIVE_JOB_KEY] = job
    save_send_state(state_path, state)


def mark_job_step(state_path: str, step: str, done: bool = True) -> None:
    state = load_send_state(state_path)
    job = get_active_job(state)
    if not job:
        return
    steps = job.setdefault("steps", _default_steps())
    steps[step] = done
    state[ACTIVE_JOB_KEY] = job
    save_send_state(state_path, state)


def set_job_last_step(state_path: str, step: str) -> None:
    update_active_job(state_path, last_step=step)


def mark_job_interrupted(
    state_path: str,
    fail_reason: Optional[str] = None,
    last_step: Optional[str] = None,
) -> None:
    state = load_send_state(state_path)
    job = get_active_job(state)
    if not job:
        return
    job["interrupted"] = True
    if fail_reason:
        job["fail_reason"] = fail_reason
    if last_step:
        job["last_step"] = last_step
    state[ACTIVE_JOB_KEY] = job
    save_send_state(state_path, state)
    step_label = STEP_LABELS.get(job.get("last_step") or "", job.get("last_step") or "")
    print(
        f"[안내] 핫스pot 끊김/중단 — 작업 미완료 "
        f"(재연결 시 '{step_label}' 단계부터 다시)"
    )


def clear_active_job(state_path: str) -> None:
    state = load_send_state(state_path)
    if ACTIVE_JOB_KEY not in state:
        return
    state.pop(ACTIVE_JOB_KEY, None)
    save_send_state(state_path, state)


def excel_step_ok(job: dict) -> bool:
    steps = job.get("steps") or {}
    if not steps.get("excel"):
        return False
    path = job.get("output_path")
    return bool(path and os.path.isfile(path))


def invalidate_steps_from(state_path: str, from_step: str) -> None:
    """재개 전 — 해당 단계부터 완료 표시 제거 (엑셀 재작성 시 기존 파일 삭제)."""
    state = load_send_state(state_path)
    job = get_active_job(state)
    if not job:
        return

    steps = job.setdefault("steps", _default_steps())
    if from_step == "prepare":
        steps.update(_default_steps())
        clear_pending_email_retry(state_path)
        path = job.get("output_path")
        if path and os.path.isfile(path):
            try:
                os.remove(path)
            except OSError:
                pass
    elif from_step == "excel":
        steps["excel"] = False
        steps["mail"] = False
        clear_pending_email_retry(state_path)
        path = job.get("output_path")
        if path and os.path.isfile(path):
            try:
                os.remove(path)
                print(f"[재개] 불완전 엑셀 삭제 — {os.path.basename(path)}")
            except OSError:
                pass
    elif from_step == "mail":
        steps["mail"] = False

    job["steps"] = steps
    job["interrupted"] = False
    state[ACTIVE_JOB_KEY] = job
    save_send_state(state_path, state)


def resume_start_step(job: dict, send_email: bool) -> Optional[str]:
    """
    재개 시 처음 다시 할 단계.

    · 핫스pot 끊김/중단 → last_step부터 다시 (엑셀 표시 완료도 재검증)
    · SMTP만 실패(끊김 없음) + 엑셀 안정 → mail만
    """
    if not job:
        return None

    interrupted = bool(job.get("interrupted"))
    last_step = job.get("last_step")
    steps = job.get("steps") or {}

    if interrupted and last_step in STEP_ORDER:
        return last_step
    if interrupted:
        if job.get("pipeline_mode") == "gc1" and not steps.get("prepare"):
            return "prepare"
        if not steps.get("excel") or not excel_step_ok(job):
            return "excel"
        if send_email and not steps.get("mail"):
            return "mail"
        return "excel"

    if send_email and steps.get("excel") and excel_step_ok(job) and not steps.get("mail"):
        return "mail"

    if job.get("pipeline_mode") == "gc1" and not steps.get("prepare"):
        return "prepare"
    if not steps.get("excel") or not excel_step_ok(job):
        return "excel"
    if send_email and not steps.get("mail"):
        return "mail"
    return None


def audit_resume_plan(job: dict, send_email: bool) -> list[str]:
    """재개 시 다시 수행할 단계 목록 (마지막 단계부터 끝까지)."""
    start = resume_start_step(job, send_email)
    if not start:
        return []
    idx = STEP_ORDER.index(start)
    plan = list(STEP_ORDER[idx:])
    if not send_email and "mail" in plan:
        plan = [s for s in plan if s != "mail"]
    return plan


def job_needs_resume(state: dict, send_email: bool) -> bool:
    job = get_active_job(state)
    if job and resume_start_step(job, send_email):
        return True
    return bool(get_pending_email_retry(state))


def record_session_mail_complete(
    state_path: str,
    excel_output_dir: str,
    action_summary: Optional[str] = None,
    *,
    chemstation_mode: str = "auto",
) -> None:
    """메일 발송·검증 성공 = 작업 세션 1회 완료."""
    from gc_state import format_auto_mail_slot_status, uses_mail_cooldown

    now = datetime.now()
    today_str = now.strftime("%Y%m%d")
    state = load_send_state(state_path)
    log = state.setdefault("session_complete_log", [])
    log.append(
        {
            "date": today_str,
            "time": now.strftime("%H:%M:%S"),
            "sequence_folder": (get_active_job(state) or {}).get("sequence_folder"),
        }
    )
    if action_summary:
        state["last_action_summary"] = action_summary
    if uses_mail_cooldown(chemstation_mode):
        state["last_auto_mail_sent_at"] = now.strftime("%Y-%m-%dT%H:%M:%S")
    state.pop(ACTIVE_JOB_KEY, None)
    state.pop("pending_email_retry", None)
    save_send_state(state_path, state)
    if uses_mail_cooldown(chemstation_mode):
        slot_msg = format_auto_mail_slot_status(state, now)
        from gc_config import AUTO_MAIL_COOLDOWN_HOURS

        print(
            f"[안내] 작업 세션 완료 — 자동 메일 {slot_msg} "
            f"({AUTO_MAIL_COOLDOWN_HOURS}시간 후 재충전)"
        )
    else:
        print(
            f"[안내] 작업 세션 완료 — 메일 발송 1회 기록 "
            f"({format_today_session_send_status(state, today_str)})"
        )
    log_gc_event(excel_output_dir, "session_mail_complete", action_summary or "메일 발송 완료")


def format_today_session_send_status(state: dict, today_str: str) -> str:
    log = state.get("session_complete_log", [])
    if not isinstance(log, list):
        return "오늘 0회 (메일 성공 시 1회)"
    count = sum(1 for e in log if isinstance(e, dict) and e.get("date") == today_str)
    return f"오늘 {count}회 (메일 성공 시 세션 1회)"


def get_today_session_send_count(state: dict, today_str: str) -> int:
    log = state.get("session_complete_log", [])
    if not isinstance(log, list):
        return 0
    return sum(1 for e in log if isinstance(e, dict) and e.get("date") == today_str)


def apply_processing_result_to_job(
    state_path: str,
    *,
    sequence_folder: str,
    latest_mtime: float,
    action_summary: str,
    email_sent: bool,
    send_email: bool,
    output_path: Optional[str] = None,
    email_body: Optional[str] = None,
    sample_name: Optional[str] = None,
    seq_date: Optional[str] = None,
    chemstation_mode: str = "auto",
    prepare_done: bool = True,
) -> None:
    """
    pipeline 결과를 active_job·pending 에 반영.
    mark_sequence_processed — 엑셀 완료 시 (메일 전에도 새 데이터 중복 방지).
    session_complete_log — 메일 성공 시에만.
    """
    excel_dir = os.path.dirname(state_path) if state_path else ""
    crm_mtime = None
    if chemstation_mode == "gc1":
        from gc_state import resolve_gc1_crm_mtime

        crm_mtime = resolve_gc1_crm_mtime(excel_dir)

    excel_ok = bool(output_path and os.path.isfile(output_path))

    if excel_ok:
        mark_sequence_processed(
            state_path,
            sequence_folder,
            latest_mtime,
            action_summary,
            crm_mtime=crm_mtime,
        )

    job_updates: dict[str, Any] = {
        "sequence_folder": sequence_folder,
        "output_path": output_path,
        "sample_name": sample_name,
        "seq_date": seq_date,
        "email_body": email_body,
        "latest_mtime": latest_mtime,
        "interrupted": False,
        "fail_reason": None,
        "steps": {
            "prepare": prepare_done,
            "excel": excel_ok,
            "mail": email_sent,
        },
    }
    if send_email and excel_ok and not email_sent:
        job_updates["last_step"] = "mail"
    update_active_job(state_path, **job_updates)

    if email_sent:
        record_session_mail_complete(
            state_path,
            excel_dir,
            action_summary,
            chemstation_mode=chemstation_mode,
        )
        return

    if not send_email and excel_ok:
        clear_active_job(state_path)
        return

    if send_email and excel_ok and email_body and sample_name and seq_date:
        set_pending_email_retry(
            state_path,
            excel_path=output_path,
            sample_name=sample_name,
            seq_date=seq_date,
            body_text=email_body,
            sequence_folder=sequence_folder,
        )
        print("[안내] 엑셀 완료 · 메일 미완료 — 재연결/핫스pot 유지 시 메일 단계 재개")


def recover_stale_job_from_state(state_path: str, excel_output_dir: str) -> bool:
    """pending 또는 엑셀-only 기록이 있으면 active_job 복구."""
    state = load_send_state(state_path)
    if get_active_job(state):
        return False

    pending = get_pending_email_retry(state)
    if pending:
        start_active_job(
            state_path,
            sequence_folder=pending.get("sequence_folder") or "",
            pipeline_mode="unknown",
            chemstation_mode="auto",
        )
        update_active_job(
            state_path,
            output_path=pending.get("excel_path"),
            sample_name=pending.get("sample_name"),
            seq_date=pending.get("seq_date"),
            email_body=pending.get("body_text"),
            steps={"prepare": True, "excel": True, "mail": False},
            last_step="mail",
        )
        print("[안내] 미발송 메일 대기 — active_work_job 복구")
        return True

    summary = state.get("last_action_summary") or ""
    if "메일 발송" in summary:
        return False
    if "엑셀" not in summary:
        return False

    sequence_folder = state.get("last_sequence_folder")
    if not sequence_folder:
        return False

    import glob

    files = glob.glob(os.path.join(excel_output_dir, "*.xlsx"))
    if not files:
        return False

    excel_path = max(files, key=os.path.getmtime)
    base = os.path.basename(excel_path)
    stem = base[:-5] if base.lower().endswith(".xlsx") else base
    parts = stem.split(" ", 1)
    seq_date = parts[0] if parts and len(parts[0]) == 8 and parts[0].isdigit() else ""
    sample_name = parts[1] if len(parts) > 1 else stem
    body_text = (
        "GC ChemStation 자동 정리 결과를 첨부합니다.\n"
        "(이전 처리에서 메일만 미완료 — 재발송)\n\n"
        f"첨부 파일: {base}\n"
    )
    set_pending_email_retry(
        state_path,
        excel_path=excel_path,
        sample_name=sample_name,
        seq_date=seq_date or datetime.now().strftime("%Y%m%d"),
        body_text=body_text,
        sequence_folder=sequence_folder,
    )
    return recover_stale_job_from_state(state_path, excel_output_dir)
