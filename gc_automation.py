#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
gc_automation.py — ChemStation / GC1 자동 정리 (CLI 진입점)

=============================================================================
[GitHub · PC — 다른 PC에서 clone 후]
=============================================================================

  Repo: https://github.com/gjtuc/GC-auto
  이 파일은 **장비 PC 전용** (GC1 장비 PC / GC2·GC3 장비 PC).
  은규 PC·차헌 PC에서는 data_pc/촉매 반응 계산.py 를 실행하세요.

  PC 명칭: docs/PC_NAMING.md
    · GC1 장비 PC (은규)  → Desktop\\박은규\\_GC자동화\\gc_automation.env (데이터 xlsx·pdf 는 박은규 루트)
    · GC2/GC3 장비 PC (차헌) → Desktop\\KCH\\gc_automation.env
    · 은규 PC / 차헌 PC → Desktop\\.cursor\\ (본 스크립트 실행 금지)

  clone → 해당 장비 PC의 env 유지 → git pull 로 코드만 갱신
  가이드: docs/CODEBASE_GUIDE.md

=============================================================================
[전체 구조]
=============================================================================

  (A) --watch  … gc_watch.py — Wi-Fi 감시, GC2/GC3는 연결 유지 중 poll
  (B) force    … gc_request.py — 「시작」「go」「진행」 또는 --force/--request

  (A)와 (B)는 **독립**. 상세 아키텍처: gc_architecture.py (문서 전용)

  GC1 장비 PC (은규): gc_autochro → gc_gc1 → gc_mailer, env=Desktop\\박은규
  GC2/GC3 장비 PC (차헌): gc_chemstation / gc_chem32, env=Desktop\\KCH
  메일 수신·계산은 각 연구원의 데이터 PC (은규 PC / 차헌 PC) 에서 처리.

=============================================================================
[GC1 vs GC2 watch 차이 — 요약]
=============================================================================

  GC2/GC3: iptime Wi-Fi, acam/Report poll, 메일 1시간 쿨다운(핫스pot 세션 무관)
  GC1: iPhone, 핫스pot **세션당** PDF·엑셀·메일 1회, 쿨다운·슬롯 없음

=============================================================================
[사용자/Cursor 개시 → force]
=============================================================================

  gc_request.message_is_initiation("진행") → handle_user_message()
    → submit_force_request() → run_processing(force=True)
    → heartbeat MMDDHHmm ±5분 (exit 0/1/2)

=============================================================================
[자주 쓰는 명령]
=============================================================================

  python gc_automation.py --watch
  python gc_automation.py --user-message "진행"
  python gc_automation.py --request          # gc_동작해줘.bat
  python gc_automation.py --force
  python gc_automation.py --show-profile

  GC1 bat: Desktop\\박은규\\GC1_감시시작.bat / GC1_동작해줘.bat
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
from dataclasses import replace

from gc_console import setup_console_encoding

setup_console_encoding()

from gc_instance import acquire_watch_lock

from gc_config import (
    DEFAULT_CHEMSTATION_DATA,
    HEARTBEAT_TOLERANCE_MINUTES,
    REQUIRED_HOTSPOT_SSID,
    AppConfig,
)
from gc_profiles import paths_for_output_dir, print_profile_summary, resolve_data_path, resolve_profile
from gc_sanitize import InvalidSampleNameError, InvalidSequenceFolderError, sanitize_sample_name, validate_sequence_folder
from gc_force_auth import require_force_auth
from gc_mailer import load_dotenv_files
from gc_pipeline import run_processing
from gc_request import (
    config_for_user_request,
    message_is_initiation,
    parse_message_as_request,
)
from gc_state import record_processing_result
from gc_status import (
    print_verify_result,
    show_watch_status,
    verify_desktop_heartbeat,
)
from gc_watch import WatchOptions, run_watch_loop
from gc_wifi import check_runtime_gate

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

# Cursor / --user-message 종료 코드 (다른 PC 스크립트에서도 동일하게 사용)
EXIT_OK = 0              # 개시 문구 → force 완료 + heartbeat ±5분 OK
EXIT_NEED_REPAIR = 1     # force 했지만 heartbeat FAIL → watch 등 수리 필요
EXIT_NOT_INITIATION = 2  # 개시 문구 아님 → 일반 Cursor 작업


