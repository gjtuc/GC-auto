# -*- coding: utf-8 -*-
"""
gc_watch.py — --watch 핫스팟 감시 루프

=============================================================================
[전체 구조 — gc_automation.py 와 분리된 두 갈래]
=============================================================================

  (A) --watch  … 핫스pot 연결 edge 에서 자동 처리 (본 파일)
  (B) force    … 「시작」「go」「진행」 등 개시 요청 (gc_request → pipeline)
                 watch·핫스pot·일일한도와 무관

=============================================================================
[매 tick(기본 15초)]
=============================================================================

  1) Wi-Fi SSID 확인 — REQUIRED_HOTSPOT 과 일치할 때만 ChemStation/PDF 접근
  2) 연결 유지 중 — pending 메일이 있으면 간격마다 SMTP 재시도 (성공까지)
  3) 순간 끊김(약한 신호) — pipeline 은 안 하지만 pending 메일은 즉시 재시도
  4) 바탕화면 MMDDHHmm.txt 갱신 — watch 생존 신호 (gc_status ±5분 검증)

=============================================================================
[핫스pot edge — 미완료 작업 재개]
=============================================================================

  · 핫스pot **연결만**으로 pipeline 실행하지 않음 (불안정)
  · 새 acam/Report/PDF 있을 때만 **새 작업** 시작
  · 작업 중 핫스pot 끊김 → active_work_job 미완료
  · 재연결 시 **last_step** 기록 지점부터 다시 (끊김 중 엑셀 → 엑셀 재작성 후 메일)
  · **메일 발송 성공** 시에만 session_complete_log 1회
  · 순간 끊김(< HOTSPOT_RECONNECT_MIN_SEC) — 동일 세션, pipeline 재실행 안 함
"""

from __future__ import annotations

import os
import time
from dataclasses import dataclass
from datetime import datetime

from gc_config import AppConfig, hotspot_reconnect_min_sec, PENDING_EMAIL_RETRY_INTERVAL_SEC
from gc_chem32 import find_active_sample_folder, resolve_chemstation_mode
from gc_gc1 import find_active_pdf
from gc_chemstation import find_sequence_folder
from gc_kch import check_sample_name_before_processing
from gc_pipeline import run_processing
from gc_state import (
    get_pending_email_retry,
    has_new_data_since_last_run,
    load_send_state,
    record_processing_result,
    recover_stale_pending_email,
    try_pending_email_retry,
)
from gc_work_job import (
    audit_resume_plan,
    ensure_active_job,
    get_active_job,
    invalidate_steps_from,
    job_needs_resume,
    mark_job_interrupted,
    mark_job_step,
    resume_start_step,
    set_job_last_step,
    STEP_LABELS,
    update_active_job,
)
from gc_status import StatusReporter
from gc_wifi import (
    check_runtime_gate,
    get_connected_wifi_ssid,
    hotspot_wait_reason,
    is_required_hotspot_connected,
    smtp_internet_wait_reason,
)


@dataclass
class WatchOptions:
    """--watch 전용 CLI 옵션."""

    watch_interval: int = 15
    status_json_path: str = ""
    status_txt_path: str = ""
    send_state_file: str = ""


