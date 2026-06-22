# -*- coding: utf-8 -*-
"""
gc_state.py — 발송·처리 기록 JSON (.gc_send_state.json)

=============================================================================
[역할]
=============================================================================

  watch·pipeline·Autochro 가 **상태ful** 로 동작하기 위한 단일 JSON.
  출력 폴더(Desktop\\박은규 또는 Desktop\\KCH)에 .gc_send_state.json 으로 저장.

=============================================================================
[주요 키]
=============================================================================

  daily_send_count          GC2/GC3 watch 자동 메일 — 날짜별 {am:0|1, pm:0|1}
  last_processed_acam_mtime GC2 acam / GC1 PDF mtime — has_new_data_since_last_run
  last_processed_crm_mtime  GC1 처리 완료 시 CRM mtime (기록용)
  last_autochro_crm_mtime   Autochro export 가 마지막으로 본 CRM mtime
  pending_email_retry       엑셀 OK · SMTP 실패 시 watch 가 성공까지 자동 재발송
  manual_send_log           force 발송 기록 (일일 슬롯 미포함)
  one_shot_hotspot_process  이번만 — 핫스pot 재연결 시 새 acam 없어도 1회 처리 후 삭제

=============================================================================
[GC1·GC2·GC3 메일 한도]
=============================================================================

  session_based_auto_send() == True (전 인스턴스)
    → 오전/오후 슬롯 검사 생략 (can_auto_send_for_mode)
    → watch 는 **핫스pot 세션당 1회** pipeline (gc_watch._tick)
    → force(config.force) 는 한도·핫스pot 모두 우회

  daily_send_count / am/pm 슬롯 — 레거시 기록용 (현재 자동 발송 한도에 사용 안 함)

=============================================================================
[has_new_data_since_last_run]
=============================================================================

  GC2/GC3: sequence 폴더 acam/Report mtime > last_processed_acam_mtime
  GC1 (수동/보조): PDF mtime 비교. watch GC1 은 세션 edge 로 처리하므로
  CRM-only gate 는 watch 에서 사용하지 않음.
"""

from __future__ import annotations

import json
import os
from datetime import datetime
from typing import Optional, Tuple

from gc_config import (
    AFTERNOON_START_HOUR,
    DAILY_SEND_LIMIT,
    PENDING_EMAIL_SEND_RETRIES,
    PENDING_EMAIL_SMTP_WAIT_MAX_SEC,
)
from gc_chemstation import get_latest_injection_acam_mtime

try:
    from gc_chem32 import get_latest_report_mtime, resolve_chemstation_mode
except ImportError:
    get_latest_report_mtime = None
    resolve_chemstation_mode = None


def load_send_state(state_path: str) -> dict:
    try:
        with open(state_path, encoding="utf-8") as state_file:
            data = json.load(state_file)
        return data if isinstance(data, dict) else {}
    except (OSError, json.JSONDecodeError):
        return {}


def save_send_state(state_path: str, state: dict) -> None:
    os.makedirs(os.path.dirname(state_path) or ".", exist_ok=True)
    with open(state_path, "w", encoding="utf-8") as state_file:
        json.dump(state, state_file, ensure_ascii=False, indent=2)