def apply_env_overrides(
    config: AppConfig,
    script_dir: str,
    *,
    chemstation_mode_cli: str = "auto",
) -> AppConfig:
    """gc_automation.env — CHEMSTATION_MODE, SAMPLE_NAME 등."""
    load_dotenv_files(script_dir, config.excel_output_dir)
    if chemstation_mode_cli == "auto":
        env_mode = os.getenv("CHEMSTATION_MODE", "").strip().lower()
        if env_mode in ("chem32", "8860", "auto", "gc1"):
            config = replace(config, chemstation_mode=env_mode)
    env_sample = os.getenv("SAMPLE_NAME", "").strip()
    if env_sample and not config.sample_name:
        try:
            config = replace(config, sample_name=sanitize_sample_name(env_sample))
        except InvalidSampleNameError as exc:
            print(f"[오류] SAMPLE_NAME env 무효 — {exc}")
    data_env = os.getenv("CHEMSTATION_DATA_PATH", "").strip() or os.getenv("DATA_PATH", "").strip()
    if data_env:
        config = replace(config, data_path=os.path.normpath(os.path.expanduser(data_env)))
    elif config.chemstation_mode == "chem32" and config.data_path == DEFAULT_CHEMSTATION_DATA:
        from gc_config import DEFAULT_GC3_DATA

        config = replace(config, data_path=DEFAULT_GC3_DATA)
    return config


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "GC 장비 PC 자동화 CLI — GC1: Autochro PDF→KCH xlsx / "
            "GC2: ChemStation acam / GC3: Chem32 Report"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
