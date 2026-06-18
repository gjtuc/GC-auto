# -*- coding: utf-8 -*-
"""
gc_pipeline.py — 시퀀스 1건 처리 파이프라인 (엑셀 + 메일)

=============================================================================
[진입점]  run_processing(config, script_dir)
=============================================================================

  chemstation_mode 에 따라 분기:

  gc1  → run_processing_gc1()     Autochro PDF · gc_gc1 파싱 · FID/TCD 엑셀
  chem32 → run_processing_chem32()
  8860 → ChemStation acam 파싱 (GC2)

=============================================================================
[GC1 파이프라인 run_processing_gc1]
=============================================================================

  1) ensure_gc1_pdf_exported() — Autochro UI PDF (config.force 시 재내보내기)
  2) parse_gc1_pdf_path() — trim 포함
  3) write_gc1_excel() — FID/TCD 2시트
  4) send_email_via_smtp() — _try_auto_email()
     · force 또는 gc1 → 슬롯 검사 생략
     · GC2 watch → 오전/오후 슬롯 확인
  5) cleanup_superseded_gc1_files() — 잘못된/중복 PDF·xlsx 정리

  GC1_SKIP_AUTOCHRO_EXPORT=1 이면 watch 가 이미 export 한 경우 pipeline 중복 방지.

=============================================================================
[ProcessResult]
=============================================================================

  watch·gc_automation 이 record_processing_result() 에 넘기는 결과 객체.
  latest_acam_mtime — GC1 은 PDF mtime.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional

from gc_chem32 import (
    build_merged_injection_cycles,
    default_sample_name_from_folder,
    find_active_sample_folder,
    get_first_analysis_date,
    get_latest_report_mtime,
    resolve_chemstation_mode,
)
from gc_gc1 import (
    cleanup_superseded_gc1_files,
    find_active_pdf,
    get_latest_pdf_mtime,
    infer_sample_name_from_pdf,
    parse_gc1_pdf_path,
    summarize_assigned_compounds,
    write_gc1_excel,
)
from gc_kch import (
    build_output_filename,
    build_stacked_dataframe,
    determine_sample_name,
    is_new_sequence_date,
    resolve_sample_name,
    write_chem32_excel,
)
from gc_chemstation import (
    drop_first_cycle_if_startup_noise,
    find_injection_folders,
    find_sequence_acam_file,
    find_sequence_folder,
    get_latest_injection_acam_mtime,
    parse_sequence_acam,
)
from gc_config import AppConfig
from gc_mailer import generate_email_body, send_email_via_smtp
from gc_state import can_auto_send_for_mode, gc1_unlimited_auto_send


def _try_auto_email(
    config: AppConfig,
    output_path: str,
    sample_name: str,
    seq_date: str,
    email_body: str,
    script_dir: str,
) -> bool:
    """자동 실행 시 슬롯(오전/오후) 확인 후 메일 발송."""
    if config.force or gc1_unlimited_auto_send(config.chemstation_mode):
        return send_email_via_smtp(
            output_path,
            sample_name,
            seq_date,
            email_body,
            script_dir,
            config.excel_output_dir,
        )
    allowed, reason = can_auto_send_for_mode(config.send_state_file, config.chemstation_mode)
    if not allowed:
        print(f"\n[안내] {reason} — 엑셀만 저장")
        return False
    return send_email_via_smtp(
        output_path,
        sample_name,
        seq_date,
        email_body,
        script_dir,
        config.excel_output_dir,
    )


@dataclass
class ProcessResult:
    """run_processing() 반환값 — 후속 상태 기록에 사용."""

    ok: bool
    email_sent: bool = False
    sequence_folder: Optional[str] = None
    latest_acam_mtime: Optional[float] = None
    action_summary: Optional[str] = None
    fail_reason: Optional[str] = None
    output_path: Optional[str] = None
    email_body: Optional[str] = None
    sample_name: Optional[str] = None
    seq_date: Optional[str] = None


def run_processing(config: AppConfig, script_dir: str) -> ProcessResult:
    """
    ChemStation 시퀀스 1건을 KCH 엑셀로 정리하고 필요 시 메일 발송.

    Args:
        config: AppConfig (data_path, detector, sample_name 등)
        script_dir: gc_automation.py 가 있는 폴더 (.env 탐색용)
    """
    if config.chemstation_mode == "gc1":
        return run_processing_gc1(config, script_dir)

    mode = resolve_chemstation_mode(config.data_path, config.chemstation_mode)
    if mode == "chem32":
        return run_processing_chem32(config, script_dir)

    sequence_folder = find_sequence_folder(
        config.data_path,
        config.sequence_date,
        config.sequence_folder,
    )
    if not sequence_folder:
        return ProcessResult(ok=False, fail_reason="시퀀스 폴더 없음")

    injection_folders = find_injection_folders(sequence_folder)
    if not injection_folders:
        print("[경고] F-... .D 주입 폴더가 없습니다.")
        return ProcessResult(ok=False, sequence_folder=sequence_folder, fail_reason="주입 폴더 없음")

    print(f"[안내] 주입 폴더 {len(injection_folders)}개 (시간순)")

    cycle_peaks_list: List[List[dict]] = []
    injection_labels: List[str] = []
    missing_acam: List[str] = []

    for injection_path in injection_folders:
        injection_name = os.path.basename(injection_path)
        acam_path = find_sequence_acam_file(injection_path)
        if not acam_path:
            print(f"[경고] sequence.acam_ 없음: {injection_name}")
            missing_acam.append(injection_name)
            continue

        peaks = parse_sequence_acam(acam_path, detector=config.detector)
        if peaks:
            cycle_peaks_list.append(peaks)
            injection_labels.append(injection_name)
            print(f"[진행] {injection_name}: 피크 {len(peaks)}개")
        else:
            print(f"[경고] 피크 없음: {injection_name}")

    if not cycle_peaks_list:
        print("\n[안내] 추출된 피크 데이터 없음.")
        return ProcessResult(ok=False, sequence_folder=sequence_folder, fail_reason="피크 없음")

    first_label = injection_labels[0] if injection_labels else None
    cycle_peaks_list, skipped_first, skipped_first_info = drop_first_cycle_if_startup_noise(
        cycle_peaks_list,
        first_injection_label=first_label,
    )

    if not cycle_peaks_list:
        print("\n[안내] 노이즈 제거 후 남은 주입 데이터 없음.")
        return ProcessResult(ok=False, sequence_folder=sequence_folder, fail_reason="노이즈 제거 후 데이터 없음")

    sample_name, seq_date = determine_sample_name(cycle_peaks_list, sequence_folder, config)
    if not sample_name:
        detail = "시료명 미지정 — --sample-name 필요"
        if is_new_sequence_date(config.excel_output_dir, seq_date):
            detail = f"새 날짜({seq_date}) 시퀀스 — 시료명 필수"
        return ProcessResult(
            ok=False,
            sequence_folder=sequence_folder,
            fail_reason=detail,
        )

    output_path = build_output_filename(config.excel_output_dir, sample_name, seq_date)
    latest_mtime = get_latest_injection_acam_mtime(sequence_folder)

    try:
        df = build_stacked_dataframe(cycle_peaks_list)
        df.to_excel(output_path, index=False, sheet_name="Sheet1")
        total_peaks = sum(len(cycle) for cycle in cycle_peaks_list)
        print(f"\n[성공] {output_path}")
        print(f"       주입 {len(cycle_peaks_list)}개 / 피크 {total_peaks}개 / 행 {len(df)}")

        email_sent = False
        email_body = None
        if config.send_email:
            email_body = generate_email_body(
                sample_name,
                seq_date,
                len(cycle_peaks_list),
                total_peaks,
                os.path.basename(output_path),
                len(injection_folders),
                skipped_first_info=skipped_first_info if skipped_first else None,
                missing_acam=missing_acam or None,
            )
            email_sent = _try_auto_email(
                config,
                output_path,
                sample_name,
                seq_date,
                email_body,
                script_dir,
            )
        else:
            print("\n[안내] 이메일 건너뜀 (--no-email)")

        action_bits = ["엑셀 저장"]
        if email_sent:
            action_bits.append("메일 발송")
        action_summary = f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} — {', '.join(action_bits)}"

        return ProcessResult(
            ok=True,
            email_sent=email_sent,
            sequence_folder=sequence_folder,
            latest_acam_mtime=latest_mtime,
            action_summary=action_summary,
            output_path=output_path,
            email_body=email_body,
            sample_name=sample_name,
            seq_date=seq_date,
        )

    except PermissionError:
        print(f"\n[오류] 엑셀 저장 실패 — 파일이 열려 있는지 확인: {output_path}")
        return ProcessResult(ok=False, sequence_folder=sequence_folder, fail_reason="엑셀 PermissionError")
    except Exception as exc:
        print(f"\n[오류] 처리 중 오류: {exc}")
        return ProcessResult(ok=False, sequence_folder=sequence_folder, fail_reason=str(exc))


def run_processing_chem32(config: AppConfig, script_dir: str) -> ProcessResult:
    """GC3 Chem32 — Report.TXT/CSV, FID+TCD 2시트, 시퀀스 중단·재시작 병합."""
    sample_folder = find_active_sample_folder(config.data_path, config.sequence_folder)
    if not sample_folder:
        return ProcessResult(ok=False, fail_reason="Chem32 시료 폴더 없음")

    fid_cycles, tcd_cycles, matched_labels, skipped = build_merged_injection_cycles(sample_folder)
    if not fid_cycles and not tcd_cycles:
        return ProcessResult(
            ok=False,
            sequence_folder=sample_folder,
            fail_reason="Report.TXT/CSV 가 있는 주입 없음",
        )

    analysis_date = get_first_analysis_date(sample_folder)
    default_name = default_sample_name_from_folder(sample_folder)
    sample_name = resolve_sample_name(config, sample_folder, script_dir, default_name)
    if not sample_name:
        return ProcessResult(
            ok=False,
            sequence_folder=sample_folder,
            fail_reason="시료명 없음 — gc_automation.env SAMPLE_NAME= 또는 --sample-name",
        )

    print(f"\n[안내] 분석 날짜(시퀀스 최초 실행): {analysis_date}")
    print(f"[안내] 시료: '{sample_name}'")

    output_path = build_output_filename(config.excel_output_dir, sample_name, analysis_date)
    latest_mtime = get_latest_report_mtime(sample_folder)
    total_peaks = sum(len(c) for c in fid_cycles) + sum(len(c) for c in tcd_cycles)

    try:
        write_chem32_excel(output_path, fid_cycles, tcd_cycles)
        print(f"\n[성공] {output_path}")
        print(
            f"       FID 주입 {len(fid_cycles)} / TCD 주입 {len(tcd_cycles)} / "
            f"피크 {total_peaks}개 / 제외 주입 {skipped}개"
        )

        email_sent = False
        email_body = None
        if config.send_email:
            email_body = generate_email_body(
                sample_name,
                analysis_date,
                len(tcd_cycles) or len(fid_cycles),
                total_peaks,
                os.path.basename(output_path),
                len(matched_labels),
                skipped_first_info=None,
                missing_acam=None,
                chem32=True,
                fid_cycles=len(fid_cycles),
                tcd_cycles=len(tcd_cycles),
            )
            email_sent = _try_auto_email(
                config,
                output_path,
                sample_name,
                analysis_date,
                email_body,
                script_dir,
            )
        else:
            print("\n[안내] 이메일 건너뜀 (--no-email)")

        action_bits = ["Chem32 엑셀(FID+TCD)"]
        if email_sent:
            action_bits.append("메일 발송")
        action_summary = f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} — {', '.join(action_bits)}"

        return ProcessResult(
            ok=True,
            email_sent=email_sent,
            sequence_folder=sample_folder,
            latest_acam_mtime=latest_mtime,
            action_summary=action_summary,
            output_path=output_path,
            email_body=email_body,
            sample_name=sample_name,
            seq_date=analysis_date,
        )

    except PermissionError:
        print(f"\n[오류] 엑셀 저장 실패 — 파일이 열려 있는지 확인: {output_path}")
        return ProcessResult(ok=False, sequence_folder=sample_folder, fail_reason="엑셀 PermissionError")
    except Exception as exc:
        print(f"\n[오류] Chem32 처리 중 오류: {exc}")
        return ProcessResult(ok=False, sequence_folder=sample_folder, fail_reason=str(exc))


def run_processing_gc1(config: AppConfig, script_dir: str) -> ProcessResult:
    """
    GC1 전체 pipeline: (옵션) Autochro export → PDF parse/trim → xlsx → SMTP.

    config.force True: CRM 변경 없어도 Autochro PDF 재생성 (개시 force·수동 --force).
    GC1_SKIP_AUTOCHRO_EXPORT: watch 가 export 직후 pipeline 만 돌릴 때 중복 방지.
    """
    try:
        from gc_autochro import ensure_gc1_pdf_exported, is_autochro_enabled
    except ImportError:
        is_autochro_enabled = lambda: False  # type: ignore
        ensure_gc1_pdf_exported = None  # type: ignore

    if is_autochro_enabled() and ensure_gc1_pdf_exported:
        skip_export = os.getenv("GC1_SKIP_AUTOCHRO_EXPORT", "").strip().lower() in ("1", "true", "yes")
        if skip_export and not config.force:
            print("[Autochro] PDF 내보내기 건너뜀 (watch에서 이미 실행됨)")
        else:
            # config.force → watch/개시 요청 시 Autochro PDF 항상 재내보내기
            export_ok, _, export_msg = ensure_gc1_pdf_exported(
                config.excel_output_dir,
                config.send_state_file,
                force=bool(config.force),
            )
            if not export_ok:
                return ProcessResult(ok=False, fail_reason=f"Autochro PDF 내보내기 실패 — {export_msg}")
            if export_msg and export_msg not in ("CRM 변경 없음", "Autochro 자동화 비활성"):
                print(f"[Autochro] {export_msg}")

    pdf_path = find_active_pdf(config)
    if not pdf_path:
        pdf_dir = config.excel_output_dir
        return ProcessResult(
            ok=False,
            fail_reason=f"PDF 없음 — {pdf_dir} 에 *.pdf 파일을 두세요",
        )

    try:
        report = parse_gc1_pdf_path(pdf_path)
    except ImportError as exc:
        return ProcessResult(ok=False, fail_reason=str(exc))
    except Exception as exc:
        return ProcessResult(ok=False, fail_reason=f"PDF 파싱 실패 — {exc}")

    if not report.fid_cycles and not report.tcd_cycles:
        if report.total_injections == 0:
            fail_reason = "PDF 에서 FID/TCD 피크를 찾지 못함"
        else:
            fail_reason = (
                "사전노이즈·환원·전환·첫 반응 제외 후 남은 데이터 없음 "
                f"(제외: 사전노이즈 {report.skipped_pre_reduction_count}, "
                f"환원 {report.skipped_reduction_count}, "
                f"전환 {report.skipped_transition_count}, "
                f"첫 반응 {report.skipped_first_reaction_count})"
            )
        return ProcessResult(
            ok=False,
            sequence_folder=pdf_path,
            fail_reason=fail_reason,
        )

    default_name = report.default_sample_name or infer_sample_name_from_pdf(pdf_path, report.analysis_date)
    sample_name = resolve_sample_name(config, pdf_path, script_dir, default_name)
    if not sample_name:
        return ProcessResult(
            ok=False,
            sequence_folder=pdf_path,
            fail_reason="시료명 없음 — gc_automation.env SAMPLE_NAME= 또는 --sample-name",
        )

    print(f"\n[안내] GC1 PDF: {os.path.basename(pdf_path)}")
    print(f"[안내] 분석 날짜: {report.analysis_date}")
    print(f"[안내] 시료: '{sample_name}'")
    kept_injections = max(len(report.fid_cycles), len(report.tcd_cycles))
    print(f"[안내] PDF 주입 {report.total_injections}회 → 엑셀 적재 {kept_injections}회")
    if (
        report.skipped_pre_reduction_count
        or report.skipped_reduction_count
        or report.skipped_transition_count
        or report.skipped_first_reaction_count
    ):
        print(
            f"[안내] 제외 - 사전노이즈 {report.skipped_pre_reduction_count}, "
            f"환원 {report.skipped_reduction_count}, "
            f"전환 {report.skipped_transition_count}, "
            f"첫 반응 {report.skipped_first_reaction_count}"
        )
    summarize_assigned_compounds(report)

    output_path = build_output_filename(config.excel_output_dir, sample_name, report.analysis_date)
    latest_mtime = get_latest_pdf_mtime(pdf_path)
    total_peaks = sum(len(c) for c in report.fid_cycles) + sum(len(c) for c in report.tcd_cycles)

    try:
        write_gc1_excel(output_path, report.fid_cycles, report.tcd_cycles)
        print(f"\n[성공] {output_path}")
        print(
            f"       FID / TCD — # Time Area Height 분석된원소 / "
            f"주입 {max(len(report.fid_cycles), len(report.tcd_cycles))}회"
        )

        email_sent = False
        email_body = None
        if config.send_email:
            email_body = generate_email_body(
                sample_name,
                report.analysis_date,
                len(report.tcd_cycles) or len(report.fid_cycles),
                total_peaks,
                os.path.basename(output_path),
                len(report.fid_cycles),
                skipped_first_info=None,
                missing_acam=None,
                chem32=True,
                fid_cycles=len(report.fid_cycles),
                tcd_cycles=len(report.tcd_cycles),
            )
            email_sent = _try_auto_email(
                config,
                output_path,
                sample_name,
                report.analysis_date,
                email_body,
                script_dir,
            )
        else:
            print("\n[안내] 이메일 건너뜀 (--no-email)")

        action_bits = ["GC1 PDF 엑셀(FID+TCD)"]
        if email_sent:
            action_bits.append("메일 발송")
        action_summary = f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} — {', '.join(action_bits)}"

        removed, surviving_pdf = cleanup_superseded_gc1_files(
            config.excel_output_dir,
            pdf_path,
            log_fn=print,
        )
        if removed:
            print(f"[GC1] 잘못된 출력 파일 {removed}개 정리")
        if surviving_pdf != pdf_path:
            print(f"[GC1] 반응 주입 더 많은 PDF 유지: {os.path.basename(surviving_pdf)}")

        return ProcessResult(
            ok=True,
            email_sent=email_sent,
            sequence_folder=pdf_path,
            latest_acam_mtime=latest_mtime,
            action_summary=action_summary,
            output_path=output_path,
            email_body=email_body,
            sample_name=sample_name,
            seq_date=report.analysis_date,
        )

    except PermissionError:
        print(f"\n[오류] 엑셀 저장 실패 — 파일이 열려 있는지 확인: {output_path}")
        return ProcessResult(ok=False, sequence_folder=pdf_path, fail_reason="엑셀 PermissionError")
    except Exception as exc:
        print(f"\n[오류] GC1 처리 중 오류: {exc}")
        return ProcessResult(ok=False, sequence_folder=pdf_path, fail_reason=str(exc))
