# -*- coding: utf-8 -*-
"""
gc_chem32_validate.py — GC3 Chem32 실데이터 로컬 검증 (GC8860 / Cursor)

GC3 PC에서 cmd가 바로 닫혀도 Desktop\\KCH\\gc3_validate_log.txt 에 전체 로그 저장.

사용:
  python gc_chem32_validate.py --data-path testdata\\gc3_real
  python gc_chem32_validate.py --data-path C:\\Chem32\\1\\Data --sample-folder "20260620 DRME..."
  python gc_chem32_validate.py --data-path ... --run-pipeline --no-email
"""

from __future__ import annotations

import argparse
import os
import sys
import traceback
from contextlib import redirect_stdout
from datetime import datetime
from io import StringIO

from gc_console import setup_console_encoding

setup_console_encoding()

from gc_chem32 import (
    build_merged_injection_cycles,
    collect_reported_injections,
    cycles_match,
    default_sample_name_from_folder,
    find_active_sample_folder,
    find_chem32_injection_folders,
    find_report_txt,
    find_sample_folders,
    find_sequence_folders,
    parse_injection_reports,
)
from gc_config import DEFAULT_GC3_DATA, EXCEL_OUTPUT_DIR
from gc_profiles import resolve_data_path


class _Tee:
    def __init__(self, *streams):
        self._streams = streams

    def write(self, data):
        for stream in self._streams:
            stream.write(data)

    def flush(self):
        for stream in self._streams:
            stream.flush()


def _log_path() -> str:
    out = os.path.join(os.path.expanduser("~"), "Desktop", "KCH")
    os.makedirs(out, exist_ok=True)
    return os.path.join(out, "gc3_validate_log.txt")


def _print_sample_tree(sample_folder: str) -> None:
    print(f"\n=== 시료 폴더 ===\n{sample_folder}\n")
    sequences = find_sequence_folders(sample_folder)
    print(f"REACTION 시퀀스 {len(sequences)}개:")
    for seq in sequences:
        print(f"  - {os.path.basename(seq)}")
        for inj in find_chem32_injection_folders(seq):
            label = os.path.basename(inj)
            report = find_report_txt(inj)
            reports = parse_injection_reports(inj)
            fid_n = len(reports.get("FID", []))
            tcd_n = len(reports.get("TCD", []))
            rep = os.path.basename(report) if report else "(없음)"
            print(f"      {label}  Report={rep}  FID={fid_n}  TCD={tcd_n}")


def _print_mismatch_detail(sample_folder: str) -> None:
    injections = collect_reported_injections(sample_folder)
    if not injections:
        print("\n[경고] Report 있는 주입 없음")
        return
    print(f"\n=== 주입 {len(injections)}개 (시간순) — TCD 패턴 비교 ===")
    reference = None
    ref_label = None
    for injection_path, seq_path in injections:
        label = os.path.basename(injection_path)
        seq_name = os.path.basename(seq_path)
        reports = parse_injection_reports(injection_path)
        for det in ("TCD", "FID"):
            peaks = reports.get(det, [])
            if not peaks:
                continue
            if reference is None and det == "TCD":
                reference = peaks
                ref_label = label
                print(f"[기준] {label} ({seq_name}) TCD {len(peaks)}피크")
                continue
            if det == "TCD" and reference:
                ok = cycles_match(reference, peaks)
                mark = "OK" if ok else "불일치"
                print(f"  [{mark}] {label} ({seq_name}) TCD {len(peaks)}피크 vs 기준 {ref_label} {len(reference)}피크")