예시:
  python gc_automation.py --watch
  python gc_automation.py --verify
  python gc_automation.py --user-message "시작"
  python gc_automation.py --request
  python gc_automation.py --sequence-date 20260613 --force
        """,
    )
    parser.add_argument(
        "--user-message",
        metavar="TEXT",
        help=(
            "Cursor용. 맥락 없는 개시 문구면 force 우선 → "
            f"바탕화면 MMDDHHmm.txt ±{HEARTBEAT_TOLERANCE_MINUTES}분 검증. "
            "exit 0/1/2"
        ),
    )
    parser.add_argument(
        "--verify",
        action="store_true",
        help=(
            f"GC 정상 여부를 MMDDHHmm.txt 파일명 시각 ±{HEARTBEAT_TOLERANCE_MINUTES}분만으로 판단. "
            "exit 0=OK, 1=FAIL"
        ),
    )
    parser.add_argument(
        "--request",
        action="store_true",
        help="force 즉시 실행 — watch 독립 (gc_동작해줘.bat)",
    )
    parser.add_argument("--status", action="store_true", help="감시 상태 출력")
    parser.add_argument("--watch", action="store_true", help="핫스팟 감시 (연결 시 새 데이터 처리)")
    parser.add_argument("--watch-interval", type=int, default=15, help="watch 폴링 간격(초, 기본 15)")
    parser.add_argument("--required-ssid", default=None, help="필수 핫스팟 SSID (기본: env/프로필)")
    parser.add_argument("--force", action="store_true", help="수동 — 핫스팟·메일 쿨다운 무시")
    parser.add_argument("--no-wifi-check", action="store_true", help="핫스팟 검사 생략 (테스트)")
    parser.add_argument("--send-state-file", default=None, help="발송 기록 JSON 경로")
    parser.add_argument("--watch-status-json", default=None)
    parser.add_argument("--watch-status-txt", default=None)
    parser.add_argument("--data-path", default=None, help="ChemStation/Chem32 Data 루트 (기본: 프로필·env)")
    parser.add_argument(
        "--chemstation-mode",
        default="auto",
        choices=["auto", "8860", "chem32", "gc1"],
        help="auto=프로필/경로로 판별, gc1=GC1 PDF, chem32=GC3, 8860=GC2",
    )
    parser.add_argument("--sequence-folder", default=None)
    parser.add_argument("--sequence-date", default=None)
    parser.add_argument("--sample-name", default=None)
    parser.add_argument("--detector", default="TCD", choices=["TCD", "FID"])
    parser.add_argument("--no-email", action="store_true")
    parser.add_argument(
        "--show-profile",
        action="store_true",
        help="GC1/GC2/GC3 프로필(출력 폴더·핫스팟·env) 확인",
    )
    parser.add_argument(
        "--force-token",
        default=None,
        help="GC_FORCE_TOKEN 설정 시 force/--request 필수 (또는 GC_FORCE_INVOKE env)",
    )
    parser.add_argument(
        "--error-poll",
        action="store_true",
        help="watch error/stale heartbeat 감지 → 로그·재시작·Cursor SDK",
    )
    parser.add_argument(
        "--error-recover",
        action="store_true",
        help="pending 오류 1건 복구 (gc_error_handler)",
    )
    return parser


def config_from_args(args: argparse.Namespace, script_dir: str) -> AppConfig:
    profile = resolve_profile(script_dir)
    runtime_paths = paths_for_output_dir(profile.excel_output_dir)
    sample_name = args.sample_name
    if sample_name:
        try:
            sample_name = sanitize_sample_name(sample_name)
        except InvalidSampleNameError as exc:
            print(f"[오류] --sample-name 무효 — {exc}")
            raise SystemExit(2) from exc
    sequence_folder = args.sequence_folder
    if sequence_folder:
        try:
            sequence_folder = validate_sequence_folder(sequence_folder, args.data_path)
        except InvalidSequenceFolderError as exc:
            print(f"[오류] --sequence-folder 무효 — {exc}")
            raise SystemExit(2) from exc
    return AppConfig(
        data_path=args.data_path or resolve_data_path(),
        chemstation_mode=args.chemstation_mode
        if args.chemstation_mode != "auto"
        else profile.chemstation_mode,
        excel_output_dir=profile.excel_output_dir,
        send_email=not args.no_email,
        sample_name=sample_name,
        sequence_date=args.sequence_date,
        sequence_folder=sequence_folder,
        detector=args.detector,
        required_ssid=args.required_ssid or profile.required_ssid,
        skip_wifi_check=args.no_wifi_check,
        force=args.force,
        allow_prompt=not args.watch,
        send_state_file=args.send_state_file or runtime_paths["send_state"],
    )


def force_config_from(base: AppConfig) -> AppConfig:
    """사용자 force 전용 설정 — 핫스팟·메일 쿨다운·input() 모두 우회."""
    return AppConfig(
        data_path=base.data_path,
        chemstation_mode=base.chemstation_mode,
        excel_output_dir=base.excel_output_dir,
        send_email=base.send_email,
        sample_name=base.sample_name,
        sequence_date=base.sequence_date,
        sequence_folder=base.sequence_folder,
        detector=base.detector,
        required_ssid=base.required_ssid,
        skip_wifi_check=base.skip_wifi_check,
        force=True,
        allow_prompt=False,
        send_state_file=base.send_state_file,
    )


def after_successful_run(config: AppConfig, result, count_email_toward_limit: bool) -> None:
    if not result.ok or not result.sequence_folder or result.latest_acam_mtime is None:
        return
    record_processing_result(
        config.send_state_file,
        sequence_folder=result.sequence_folder,
        latest_mtime=result.latest_acam_mtime,
        action_summary=result.action_summary or "",
        email_sent=result.email_sent,
        send_email=config.send_email,
        count_email_toward_limit=count_email_toward_limit,
        output_path=result.output_path,
        email_body=result.email_body,
        sample_name=result.sample_name,
        seq_date=result.seq_date,
        chemstation_mode=config.chemstation_mode,
    )


def run_force_once(config: AppConfig, script_dir: str) -> None:
    """pipeline 1회 — force 규칙(핫스팟·한도 무시). 메일은 daily_send_count에 안 넣음."""
    from gc1_runtime.layer3_run_closure import format_end_user_summary

    print("[안내] force 우선 실행 — 핫스팟·메일 쿨다운 규칙 적용 안 함")
    result = run_processing(config, script_dir)
    after_successful_run(config, result, count_email_toward_limit=False)
    out_base = os.path.basename(result.output_path) if result.output_path else ""
    print()
    print(
        format_end_user_summary(
            ok=result.ok,
            email_sent=bool(result.email_sent),
            output_basename=out_base,
            fail_reason=result.fail_reason or "",
        )
    )


def submit_force_request(config: AppConfig, script_dir: str, trigger_text: str) -> None:
    """[1단계] force — watch 와 무관하게 이 프로세스에서 즉시 pipeline 실행."""
    print(f"[1/2] force 실행 — '{trigger_text}' (watch 독립, 핫스팟·메일 쿨다운 무시)")
    if not os.path.isdir(config.data_path) and config.chemstation_mode != "gc1":
        print(f"[오류] Data 경로 없음: {config.data_path}")
        return
    os.makedirs(config.excel_output_dir, exist_ok=True)
    force_cfg = config if config.force else force_config_from(config)
    run_force_once(force_cfg, script_dir)


def verify_system_health() -> int:
    """
    [2단계] GC 전체 OK 여부 — **오직** 바탕화면 MMDDHHmm.txt ±5분.

    --watch가 돌면 gc_status.py 가 1분마다 06151513.txt 처럼
    파일 이름을 현재 시각으로 바꿉니다. 이름이 5분 이상 밀리면 watch 멈춤으로 봅니다.
    """
    check = verify_desktop_heartbeat(HEARTBEAT_TOLERANCE_MINUTES)
    print_verify_result(check)
    return EXIT_OK if check.ok else EXIT_NEED_REPAIR


def handle_user_message(text: str, config: AppConfig) -> int:
    """
    Cursor가 호출하는 진입점.

    순서가 중요합니다:
      1) 개시 문구인지 판별 (gc_request.message_is_initiation)
      2) force 우선 (submit_force_request)
      3) heartbeat ±5분만 검증 — OK면 Cursor 추가 작업 금지
    """
    if not message_is_initiation(text):
        print("[안내] 개시 문구 아님 — Cursor가 일반 작업 진행")
        return EXIT_NOT_INITIATION

    request = parse_message_as_request(text)
    trigger = request.trigger_line if request else text.strip()
    print(f"[개시] '{trigger}' → force (watch 독립)")

    force_config = config_for_user_request(config, request) if request else force_config_from(config)
    submit_force_request(force_config, SCRIPT_DIR, trigger)

    print(f"[2/2] 바탕화면 MMDDHHmm.txt ±{HEARTBEAT_TOLERANCE_MINUTES}분 검증")
    deadline = time.time() + 90
    check = verify_desktop_heartbeat(HEARTBEAT_TOLERANCE_MINUTES)
    while not check.ok and time.time() < deadline:
        time.sleep(10)
        check = verify_desktop_heartbeat(HEARTBEAT_TOLERANCE_MINUTES)

    print_verify_result(check)
    if check.ok:
        print("[완료] GC 자동화 정상 — 추가 수리 불필요")
        return EXIT_OK

    print("[필요] heartbeat 비정상 — Cursor가 watch 재시작 등 force 외 작업 진행")
    return EXIT_NEED_REPAIR


def main() -> None:
    args = build_parser().parse_args()

    from gc_profiles import bootstrap_env, gc_runtime_dir, migrate_gc1_runtime_layout, resolve_gc_instance

    data_root, _ = bootstrap_env(SCRIPT_DIR)
    if resolve_gc_instance() == "gc1":
        moved = migrate_gc1_runtime_layout(data_root)
        if moved:
            bootstrap_env(SCRIPT_DIR)
            print(f"[안내] GC1 자동화 파일 {moved}개 → {gc_runtime_dir(data_root)} 로 정리됨")

    if args.show_profile:
        print_profile_summary(resolve_profile(SCRIPT_DIR))
        return

    config = apply_env_overrides(
        config_from_args(args, SCRIPT_DIR),
        SCRIPT_DIR,
        chemstation_mode_cli=args.chemstation_mode,
    )
    runtime_paths = paths_for_output_dir(config.excel_output_dir)
    status_json = args.watch_status_json or runtime_paths["watch_status_json"]
    status_txt = args.watch_status_txt or runtime_paths["watch_status_txt"]

    if args.verify:
        sys.exit(verify_system_health())

    if args.user_message:
        require_force_auth(args.force_token)
        sys.exit(handle_user_message(args.user_message, config))

    if args.status:
        show_watch_status(status_json, status_txt)
        return

    if args.error_poll:
        from gc_error_handler import poll_and_recover

        results = poll_and_recover(config.excel_output_dir, SCRIPT_DIR, status_json)
        print(json.dumps(results, ensure_ascii=False, indent=2))
        return

    if args.error_recover:
        from gc_error_handler import recover_pending_once

        result = recover_pending_once(config.excel_output_dir, SCRIPT_DIR)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return

    if args.request:
        require_force_auth(args.force_token)
        trigger = "시작"
        submit_force_request(force_config_from(config), SCRIPT_DIR, trigger)
        sys.exit(verify_system_health())

    if not os.path.isdir(config.data_path) and config.chemstation_mode != "gc1":
        print(f"[오류] Data 경로 없음: {config.data_path}")
        return

    os.makedirs(config.excel_output_dir, exist_ok=True)

    if args.watch:
        if not acquire_watch_lock(config.excel_output_dir):
            print("[안내] GC 감시가 이미 실행 중입니다 — 추가 창은 닫아도 됩니다.")
            time.sleep(4)
            return
        watch_opts = WatchOptions(
            watch_interval=args.watch_interval,
            status_json_path=status_json,
            status_txt_path=status_txt,
            send_state_file=config.send_state_file,
        )
        run_watch_loop(config, watch_opts, SCRIPT_DIR)
        return

    allowed, reason = check_runtime_gate(
        config.required_ssid,
        config.send_email,
        config.send_state_file,
        skip_wifi_check=config.skip_wifi_check,
        force=config.force,
    )
    if not allowed:
        print(f"[중단] {reason}")
        return

    if config.force:
        require_force_auth(args.force_token)
        print("[안내] 수동(--force) — 핫스팟·메일 쿨다운 규칙 적용 안 함")

    result = run_processing(config, SCRIPT_DIR)
    after_successful_run(config, result, count_email_toward_limit=not config.force)


if __name__ == "__main__":
    main()