def log_gc_event(excel_output_dir: str, event_type: str, message: str, **extra) -> None:
    """출력 폴더\\_system\\gc_events.jsonl — 오류·재시도 기록."""
    if not excel_output_dir:
        return
    system_dir = os.path.join(excel_output_dir, "_system")
    os.makedirs(system_dir, exist_ok=True)
    path = os.path.join(system_dir, "gc_events.jsonl")
    entry = {
        "ts": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "type": event_type,
        "message": message,
        **extra,
    }
    try:
        with open(path, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")
    except OSError:
        pass


def current_send_slot(dt: Optional[datetime] = None) -> str:
    """현재 시각 기준 자동 메일 슬롯 — am(00:00~11:59) / pm(12:00~)."""
    hour = (dt or datetime.now()).hour
    return "pm" if hour >= AFTERNOON_START_HOUR else "am"


def slot_label(slot: str) -> str:
    return "오전" if slot == "am" else "오후"


def _normalize_day_slots(raw) -> dict:
    """일별 슬롯 기록을 {am, pm} 정수로 통일. 구형 int 형식도 호환."""
    if isinstance(raw, dict):
        return {"am": int(raw.get("am", 0)), "pm": int(raw.get("pm", 0))}
    if isinstance(raw, int):
        total = max(0, int(raw))
        return {"am": min(total, 1), "pm": min(max(0, total - 1), 1)}
    return {"am": 0, "pm": 0}


def get_day_slots(state: dict, today_str: str) -> dict:
    counts = state.get("daily_send_count")
    if not isinstance(counts, dict):
        return {"am": 0, "pm": 0}
    return _normalize_day_slots(counts.get(today_str, {}))


def get_today_send_count(state: dict, today_str: str) -> int:
    slots = get_day_slots(state, today_str)
    return slots["am"] + slots["pm"]


def format_today_send_status(state: dict, today_str: str) -> str:
    slots = get_day_slots(state, today_str)
    return f"오전 {slots['am']}/1, 오후 {slots['pm']}/1"


def is_slot_available(state: dict, today_str: str, slot: str) -> bool:
    return get_day_slots(state, today_str).get(slot, 0) < 1


def session_based_auto_send(mode: str) -> bool:
    """GC1·GC2·GC3 — 오전/오후 슬롯 없이 핫스pot 세션당 자동 처리·메일."""
    return True


def gc1_unlimited_auto_send(mode: str) -> bool:
    """session_based_auto_send 와 동일 (GC1 호환 별칭)."""
    return session_based_auto_send(mode)


def get_today_session_send_count(state: dict, today_str: str) -> int:
    from gc_work_job import get_today_session_send_count as _count

    return _count(state, today_str)


def format_today_session_send_status(state: dict, today_str: str) -> str:
    from gc_work_job import format_today_session_send_status as _fmt

    return _fmt(state, today_str)


def resolve_gc1_crm_mtime(excel_output_dir: str) -> Optional[float]:
    try:
        from gc_autochro import get_crm_mtime, is_autochro_enabled, load_autochro_config

        if not is_autochro_enabled():
            return None
        cfg = load_autochro_config(excel_output_dir)
        if cfg.crm_path:
            return get_crm_mtime(cfg.crm_path)
    except ImportError:
        pass
    return None


def can_auto_send_for_mode(
    state_path: str,
    mode: str = "auto",
    dt: Optional[datetime] = None,
) -> Tuple[bool, str]:
    """전 인스턴스 session_based — 오전/오후 슬롯 한도 없음."""
    if session_based_auto_send(mode):
        return True, ""
    return can_auto_send_in_current_slot(state_path, dt)


def can_auto_send_in_current_slot(
    state_path: str,
    dt: Optional[datetime] = None,
) -> Tuple[bool, str]:
    """현재 시각 슬롯(오전/오후)에 자동 메일을 보낼 수 있는지 (GC2/GC3)."""
    now = dt or datetime.now()
    today_str = now.strftime("%Y%m%d")
    slot = current_send_slot(now)
    state = load_send_state(state_path)
    if is_slot_available(state, today_str, slot):
        return True, ""
    return False, f"오늘 {slot_label(slot)} 자동 메일 1/1회 사용 ({format_today_send_status(state, today_str)})"


def record_daily_send(
    state_path: str,
    count_toward_limit: bool = True,
    today_str: Optional[str] = None,
    dt: Optional[datetime] = None,
) -> None:
    """메일 발송 기록. --force 는 count_toward_limit=False."""
    now = dt or datetime.now()
    today_str = today_str or now.strftime("%Y%m%d")
    state = load_send_state(state_path)
    if count_toward_limit:
        counts = state.setdefault("daily_send_count", {})
        day_slots = _normalize_day_slots(counts.get(today_str, {}))
        slot = current_send_slot(now)
        day_slots[slot] = int(day_slots.get(slot, 0)) + 1
        counts[today_str] = day_slots
        save_send_state(state_path, state)
        print(
            f"[안내] 오늘({today_str}) {slot_label(slot)} 자동 메일 "
            f"{day_slots[slot]}/1 기록 — {format_today_send_status(state, today_str)}"
        )
    else:
        manual = state.setdefault("manual_send_log", [])
        manual.append({"date": today_str, "time": now.strftime("%H:%M:%S")})
        save_send_state(state_path, state)
        print("[안내] 메일 발송 기록 (일일 슬롯 한도 미포함)")


def mark_sequence_processed(
    state_path: str,
    sequence_folder: str,
    latest_mtime: float,
    action_summary: str,
    *,
    crm_mtime: Optional[float] = None,
) -> None:
    """
    처리 완료 시각 기록 — watch 가 '새 데이터' 판별에 사용.

    GC1: last_processed_crm_mtime — 처리 시각 기록(참고용).
    """
    state = load_send_state(state_path)
    state["last_processed_acam_mtime"] = latest_mtime
    state["last_sequence_folder"] = sequence_folder
    state["last_action_summary"] = action_summary
    if crm_mtime is not None:
        state["last_processed_crm_mtime"] = crm_mtime
    if sequence_folder and state.get("last_failed_gc1_pdf") == sequence_folder:
        for key in (
            "last_failed_gc1_pdf",
            "last_failed_gc1_pdf_mtime",
            "last_failed_gc1_reason",
            "last_failed_gc1_at",
        ):
            state.pop(key, None)
    save_send_state(state_path, state)


def mark_gc1_pdf_attempt_failed(state_path: str, pdf_path: str, fail_reason: str) -> None:
    """GC1 watch — 동일 PDF 파싱/엑셀 실패 시 15초마다 Autochro 재실행 방지."""
    from gc_gc1 import get_latest_pdf_mtime

    mtime = get_latest_pdf_mtime(pdf_path)
    if mtime is None:
        return
    state = load_send_state(state_path)
    state["last_failed_gc1_pdf"] = pdf_path
    state["last_failed_gc1_pdf_mtime"] = mtime
    state["last_failed_gc1_reason"] = fail_reason
    state["last_failed_gc1_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    save_send_state(state_path, state)
    print(
        "[안내] GC1 처리 실패 기록 — 동일 PDF는 watch에서 재시도 안 함 "
        "(핫스팟 재연결·force·새 PDF/CRM 필요)"
    )
    print(f"       사유: {fail_reason}")


def should_retry_gc1_pdf(state_path: str, pdf_path: str) -> bool:
    """마지막 처리 이후 새 PDF이고, 동일 파일로 이미 실패 기록이 없을 때만 재시도."""
    if not has_new_data_since_last_run(state_path, pdf_path, "", "gc1"):
        return False
    from gc_gc1 import get_latest_pdf_mtime

    mtime = get_latest_pdf_mtime(pdf_path)
    if mtime is None:
        return False
    state = load_send_state(state_path)
    if state.get("last_failed_gc1_pdf") == pdf_path:
        failed_mtime = state.get("last_failed_gc1_pdf_mtime")
        if failed_mtime is not None and float(failed_mtime) == float(mtime):
            return False
    return True


def get_pending_email_retry(state: dict) -> Optional[dict]:
    pending = state.get("pending_email_retry")
    if isinstance(pending, dict) and pending.get("excel_path"):
        return pending
    return None


def set_pending_email_retry(
    state_path: str,
    *,
    excel_path: str,
    sample_name: str,
    seq_date: str,
    body_text: str,
    sequence_folder: str,
) -> None:
    state = load_send_state(state_path)
    state["pending_email_retry"] = {
        "excel_path": excel_path,
        "sample_name": sample_name,
        "seq_date": seq_date,
        "body_text": body_text,
        "sequence_folder": sequence_folder,
        "failed_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "retry_count": 0,
    }
    save_send_state(state_path, state)
    print(f"[안내] 메일 재발송 대기 등록 — {os.path.basename(excel_path)}")
    print(f"       watch가 핫스팟 연결 중 {os.getenv('PENDING_EMAIL_RETRY_INTERVAL_SEC', '60')}초마다 자동 재시도 (성공까지)")


def clear_pending_email_retry(state_path: str) -> None:
    state = load_send_state(state_path)
    if "pending_email_retry" not in state:
        return
    state.pop("pending_email_retry", None)
    save_send_state(state_path, state)


def has_one_shot_hotspot_process(state_path: str) -> bool:
    """이번만 핫스pot 재연결 시 새 acam 없이도 pipeline 1회."""
    return bool(load_send_state(state_path).get("one_shot_hotspot_process"))


def consume_one_shot_hotspot_process(state_path: str) -> bool:
    """one_shot_hotspot_process 가 있으면 소비(삭제) 후 True."""
    state = load_send_state(state_path)
    if not state.get("one_shot_hotspot_process"):
        return False
    state.pop("one_shot_hotspot_process", None)
    save_send_state(state_path, state)
    print("[안내] one_shot_hotspot_process — 이번만 핫스팟 재연결 시 처리 (새 데이터 없어도 1회)")
    return True


def record_processing_result(
    state_path: str,
    *,
    sequence_folder: str,
    latest_mtime: float,
    action_summary: str,
    email_sent: bool,
    send_email: bool,
    count_email_toward_limit: bool,
    output_path: Optional[str] = None,
    email_body: Optional[str] = None,
    sample_name: Optional[str] = None,
    seq_date: Optional[str] = None,
    chemstation_mode: str = "auto",
    prepare_done: bool = True,
) -> None:
    """처리 후 상태 기록 — 메일 성공 시에만 세션 1회 완료."""
    from gc_work_job import apply_processing_result_to_job

    apply_processing_result_to_job(
        state_path,
        sequence_folder=sequence_folder,
        latest_mtime=latest_mtime,
        action_summary=action_summary,
        email_sent=email_sent,
        send_email=send_email,
        output_path=output_path,
        email_body=email_body,
        sample_name=sample_name,
        seq_date=seq_date,
        chemstation_mode=chemstation_mode,
        prepare_done=prepare_done,
    )


def try_pending_email_retry(
    state_path: str,
    script_dir: str,
    excel_output_dir: str,
    *,
    send_email: bool = True,
    chemstation_mode: str = "auto",
) -> Tuple[bool, str]:
    """엑셀-only 처리 후 남은 메일을 재발송. (성공 여부, 요약 메시지)"""
    if not send_email:
        return False, ""

    state = load_send_state(state_path)
    pending = get_pending_email_retry(state)
    if not pending:
        return False, ""

    allowed, slot_reason = can_auto_send_for_mode(state_path, chemstation_mode)
    if not allowed:
        return False, f"{slot_reason} — 재발송 보류"

    excel_path = pending["excel_path"]
    if not os.path.isfile(excel_path):
        clear_pending_email_retry(state_path)
        return False, "재발송 대기 엑셀 파일 없음 — 대기 항목 삭제"

    from gc_mailer import send_email_via_smtp

    print(f"\n[진행] 미발송 메일 재시도 — {os.path.basename(excel_path)}")
    attempts_before = int(pending.get("retry_count", 0))
    ok = send_email_via_smtp(
        excel_path,
        pending["sample_name"],
        pending["seq_date"],
        pending["body_text"],
        script_dir,
        excel_output_dir,
        smtp_wait_max_sec=PENDING_EMAIL_SMTP_WAIT_MAX_SEC,
        smtp_send_retries=PENDING_EMAIL_SEND_RETRIES,
    )
    if ok:
        from gc_work_job import record_session_mail_complete

        summary = f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} — 메일 재발송"
        record_session_mail_complete(state_path, excel_output_dir, summary)
        log_gc_event(
            excel_output_dir,
            "mail_retry_ok",
            summary,
            excel=os.path.basename(excel_path),
            attempts=attempts_before,
        )
        return True, summary
    state = load_send_state(state_path)
    pending = get_pending_email_retry(state)
    if pending:
        pending["retry_count"] = int(pending.get("retry_count", 0)) + 1
        pending["last_retry_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        save_send_state(state_path, state)
        log_gc_event(
            excel_output_dir,
            "mail_retry_fail",
            "미발송 메일 재시도 실패 — watch 자동 재시도 계속",
            excel=os.path.basename(excel_path),
            attempts=pending["retry_count"],
        )
    return False, "미발송 메일 재시도 실패 — watch가 자동 재시도 (핫스팟·SMTP 준비 대기)"


def recover_stale_pending_email(state_path: str, excel_output_dir: str) -> bool:
    """이전 엑셀-only·pending 메일 기록을 active_work_job으로 복구."""
    from gc_work_job import recover_stale_job_from_state

    return recover_stale_job_from_state(state_path, excel_output_dir)


def has_new_data_since_last_run(state_path: str, sequence_folder: str, data_path: str = "", mode: str = "auto") -> bool:
    """마지막 처리 이후 새 Report(acam/PDF) 데이터가 있는지."""
    state = load_send_state(state_path)
    if mode == "gc1":
        from gc_gc1 import get_latest_pdf_mtime

        latest_mtime = get_latest_pdf_mtime(sequence_folder)
        if latest_mtime is None:
            return False
        last_mtime = state.get("last_processed_acam_mtime")
        if last_mtime is None:
            return True
        return latest_mtime > last_mtime
    elif resolve_chemstation_mode and get_latest_report_mtime:
        if resolve_chemstation_mode(data_path or sequence_folder, mode) == "chem32":
            latest_mtime = get_latest_report_mtime(sequence_folder)
        else:
            latest_mtime = get_latest_injection_acam_mtime(sequence_folder)
    else:
        latest_mtime = get_latest_injection_acam_mtime(sequence_folder)
    if latest_mtime is None:
        return False
    last_mtime = state.get("last_processed_acam_mtime")
    if last_mtime is None:
        return True
    return latest_mtime > last_mtime