def run_validate(args: argparse.Namespace) -> int:
    data_path = os.path.normpath(args.data_path or resolve_data_path() or DEFAULT_GC3_DATA)
    print(f"[Data] {data_path}")
    if not os.path.isdir(data_path):
        print(f"[오류] Data 경로 없음: {data_path}")
        return 1

    samples = find_sample_folders(data_path)
    print(f"[안내] 시료 후보 {len(samples)}개 (mtime 최신순):")
    for index, path in enumerate(samples[:10]):
        print(f"  {index + 1}. {os.path.basename(path)}  mtime={datetime.fromtimestamp(os.path.getmtime(path))}")

    sample_folder = None
    if args.sample_folder:
        candidate = args.sample_folder
        if not os.path.isabs(candidate):
            candidate = os.path.join(data_path, candidate)
        sample_folder = os.path.normpath(candidate)
        if not os.path.isdir(sample_folder):
            print(f"[오류] 시료 폴더 없음: {sample_folder}")
            return 1
    else:
        sample_folder = find_active_sample_folder(data_path)

    if not sample_folder:
        print("[오류] 시료 폴더를 찾지 못함")
        return 1

    _print_sample_tree(sample_folder)
    _print_mismatch_detail(sample_folder)

    print("\n=== 병합 결과 (pipeline 과 동일) ===")
    fid_cycles, tcd_cycles, matched, skipped = build_merged_injection_cycles(sample_folder)
    default_name = default_sample_name_from_folder(sample_folder)
    print(f"시료명(자동): {default_name!r}")
    print(f"FID 사이클 {len(fid_cycles)} / TCD 사이클 {len(tcd_cycles)} / 매칭 주입 {len(matched)} / 건너뜀 {skipped}")

    if skipped >= 5:
        print(
            "\n[힌트] 불일치가 많으면 보통:\n"
            "  · 시료 폴더 안에 예전 REACTION 시퀀스가 여러 개 쌓여 있음\n"
            "  · 첫 주입만 기준으로 잡고 나머지를 '다른 실험'으로 제외함\n"
            "  · 최신 시퀀스만 쓰도록 코드 수정이 필요할 수 있음 — 이 로그를 Cursor에 공유"
        )

    if args.run_pipeline:
        print("\n=== pipeline 실행 (--no-email) ===")
        from gc_automation import config_from_args, apply_env_overrides
        from gc_pipeline import run_processing
        from gc_config import AppConfig
        from dataclasses import replace

        script_dir = os.path.dirname(os.path.abspath(__file__))
        ns = argparse.Namespace(
            data_path=data_path,
            chemstation_mode="chem32",
            sample_name=args.sample_name,
            sequence_folder=sample_folder,
            sequence_date=None,
            detector="TCD",
            no_email=True,
            no_wifi_check=True,
            force=True,
            required_ssid=None,
            send_state_file=None,
            watch_status_json=None,
            watch_status_txt=None,
        )
        config = apply_env_overrides(
            config_from_args(ns, script_dir),
            script_dir,
            chemstation_mode_cli="chem32",
        )
        config = replace(config, sequence_folder=sample_folder)
        result = run_processing(config, script_dir)
        print(f"\n결과: ok={result.ok}  reason={result.fail_reason or '-'}")
        if result.output_path:
            print(f"엑셀: {result.output_path}")
        return 0 if result.ok else 1

    if not fid_cycles and not tcd_cycles:
        return 1
    return 0


def main() -> None:
    parser = argparse.ArgumentParser(description="GC3 Chem32 실데이터 검증")
    parser.add_argument("--data-path", default=None, help=f"기본: {DEFAULT_GC3_DATA}")
    parser.add_argument("--sample-folder", default=None, help="시료 폴더 이름 또는 전체 경로")
    parser.add_argument("--sample-name", default=None, help="pipeline 테스트 시 시료명")
    parser.add_argument("--run-pipeline", action="store_true", help="엑셀까지 생성 (--no-email)")
    args = parser.parse_args()

    log_file = _log_path()
    buffer = StringIO()
    code = 1
    try:
        with open(log_file, "w", encoding="utf-8") as log_fp:
            tee = _Tee(sys.stdout, buffer, log_fp)
            old_stdout = sys.stdout
            sys.stdout = tee
            try:
                print(f"=== gc_chem32_validate {datetime.now().isoformat(timespec='seconds')} ===")
                code = run_validate(args)
            finally:
                sys.stdout = old_stdout
        print(f"\n[저장] 전체 로그: {log_file}")
    except Exception:
        with open(log_file, "a", encoding="utf-8") as log_fp:
            log_fp.write("\n[예외]\n")
            log_fp.write(traceback.format_exc())
        print(traceback.format_exc())
        print(f"\n[저장] {log_file}")
        code = 1
    sys.exit(code)


if __name__ == "__main__":
    main()
