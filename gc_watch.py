# -*- coding: utf-8 -*-
"""
gc_watch.py — --watch 핫스팟 감시 루프

=============================================================================
[PC 명칭]  docs/PC_NAMING.md — 본 모듈은 **장비 PC** 전용
=============================================================================

  GC1 **장비** PC: iPhone 핫스팟 세션당 PDF·엑셀·메일 1회 (Desktop\\박은규)
  GC2/GC3 **장비** PC: iptime 3종 Wi-Fi, acam mtime, gc_work_job 단계 재개 (Desktop\\KCH)

  은규 PC / 차헌 PC 에서는 --watch 를 돌리지 않음.

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
  2) 연결 유지 중에는 pipeline 재실행 안 함 (GC1·GC2 공통)
  3) 바탕화면 MMDDHHmm.txt 갱신 — **핫스팟 연결 중만** (gc_status ±5분 검증)

=============================================================================
[핫스pot edge — GC2/GC3 vs GC1]
=============================================================================

  공통:
    · 새로 연결(just_connected)일 때만 _on_hotspot_connected()
    · 순간 끊김: 끊긴 시간 < HOTSPOT_RECONNECT_MIN_SEC → 동일 세션 (GC1 90s, GC2 45s)

  GC2/GC3: 새 acam/Report + 오전/오후 메일 각 1회
  GC1: 핫스pot 세션당 PDF·엑셀·메일 1회 (슬롯 한도 없음, 켜진 채 반복 없음)
       충분히 껐다 켠 재연결 → 세션 1회 더 (Autochro force export)

[새 날짜 시퀀스 — GC2/GC3]
  시료명 없으면 watch skip. force 시 --sample-name 지정.
"""

from __future__ import annotations

import os
import time
from dataclasses import dataclass
from datetime import datetime