class WatchRunner:
    """
    핫스pot edge-trigger 감시.

    _hotspot_was_connected / _hotspot_lost_at:
      순간 끊김(약한 신호)과 사용자가 껐다 켠 재연결을 구분합니다.
      gap < hotspot_reconnect_min_sec → pipeline 호출 안 함.
    """

    def __init__(self, config: AppConfig, watch_opts: WatchOptions, script_dir: str):
        self.config = config
        self.watch_opts = watch_opts
        self.script_dir = script_dir
        self._hotspot_was_connected = False
        self._hotspot_lost_at: float | None = None
        self._last_pending_retry_at: float = 0.0
        self._processing_active: bool = False
        self._current_job_step: str | None = None
        self._started_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self._reporter = StatusReporter(
            watch_opts.status_json_path,
            watch_opts.status_txt_path,
            config.required_ssid,
            watch_opts.watch_interval,
            watch_opts.send_state_file,
            self._started_at,
        )

    def run_forever(self) -> None:
        """Ctrl+C 또는 프로세스 종료까지 루프."""
        interval = self.watch_opts.watch_interval
        mode = self.config.chemstation_mode
        reconnect_sec = hotspot_reconnect_min_sec(mode)
        mail_rule = (
            f"새 데이터 또는 미완료 작업 시 처리 — 메일 성공 시 세션 1회 "
            f"(끊김 후 {reconnect_sec}초+ 재연결 시 재개)"
        )
        print(f"[안내] 핫스팟 감시 시작 — {interval}초 간격, SSID: {self.config.required_ssid}")
        print(f"       {mail_rule}")
        print(f"       순간 끊김({reconnect_sec}초 미만 재연결) — pipeline 중복 없음, 미발송 메일은 계속 재시도")
        print(f"       미발송 메일: 핫스팟 붙는 동안 {PENDING_EMAIL_RETRY_INTERVAL_SEC}초마다 자동 재발송")
        print(f"       바탕화면 확인: MMDDHHmm.txt")
        print(f"       수동 force: gc_동작해줘.bat 또는 Cursor")

        self._publish("starting", "감시 시작됨")

        if recover_stale_pending_email(self.watch_opts.send_state_file, self.config.excel_output_dir):
            print("[안내] 이전 엑셀-only 처리 감지 — 다음 핫스팟 연결 시 메일 재시도")

        try:
            while True:
                self._tick()
                time.sleep(interval)
        except KeyboardInterrupt:
            print("\n[안내] 사용자가 감시를 종료했습니다 (Ctrl+C).")
        finally:
            self._publish_stopped()

    def _publish(self, code: str, message: str, **extra) -> None:
        self._reporter.publish(
            alive=True,
            status_code=code,
            message=message,
            wifi_ssid=get_connected_wifi_ssid(),
            **extra,
        )

    def _publish_stopped(self) -> None:
        self._reporter.publish(
            alive=False,
            status_code="stopped",
            message="감시 종료됨 — gc_start_watch.bat 로 다시 시작",
            wifi_ssid=get_connected_wifi_ssid(),
        )

    def _has_pending_email(self) -> bool:
        return bool(get_pending_email_retry(load_send_state(self.watch_opts.send_state_file)))

    def _retry_pending_email_if_due(self, force: bool = False) -> str | None:
        """
        pending 메일 자동 재발송.

        force=True: 순간 재연결(약한 핫스팟) 직후 — 간격 무시하고 즉시 1회 시도.
        """
        if not self.config.send_email or not self._has_pending_email():
            return None

        interval = max(15, PENDING_EMAIL_RETRY_INTERVAL_SEC)
        elapsed = time.monotonic() - self._last_pending_retry_at
        if not force and elapsed < interval:
            return None

        self._last_pending_retry_at = time.monotonic()
        return self._try_pending_email_retry()

    def _tick(self) -> None:
        """
        watch_interval(기본 15초)마다 1회.

        상태 머신:
          Wi-Fi 없음 → lost_at 기록
          Wi-Fi 있음 + was_connected → 유지(아무 것도 안 함)
          Wi-Fi 있음 + !was_connected → edge; min_gap 검사 후 _on_hotspot_connected
        """
        if not is_required_hotspot_connected(self.config.required_ssid, self.config.skip_wifi_check):
            if self._hotspot_was_connected:
                self._hotspot_lost_at = time.monotonic()
                state = load_send_state(self.watch_opts.send_state_file)
                if self._processing_active or job_needs_resume(state, self.config.send_email):
                    mark_job_interrupted(
                        self.watch_opts.send_state_file,
                        "핫스pot 끊김",
                        last_step=self._current_job_step,
                    )
            self._hotspot_was_connected = False
            reason = hotspot_wait_reason(self.config.required_ssid)
            if self._has_pending_email():
                state = load_send_state(self.watch_opts.send_state_file)
                pending = state.get("pending_email_retry") or {}
                attempts = pending.get("retry_count", 0)
                reason = (
                    f"{reason} — 미발송 메일 대기 ({attempts}회 시도) "
                    f"핫스팟·SMTP 잠깐 붙으면 자동 재발송"
                )
            self._publish("waiting_wifi", reason)
            print(f"[대기] {reason}")
            return

        min_gap = hotspot_reconnect_min_sec(self.config.chemstation_mode)
        if not self._hotspot_was_connected:
            if self._hotspot_lost_at is not None:
                gap_sec = time.monotonic() - self._hotspot_lost_at
                if gap_sec < min_gap:
                    self._hotspot_was_connected = True
                    msg = (
                        f"핫스팟 순간 끊김 ({int(gap_sec)}초) — "
                        f"동일 세션 ({min_gap}초 미만, pipeline 재실행 안 함)"
                    )
                    retry_summary = self._retry_pending_email_if_due(force=True)
                    if retry_summary:
                        msg = f"{msg} — 미발송 메일 발송 완료"
                        self._publish("done", msg, last_action=retry_summary)
                        print(f"[성공] {retry_summary}")
                    else:
                        if self._has_pending_email():
                            net = smtp_internet_wait_reason()
                            if net:
                                msg = f"{msg} — SMTP 대기 ({net})"
                        self._publish("wifi_ok", msg)
                        print(f"[안내] {msg}")
                    return
            just_connected = True
        else:
            just_connected = False

        self._hotspot_was_connected = True

        if not just_connected:
            retry_summary = self._retry_pending_email_if_due()
            if retry_summary:
                self._publish(
                    "done",
                    "미발송 메일 재발송 완료 — 핫스팟 유지 중",
                    last_action=retry_summary,
                )
                print(f"[성공] {retry_summary}")
                return
            if self._has_pending_email():
                net = smtp_internet_wait_reason()
                extra = f" — SMTP: {net}" if net else ""
                self._publish(
                    "waiting_internet",
                    f"핫스팟 연결 — 미발송 메일 재시도 중{extra}",
                )
                print(f"[안내] 미발송 메일 재시도 대기{extra}")
                return
            self._publish("wifi_ok", "핫스팟 연결 유지 중 — 재연결 시 새 데이터 확인")
            return

        print("\n[감지] 핫스팟 연결됨 — 새 데이터 확인")
        self._on_hotspot_connected()

    def _record_result(self, result, prepare_done: bool = True) -> None:
        if not result.ok or not result.sequence_folder or result.latest_acam_mtime is None:
            return
        record_processing_result(
            self.watch_opts.send_state_file,
            sequence_folder=result.sequence_folder,
            latest_mtime=result.latest_acam_mtime,
            action_summary=result.action_summary or "",
            email_sent=result.email_sent,
            send_email=self.config.send_email,
            count_email_toward_limit=False,
            output_path=result.output_path,
            email_body=result.email_body,
            sample_name=result.sample_name,
            seq_date=result.seq_date,
            chemstation_mode=self.config.chemstation_mode,
            prepare_done=prepare_done,
        )

    def _try_pending_email_retry(self) -> str | None:
        """미발송 메일 재시도. 성공 시 action_summary 반환."""
        sent, summary = try_pending_email_retry(
            self.watch_opts.send_state_file,
            self.script_dir,
            self.config.excel_output_dir,
            send_email=self.config.send_email,
            chemstation_mode=self.config.chemstation_mode,
        )
        if not summary:
            return None
        if sent:
            print(f"[성공] {summary}")
            return summary
        print(f"[안내] {summary}")
        return None

    def _finalize_processing(
        self,
        result,
        *,
        prepare_done: bool = True,
        sequence_folder: str | None = None,
    ) -> None:
        folder = sequence_folder or result.sequence_folder
        if result.ok and result.sequence_folder and result.latest_acam_mtime is not None:
            self._record_result(result, prepare_done=prepare_done)
            if result.email_sent or not self.config.send_email:
                self._publish(
                    "done",
                    "작업 세션 완료 — 메일 발송까지 완료",
                    last_action=result.action_summary,
                    sequence_folder=result.sequence_folder,
                )
            else:
                self._publish(
                    "waiting_internet",
                    "엑셀 완료 · 메일 미완료 — 핫스pot 재연결 시 메일 단계 재개",
                    last_action=result.action_summary,
                    sequence_folder=result.sequence_folder,
                )
        else:
            reason = result.fail_reason or "처리 실패"
            mark_job_interrupted(
                self.watch_opts.send_state_file,
                reason,
                last_step=self._current_job_step,
            )
            self._publish(
                "error",
                f"{reason} — 핫스pot 재연결 후 미완료 작업 재개",
                sequence_folder=folder,
            )

    def _gc1_prepare_export(self) -> tuple[bool, str | None]:
        try:
            from gc_autochro import ensure_gc1_pdf_exported, is_autochro_enabled
        except ImportError:
            is_autochro_enabled = lambda: False  # type: ignore
            ensure_gc1_pdf_exported = None  # type: ignore

        pdf_path = find_active_pdf(self.config)
        if not pdf_path and not (is_autochro_enabled() and ensure_gc1_pdf_exported):
            self._publish("no_new_data", "GC1 PDF 없음 — Desktop\\박은규 폴더 확인")
            return False, None

        if is_autochro_enabled() and ensure_gc1_pdf_exported:
            export_ok, export_pdf, export_msg = ensure_gc1_pdf_exported(
                self.config.excel_output_dir,
                self.watch_opts.send_state_file,
                force=True,
            )
            if export_ok and export_pdf:
                print(f"[Autochro] PDF보내기 완료 — {export_msg}")
                os.environ["GC1_SKIP_AUTOCHRO_EXPORT"] = "1"
                pdf_path = export_pdf
            elif export_ok:
                print(f"[Autochro] {export_msg}")
                pdf_path = find_active_pdf(self.config) or pdf_path
            else:
                self._publish("error", f"Autochro PDF보내기 실패 — {export_msg}")
                print(f"[오류] Autochro PDF보내기 실패 — {export_msg}")
                return False, None

        pdf_path = find_active_pdf(self.config) or pdf_path
        if not pdf_path:
            self._publish("no_new_data", "GC1 PDF 없음 — Desktop\\박은규 폴더 확인")
            return False, None
        return True, pdf_path

    def _execute_pipeline(
        self,
        pipeline_mode: str,
        sequence_folder: str,
        label: str,
        *,
        gc1_prepare: bool = False,
    ) -> None:
        ensure_active_job(
            self.watch_opts.send_state_file,
            sequence_folder=sequence_folder,
            pipeline_mode=pipeline_mode,
            chemstation_mode=self.config.chemstation_mode,
        )
        self._publish("processing", label, sequence_folder=sequence_folder)
        print(f"[진행] {label} — {sequence_folder}")

        prepare_done = pipeline_mode != "gc1"
        self._processing_active = True
        try:
            if gc1_prepare:
                self._current_job_step = "prepare"
                set_job_last_step(self.watch_opts.send_state_file, "prepare")
                ok, pdf_path = self._gc1_prepare_export()
                if not ok:
                    mark_job_interrupted(
                        self.watch_opts.send_state_file,
                        "GC1 전처리 실패",
                        last_step="prepare",
                    )
                    return
                prepare_done = True
                mark_job_step(self.watch_opts.send_state_file, "prepare", True)
                if pdf_path:
                    sequence_folder = pdf_path
                    update_active_job(
                        self.watch_opts.send_state_file,
                        sequence_folder=pdf_path,
                    )
                os.environ["GC1_SKIP_AUTOCHRO_EXPORT"] = "1"

            self._current_job_step = "excel"
            set_job_last_step(self.watch_opts.send_state_file, "excel")
            result = run_processing(self.config, self.script_dir)
            if (
                self.config.send_email
                and result.ok
                and result.output_path
                and not result.email_sent
            ):
                self._current_job_step = "mail"
                set_job_last_step(self.watch_opts.send_state_file, "mail")
        finally:
            self._processing_active = False
            os.environ.pop("GC1_SKIP_AUTOCHRO_EXPORT", None)

        self._finalize_processing(
            result,
            prepare_done=prepare_done,
            sequence_folder=sequence_folder,
        )

    def _resume_incomplete_work(self) -> bool:
        """미완료 작업 — 마지막 진행 단계부터 다시 수행."""
        state_path = self.watch_opts.send_state_file
        state = load_send_state(state_path)
        if not job_needs_resume(state, self.config.send_email):
            return False

        job = get_active_job(state)
        if not job:
            if get_pending_email_retry(state):
                self._try_pending_email_retry()
            return True

        start = resume_start_step(job, self.config.send_email)
        if not start:
            return True

        plan = audit_resume_plan(job, self.config.send_email)
        labels = [STEP_LABELS.get(s, s) for s in plan]
        print(f"[재개] 다시 수행: {' → '.join(labels)}")
        if job.get("interrupted"):
            print(f"[재개] 이전 중단: {job.get('fail_reason') or '핫스pot 끊김'}")

        invalidate_steps_from(state_path, start)

        if start == "mail":
            retry_summary = self._try_pending_email_retry()
            if retry_summary:
                self._publish(
                    "done",
                    "메일 단계 재시도 완료",
                    last_action=retry_summary,
                )
            return True

        mode = job.get("pipeline_mode") or "8860"
        folder = job.get("sequence_folder") or ""
        label = f"재개 — {STEP_LABELS.get(start, start)}부터"
        gc1_prepare = start == "prepare"

        if mode == "gc1":
            self._execute_pipeline("gc1", folder, label, gc1_prepare=gc1_prepare)
        elif mode == "chem32":
            self._execute_pipeline("chem32", folder, label)
        else:
            self._execute_pipeline("8860", folder, label)
        return True

    def _on_hotspot_connected(self) -> None:
        """핫스pot edge: 미완료 재개 → (새 데이터 있을 때만) 새 작업."""
        self._publish("wifi_connected", "핫스pot 연결 — 미완료 작업·새 데이터 확인")

        allowed, reason = check_runtime_gate(
            self.config.required_ssid,
            self.config.send_email,
            self.watch_opts.send_state_file,
            skip_wifi_check=self.config.skip_wifi_check,
            force=False,
            chemstation_mode=self.config.chemstation_mode,
        )
        if not allowed:
            code = "waiting_quota" if "메일" in reason else "waiting_wifi"
            self._publish(code, reason)
            print(f"[대기] {reason}")
            return

        if self._resume_incomplete_work():
            return

        if not os.path.isdir(self.config.data_path) and self.config.chemstation_mode != "gc1":
            print(f"[오류] Data 경로 없음: {self.config.data_path}")
            return

        state_path = self.watch_opts.send_state_file

        if self.config.chemstation_mode == "gc1":
            pdf_path = find_active_pdf(self.config)
            if not pdf_path:
                self._publish("no_new_data", "GC1 PDF 없음")
                return
            if not has_new_data_since_last_run(
                state_path,
                pdf_path,
                self.config.excel_output_dir,
                "gc1",
            ):
                self._publish("no_new_data", "GC1 — 마지막 완료 이후 새 PDF 없음")
                print("[안내] 새 PDF 없음 — 미완료 작업 없음")
                return
            self._execute_pipeline(
                "gc1",
                pdf_path,
                "GC1 새 PDF — PDF·엑셀·메일 처리",
                gc1_prepare=True,
            )
            return

        mode = resolve_chemstation_mode(self.config.data_path, self.config.chemstation_mode)
        if mode == "chem32":
            sample_folder = find_active_sample_folder(self.config.data_path, self.config.sequence_folder)
            if not sample_folder:
                self._publish("no_new_data", "Chem32 시료 폴더 없음")
                return
            if not has_new_data_since_last_run(
                state_path,
                sample_folder,
                self.config.data_path,
                self.config.chemstation_mode,
            ):
                self._publish("no_new_data", "Chem32 — 마지막 완료 이후 새 Report 없음")
                print("[안내] 새 Report 없음")
                return
            self._execute_pipeline(
                "chem32",
                sample_folder,
                "Chem32 새 Report — FID+TCD 엑셀·메일",
            )
            return

        sequence_folder = find_sequence_folder(
            self.config.data_path,
            self.config.sequence_date,
            self.config.sequence_folder,
        )
        if not sequence_folder:
            self._publish("no_new_data", "시퀀스 폴더 없음")
            return

        if not has_new_data_since_last_run(
            state_path,
            sequence_folder,
            self.config.data_path,
            self.config.chemstation_mode,
        ):
            self._publish("no_new_data", "마지막 완료 이후 새 acam 없음")
            print("[안내] 새 acam 없음")
            return

        sample_block = check_sample_name_before_processing(sequence_folder, self.config)
        if sample_block:
            self._publish("need_sample_name", sample_block, sequence_folder=sequence_folder)
            print(f"[중단] {sample_block}")
            return

        self._execute_pipeline(
            "8860",
            sequence_folder,
            "새 acam — 엑셀·메일 처리",
        )


def run_watch_loop(config: AppConfig, watch_opts: WatchOptions, script_dir: str) -> None:
    """WatchRunner 진입점."""
    WatchRunner(config, watch_opts, script_dir).run_forever()