from gc_config import AppConfig, hotspot_reconnect_min_sec
from gc_chem32 import find_active_sample_folder, resolve_chemstation_mode
from gc_gc1 import find_active_pdf
from gc_chemstation import find_sequence_folder
from gc_kch import check_sample_name_before_processing
from gc_pipeline import run_processing
from gc_state import (
    gc1_unlimited_auto_send,
    has_new_data_since_last_run,
    load_send_state,
    mark_gc1_pdf_attempt_failed,
    record_processing_result,
    recover_stale_pending_email,
    should_retry_gc1_pdf,
    try_pending_email_retry,
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
        self._pipeline_running = False
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
        if gc1_unlimited_auto_send(mode):
            mail_rule = (
                f"핫스pot 연결 세션당 PDF·엑셀·메일 1회 "
                f"(끊었다가 {reconnect_sec}초+ 후 재연결 시 1회 더)"
            )
        else:
            mail_rule = "엑셀·메일 (오전 1회 + 오후 1회, 새 데이터 있을 때)"
        print(f"[안내] 핫스팟 감시 시작 — {interval}초 간격, SSID: {self.config.required_ssid}")
        print(f"       {mail_rule}")
        print(f"       순간 끊김({reconnect_sec}초 미만 재연결) — 동일 세션, 중복 없음")
        print(f"       바탕화면 확인: MMDDHHmm.txt (핫스팟 연결 중에만 갱신)")
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
        wifi_ready = is_required_hotspot_connected(
            self.config.required_ssid,
            self.config.skip_wifi_check,
        )
        self._reporter.publish(
            alive=True,
            status_code=code,
            message=message,
            wifi_ssid=get_connected_wifi_ssid(),
            wifi_ready=wifi_ready,
            **extra,
        )
        if code == "error":
            self._schedule_error_recovery(message, **extra)

    def _schedule_error_recovery(self, message: str, **extra) -> None:
        try:
            from gc_error_handler import enqueue_and_recover

            enqueue_and_recover(
                self.config.excel_output_dir,
                self.script_dir,
                status_code="error",
                message=message,
                sequence_folder=extra.get("sequence_folder"),
                watch_status_path=self.watch_opts.status_json_path,
            )
        except Exception as exc:
            print(f"[경고] 오류 복구 예약 실패: {exc}")

    def _publish_stopped(self) -> None:
        self._reporter.publish(
            alive=False,
            status_code="stopped",
            message="감시 종료됨 — gc_start_watch.bat 로 다시 시작",
            wifi_ssid=get_connected_wifi_ssid(),
        )

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
            self._hotspot_was_connected = False
            reason = hotspot_wait_reason(self.config.required_ssid)
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
                        f"동일 세션 ({min_gap}초 미만 재연결, 재처리 안 함)"
                    )
                    self._publish("wifi_ok", msg)
                    print(f"[안내] {msg}")
                    return
            just_connected = True
        else:
            just_connected = False

        self._hotspot_was_connected = True

        if not just_connected:
            if self._pipeline_running:
                self._publish("processing", "GC1 처리 진행 중 — 완료까지 대기")
                return
            if gc1_unlimited_auto_send(self.config.chemstation_mode) and self._gc1_has_pending_work():
                print("\n[감지] GC1 새 CRM/PDF — 핫스팟 연결 유지 중 처리")
                self._on_hotspot_connected(just_connected=False)
                return
            self._publish("wifi_ok", "핫스팟 연결 유지 중 — 새 CRM/PDF 있으면 자동 처리")
            return

        print("\n[감지] 핫스팟 연결됨 — 새 데이터 확인")
        self._on_hotspot_connected(just_connected=True)

    def _gc1_has_pending_work(self) -> bool:
        """GC1: 핫스pot 유지 중에도 CRM 갱신·새 PDF면 재처리."""
        try:
            from gc_autochro import is_autochro_enabled, resolve_crm_path, should_export_crm
        except ImportError:
            is_autochro_enabled = lambda: False  # type: ignore[assignment]
            resolve_crm_path = None  # type: ignore[assignment]
            should_export_crm = None  # type: ignore[assignment]

        if is_autochro_enabled() and resolve_crm_path and should_export_crm:
            crm_path = resolve_crm_path()
            if crm_path and os.path.isfile(crm_path):
                should, _ = should_export_crm(self.watch_opts.send_state_file, crm_path, force=False)
                if should:
                    return True

        pdf_path = find_active_pdf(self.config)
        if pdf_path and should_retry_gc1_pdf(self.watch_opts.send_state_file, pdf_path):
            return True
        return False

    def _record_result(self, result) -> None:
        if not result.ok or not result.sequence_folder or result.latest_acam_mtime is None:
            return
        record_processing_result(
            self.watch_opts.send_state_file,
            sequence_folder=result.sequence_folder,
            latest_mtime=result.latest_acam_mtime,
            action_summary=result.action_summary or "",
            email_sent=result.email_sent,
            send_email=self.config.send_email,
            count_email_toward_limit=not gc1_unlimited_auto_send(self.config.chemstation_mode),
            output_path=result.output_path,
            email_body=result.email_body,
            sample_name=result.sample_name,
            seq_date=result.seq_date,
            chemstation_mode=self.config.chemstation_mode,
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

    def _on_hotspot_connected(self, *, just_connected: bool = True) -> None:
        """핫스팟 edge: 일일 한도 → 미발송 메일 재시도 → 새 데이터 → pipeline."""
        if self._pipeline_running:
            return
        self._publish("wifi_connected", "핫스팟 연결됨 — 새 데이터 확인 중")

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

        if self.config.send_email and not self.config.skip_wifi_check:
            net_reason = smtp_internet_wait_reason()
            if net_reason:
                self._publish(
                    "waiting_internet",
                    f"{net_reason} — 엑셀 먼저 처리, 메일은 SMTP 준비 후 최대 90초 대기",
                )
                print(f"[안내] {net_reason} — 엑셀 처리 후 SMTP 준비될 때까지 대기·재시도")

        retry_summary = self._try_pending_email_retry()
        if retry_summary:
            self._publish(
                "done",
                "미발송 메일 재발송 완료 — 새 데이터도 확인 중",
                last_action=retry_summary,
            )

        if not os.path.isdir(self.config.data_path) and self.config.chemstation_mode != "gc1":
            print(f"[오류] Data 경로 없음: {self.config.data_path}")
            return

        if self.config.chemstation_mode == "gc1":
            try:
                from gc_autochro import ensure_gc1_pdf_exported, is_autochro_enabled
            except ImportError:
                is_autochro_enabled = lambda: False  # type: ignore
                ensure_gc1_pdf_exported = None  # type: ignore

            pdf_path = find_active_pdf(self.config)
            if not pdf_path and not (is_autochro_enabled() and ensure_gc1_pdf_exported):
                self._publish("no_new_data", "GC1 PDF 없음 — Desktop\\박은규 폴더 확인")
                return

            if is_autochro_enabled() and ensure_gc1_pdf_exported:
                export_ok, export_pdf, export_msg = ensure_gc1_pdf_exported(
                    self.config.excel_output_dir,
                    self.watch_opts.send_state_file,
                    force=just_connected,
                )
                if export_ok and export_pdf:
                    print(f"[Autochro] PDF 내보내기 완료 — {export_msg}")
                    os.environ["GC1_SKIP_AUTOCHRO_EXPORT"] = "1"
                    pdf_path = export_pdf
                elif export_ok:
                    print(f"[Autochro] {export_msg}")
                    pdf_path = find_active_pdf(self.config) or pdf_path
                else:
                    self._publish(
                        "error",
                        f"Autochro PDF 내보내기 실패 — {export_msg}",
                    )
                    print(f"[오류] Autochro PDF 내보내기 실패 — {export_msg}")
                    return

            pdf_path = find_active_pdf(self.config) or pdf_path
            if not pdf_path:
                self._publish("no_new_data", "GC1 PDF 없음 — Desktop\\박은규 폴더 확인")
                return

            self._publish(
                "processing",
                "GC1 핫스pot 세션 — PDF·엑셀·메일 처리 중",
                sequence_folder=pdf_path,
            )
            print(f"[진행] GC1 핫스pot 세션 — {pdf_path}")
            self._pipeline_running = True
            try:
                result = run_processing(self.config, self.script_dir)
            finally:
                os.environ.pop("GC1_SKIP_AUTOCHRO_EXPORT", None)
                self._pipeline_running = False
            if result.ok and result.sequence_folder and result.latest_acam_mtime is not None:
                self._record_result(result)
                self._publish(
                    "done",
                    "GC1 처리 완료 — 핫스pot 유지 중 반복 없음, 끊었다 재연결 시 다시",
                    last_action=result.action_summary,
                    sequence_folder=result.sequence_folder,
                )
            else:
                reason = result.fail_reason or "처리 실패"
                failed_pdf = result.sequence_folder or pdf_path
                if failed_pdf:
                    mark_gc1_pdf_attempt_failed(
                        self.watch_opts.send_state_file,
                        failed_pdf,
                        reason,
                    )
                self._publish(
                    "error",
                    f"{reason} — PDF·시료명 확인 (동일 PDF watch 재시도 안 함)",
                    sequence_folder=failed_pdf,
                )
            return

        mode = resolve_chemstation_mode(self.config.data_path, self.config.chemstation_mode)
        if mode == "chem32":
            sample_folder = find_active_sample_folder(self.config.data_path, self.config.sequence_folder)
            if not sample_folder:
                self._publish("no_new_data", "Chem32 시료 폴더 없음")
                return
            if not has_new_data_since_last_run(
                self.watch_opts.send_state_file,
                sample_folder,
                self.config.data_path,
                self.config.chemstation_mode,
            ):
                if retry_summary:
                    return
                state = load_send_state(self.watch_opts.send_state_file)
                last_action = state.get("last_action_summary") or "이전 처리와 동일"
                self._publish(
                    "no_new_data",
                    "Chem32 — 마지막 처리 이후 새 Report 없음",
                    last_action=last_action,
                    sequence_folder=sample_folder,
                )
                print("[안내] 마지막 처리 이후 새 Report 없음")
                return
            self._publish(
                "processing",
                "Chem32 새 Report — FID+TCD 엑셀 처리 중",
                sequence_folder=sample_folder,
            )
            print(f"[진행] Chem32 — {sample_folder}")
            result = run_processing(self.config, self.script_dir)
            if result.ok and result.sequence_folder and result.latest_acam_mtime is not None:
                self._record_result(result)
                self._publish(
                    "done",
                    "Chem32 처리 완료 — 핫스팟 재연결 시 다시 확인",
                    last_action=result.action_summary,
                    sequence_folder=result.sequence_folder,
                )
            else:
                reason = result.fail_reason or "처리 실패"
                self._publish(
                    "error",
                    f"{reason} — 수동 실행 또는 Report 생성 확인",
                    sequence_folder=sample_folder,
                )
            return

        sequence_folder = find_sequence_folder(
            self.config.data_path,
            self.config.sequence_date,
            self.config.sequence_folder,
        )
        if not sequence_folder:
            self._publish("no_new_data", "새 데이터 없음 — 시퀀스 폴더 없음")
            return

        if not has_new_data_since_last_run(
            self.watch_opts.send_state_file,
            sequence_folder,
            self.config.data_path,
            self.config.chemstation_mode,
        ):
            if retry_summary:
                return
            state = load_send_state(self.watch_opts.send_state_file)
            last_action = state.get("last_action_summary") or "이전 처리와 동일"
            self._publish(
                "no_new_data",
                "핫스팟 연결됨 — 마지막 처리 이후 새 데이터 없음",
                last_action=last_action,
                sequence_folder=sequence_folder,
            )
            print("[안내] 마지막 처리 이후 새 데이터 없음")
            return

        sample_block = check_sample_name_before_processing(sequence_folder, self.config)
        if sample_block:
            self._publish(
                "need_sample_name",
                sample_block,
                sequence_folder=sequence_folder,
            )
            print(f"[중단] {sample_block}")
            return

        self._publish(
            "processing",
            "새 데이터 있음 — 엑셀·메일 처리 중",
            sequence_folder=sequence_folder,
        )
        print(f"[진행] 새 데이터 — {sequence_folder}")

        result = run_processing(self.config, self.script_dir)
        if result.ok and result.sequence_folder and result.latest_acam_mtime is not None:
            self._record_result(result)
            self._publish(
                "done",
                "처리 완료 — 핫스팟 해제 후 재연결 시 다시 확인",
                last_action=result.action_summary,
                sequence_folder=result.sequence_folder,
            )
        else:
            reason = result.fail_reason or "처리 실패"
            code = "need_sample_name" if "시료" in reason else "error"
            self._publish(
                code,
                f"{reason} — 수동 실행 필요" if code == "need_sample_name" else f"{reason} — 핫스팟 재연결 후 재시도",
                sequence_folder=sequence_folder,
            )


def run_watch_loop(config: AppConfig, watch_opts: WatchOptions, script_dir: str) -> None:
    """WatchRunner 진입점."""
    WatchRunner(config, watch_opts, script_dir).run_forever()
