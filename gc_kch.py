# -*- coding: utf-8 -*-
"""
gc_kch.py — KCH 엑셀 생성 및 시료 이름 결정

[시료 이름 규칙 — GC2 8860]
  1) --sample-name 지정 → 최우선 (사용자 지정)
  2) 대화형(allow_prompt) → Data 폴더 정규화명을 기본값으로 보여 주고 확인/수정
     예: 20260724DRE(1.5)600CNi… → 20260724 DRE(1.5%)@600C Ni…
  3) ``… sequence YYYY-MM-DD …`` 자동 폴더명 → 기본값 없음, 반드시 직접 입력
  4) watch/force 무입력 → 기본 제안만 안내 후 대기 (자동 전송 안 함)

  엑셀 파일명 = 시료명만 (``시료명.xlsx``), 같은 이름이면 덮어쓰기.
"""

from __future__ import annotations

import glob
import os
from typing import List, Optional, Tuple

import pandas as pd

from gc_config import (
    CHEM32_COLUMNS,
    CHEM32_FID_SHEET,
    CHEM32_HEADER_ROW,
    CHEM32_TCD_SHEET,
    CHEMSTATION_COLUMNS,
    COMPARE_CYCLES,
    HEADER_ROW,
    RT_TOLERANCE,
    AppConfig,
)
from gc_mailer import load_dotenv_files
from gc_chemstation import get_sequence_date, rt_patterns_match
from gc_sanitize import InvalidSampleNameError, build_safe_output_filename, sanitize_sample_name


def is_new_sequence_date(
    excel_output_dir: str,
    seq_date: str,
    state_path: Optional[str] = None,
) -> bool:
    """
    해당 날짜 KCH 엑셀이 아직 없으면 True.

    실무상 「새 날짜」= 시료가 바뀐 새 시퀀스 → watch 가 시료명 1회 입력을 요청.
    같은 날짜·같은 RT 패턴의 추가 주입은 기존 엑셀·시료명으로 자동 처리.
    """
    return len(list_excel_files_for_date(excel_output_dir, seq_date, state_path=state_path)) == 0


def format_watch_sample_name_required_message(
    seq_date: str,
    *,
    reason: str = "new_date",
    new_injection_detected: bool = False,
    suggested_name: str = "",
) -> str:
    """
    watch·바탕화면 heartbeat — 시료명은 사용자 확인 후 지정.
    suggested_name 이 있으면 폴더 정규화 기본값을 안내한다.
    """
    if new_injection_detected:
        lead = "새 주입 감지됨 — 시료명을 확인해 주세요."
    else:
        lead = "시료명 확인 대기 중"
    if reason == "rt_mismatch":
        head = f"날짜 {seq_date} — KCH 기존 엑셀과 RT(peak) 패턴 불일치"
    elif reason == "confirm_folder":
        head = f"날짜 {seq_date} — Data 시료 폴더 기본명 확인 필요"
    elif reason == "auto_sequence":
        head = f"날짜 {seq_date} — 자동 시퀀스 폴더(이름 미지정) → 시료명 필수"
    else:
        head = f"새 날짜({seq_date}) 시퀀스"
    suggest_line = ""
    if suggested_name:
        suggest_line = f"\n  기본 제안: {suggested_name}"
    return (
        f"{lead}\n"
        f"  {head} (진행 시마다 시료명 확인 · 자동 전송 전 사용자 확인){suggest_line}\n"
        f"  Cursor 또는: gc_동작해줘.bat --sample-name \"{suggested_name or '<직접입력>'}\" "
        f"--sequence-date {seq_date}"
    )


def check_sample_name_before_processing(sequence_folder: str, config: AppConfig) -> Optional[str]:
    """
    acam 파싱 전 빠른 검사 — GC2 watch 시료명 확인.

    통과 (None):
      · config.sample_name 지정
      · allow_prompt (대화형)
      · 폴더 정규화명과 같은 KCH 엑셀이 이미 있음 (같은 실험 덮어쓰기 계속)

    그 외 → 시료명 확인 메시지 (suggested_name 포함)
    """
    from gc_chemstation import get_sample_seq_date, suggest_sample_name_from_folder

    if config.sample_name:
        return None
    if config.allow_prompt:
        return None

    seq_date = get_sample_seq_date(sequence_folder, config.sequence_date)
    suggested = suggest_sample_name_from_folder(sequence_folder)
    if suggested:
        try:
            existing = build_output_filename(config.excel_output_dir, suggested, seq_date)
        except InvalidSampleNameError:
            existing = ""
        if existing and os.path.isfile(existing):
            return None
        return format_watch_sample_name_required_message(
            seq_date,
            reason="confirm_folder",
            suggested_name=suggested,
        )

    return format_watch_sample_name_required_message(
        seq_date,
        reason="auto_sequence",
        suggested_name="",
    )


def resolve_active_sequence_folder(config: AppConfig) -> Optional[str]:
    """GC2/GC3 watch 가 보는 활성 시퀀스·시료 폴더."""
    from gc_chem32 import find_active_sample_folder, resolve_chemstation_mode
    from gc_chemstation import find_active_sample_folder_8860

    if not os.path.isdir(config.data_path):
        return None
    mode = resolve_chemstation_mode(config.data_path, config.chemstation_mode)
    if mode == "chem32":
        return find_active_sample_folder(config.data_path, config.sequence_folder)
    # GC2: 최신 F- 주입이 들어 있는 **시료** 폴더 (시퀀스 내부가 아님)
    return find_active_sample_folder_8860(config.data_path, config.sequence_folder)


def resolve_watch_sample_name_alert(
    config: AppConfig,
    state_path: str,
) -> Optional[dict]:
    """
    watch UI — 시료명 입력이 필요하면 메시지·폴더 반환.

    Wi-Fi 유지 중 idle tick 에서도 need_sample_name 이 wifi_ok 로 덮이지 않게 유지.
    KCH 에 해당 날짜 엑셀이 생기거나 force 로 시료명 지정되면 clear.

    판정:
      · 새 시료(날짜 엑셀 없음) 또는 state 의 watch_need_sample_name 잔존
      · new_injection_detected = has_new_data_since_last_run (안내 문구용)
    """
    from gc_chem32 import resolve_chemstation_mode
    from gc_state import (
        clear_watch_need_sample_name,
        get_watch_need_sample_name,
        has_new_data_since_last_run,
        load_send_state,
        set_watch_need_sample_name,
    )

    sequence_folder = resolve_active_sequence_folder(config)
    if not sequence_folder:
        return None

    seq_date = get_sequence_date(sequence_folder, config.sequence_date)
    has_new = has_new_data_since_last_run(
        state_path,
        sequence_folder,
        config.data_path,
        config.chemstation_mode,
    )

    if config.sample_name:
        clear_watch_need_sample_name(state_path)
        return None

    from gc_state import get_seq_sample_name

    if get_seq_sample_name(state_path, seq_date):
        clear_watch_need_sample_name(state_path)
        return None

    state = load_send_state(state_path)
    pending = get_watch_need_sample_name(state)
    new_date = is_new_sequence_date(
        config.excel_output_dir, seq_date, state_path=state_path
    )

    if not new_date and not pending:
        return None

    if not new_date and pending and pending.get("reason") == "new_date":
        clear_watch_need_sample_name(state_path)
        return None

    if new_date:
        reason = "new_date"
    else:
        reason = str(pending.get("reason") if pending else "rt_mismatch")

    message = format_watch_sample_name_required_message(
        seq_date,
        reason=reason,
        new_injection_detected=has_new,
    )
    set_watch_need_sample_name(
        state_path,
        seq_date=seq_date,
        sequence_folder=sequence_folder,
        message=message,
        reason=reason,
    )
    return {
        "message": message,
        "sequence_folder": sequence_folder,
        "seq_date": seq_date,
        "reason": reason,
        "new_injection_detected": has_new,
    }


def list_excel_files_for_date(
    excel_output_dir: str,
    seq_date: str,
    state_path: Optional[str] = None,
) -> List[str]:
    """해당 시퀀스 날짜에 연결된 KCH 엑셀 목록 (최신순).

    · 레거시: ``{YYYYMMDD} *.xlsx``
    · 현재: send_state 의 시료명 → ``{시료명}.xlsx``
    """
    found: List[str] = []
    pattern = os.path.join(excel_output_dir, f"{seq_date} *.xlsx")
    found.extend(
        path for path in glob.glob(pattern) if not os.path.basename(path).startswith("~$")
    )
    if state_path:
        from gc_state import get_seq_sample_name

        persisted = get_seq_sample_name(state_path, seq_date)
        if persisted:
            try:
                safe = sanitize_sample_name(persisted)
            except InvalidSampleNameError:
                safe = ""
            if safe:
                candidate = os.path.join(excel_output_dir, f"{safe}.xlsx")
                if os.path.isfile(candidate) and candidate not in found:
                    found.append(candidate)
    return sorted(found, key=os.path.getmtime, reverse=True)


def parse_sample_name_from_excel(excel_path: str, seq_date: str = "") -> Optional[str]:
    """엑셀 stem → 시료명. 레거시 ``YYYYMMDD 시료`` 또는 시료명만."""
    filename = os.path.basename(excel_path)
    if filename.lower().endswith(".xlsx"):
        filename = filename[:-5]
    if not filename or filename.startswith("~$"):
        return None
    if seq_date:
        prefix = f"{seq_date} "
        if filename.startswith(prefix):
            return filename[len(prefix) :]
    parts = filename.split(" ", 1)
    if len(parts) == 2 and len(parts[0]) == 8 and parts[0].isdigit():
        return parts[1]
    return filename


def extract_cycles_from_dataframe(df: pd.DataFrame) -> List[List[dict]]:
    """KCH 엑셀을 사이클(주입) 단위 dict 리스트로 분리 (# 헤더 행 기준)."""
    cycles = []
    current = []
    for _, row in df.iterrows():
        peak_num = str(row["#"]).strip()
        if peak_num == "#":
            if current:
                cycles.append(current)
                current = []
            continue
        try:
            int(peak_num)
        except ValueError:
            continue
        current.append(row.to_dict())
    if current:
        cycles.append(current)
    return cycles


def cycle_fingerprint(cycle_peaks_list: List[List[dict]], compare_cycles: int = COMPARE_CYCLES) -> tuple:
    """앞쪽 N주입의 RT 튜플 — 시료 동일성 비교용."""
    fingerprint = []
    for peaks in cycle_peaks_list[:compare_cycles]:
        fingerprint.append(tuple(round(float(p["Time"]), 3) for p in peaks))
    return tuple(fingerprint)


def excel_fingerprint(excel_path: str, compare_cycles: int = COMPARE_CYCLES) -> tuple:
    df = pd.read_excel(excel_path, sheet_name="Sheet1")
    cycles = extract_cycles_from_dataframe(df)
    converted = [[{"Time": row["Time"]} for row in cycle] for cycle in cycles]
    return cycle_fingerprint(converted, compare_cycles)


def fingerprints_match(fp_a: tuple, fp_b: tuple, rt_tolerance: float = RT_TOLERANCE) -> bool:
    if not fp_a or not fp_b or len(fp_a) != len(fp_b):
        return False
    for cycle_a, cycle_b in zip(fp_a, fp_b):
        if not rt_patterns_match(cycle_a, cycle_b, rt_tolerance):
            return False
    return True


def fingerprints_prefix_match(fp_a: tuple, fp_b: tuple, rt_tolerance: float = RT_TOLERANCE) -> bool:
    """
    주입 추가 중 — 기존 엑셀 사이클 수 < 현재 acam 사이클 수일 때 앞쪽만 비교.

    force 1회(1주입) 후 watch 가 2·3주입을 붙일 때 len 불일치로 rt_mismatch 나던 문제 방지.
    """
    if not fp_a or not fp_b:
        return False
    n = min(len(fp_a), len(fp_b))
    if n == 0:
        return False
    return fingerprints_match(fp_a[:n], fp_b[:n], rt_tolerance)


def find_matching_sample_name(
    cycle_peaks_list: List[List[dict]],
    seq_date: str,
    excel_output_dir: str,
    state_path: Optional[str] = None,
) -> Optional[str]:
    """KCH 기존 파일 RT 지문과 일치하는 시료명."""
    current_fp = cycle_fingerprint(cycle_peaks_list)
    for excel_path in list_excel_files_for_date(
        excel_output_dir, seq_date, state_path=state_path
    ):
        sample_name = parse_sample_name_from_excel(excel_path, seq_date)
        if not sample_name:
            continue
        try:
            existing_fp = excel_fingerprint(excel_path)
        except Exception as exc:
            print(f"[경고] 기존 엑셀 비교 실패 ({os.path.basename(excel_path)}): {exc}")
            continue
        if fingerprints_match(current_fp, existing_fp) or fingerprints_prefix_match(
            current_fp, existing_fp
        ):
            matched_cycles = min(len(current_fp), len(existing_fp))
            print(f"\n[안내] 앞 {matched_cycles}개 주입 RT가 기존 파일과 일치 → 동일 시료")
            print(f"       시료: '{sample_name}' / 파일: {os.path.basename(excel_path)}")
            return sample_name
    return None


def prompt_sample_name(
    seq_date: str,
    has_existing_files: bool,
    default_name: str = "",
) -> str:
    """대화형 터미널에서 시료명 입력. default_name 있으면 Enter 로 수락."""
    if has_existing_files and not default_name:
        print(f"\n[주의] KCH 기존 엑셀과 앞 {COMPARE_CYCLES}주입 RT 패턴 불일치 → 다른 시료")
    elif default_name:
        print(f"\n[안내] 날짜 {seq_date} — Data 폴더 기본 시료명 확인")
        print(f"       기본값: {default_name}")
        print("       Enter = 이 이름 사용 / 다른 이름 입력 = 수정 (사용자 지정 우선)")
    else:
        print(f"\n[안내] 날짜 {seq_date} — 자동 시퀀스 폴더(시료명 미지정) → 직접 입력 필요")
        print("       예: 20260724 DRE(1.5%)@600C Ni5-Al2O3")
    print("       (--sample-name 으로도 지정 가능)")
    while True:
        prompt = "=> 시료 이름"
        if default_name:
            prompt += f" [{default_name}]"
        prompt += ": "
        new_name = input(prompt).strip()
        if not new_name:
            if default_name:
                new_name = default_name
            else:
                print("[오류] 시료 이름은 비워둘 수 없습니다.")
                continue
        try:
            return sanitize_sample_name(new_name)
        except InvalidSampleNameError as exc:
            print(f"[오류] {exc}")


def determine_sample_name_8860(
    sample_folder: str,
    config: AppConfig,
) -> Tuple[Optional[str], str]:
    """
    GC2 시료 폴더 기준 이름 결정.

    · CLI ``--sample-name`` 최우선
    · 그 외 진행마다 확인: 새 스타일 폴더는 정규화명을 기본값으로 제안
    · ``… sequence …`` 자동명은 기본값 없음 (필수 입력)
    """
    from gc_chemstation import get_sample_seq_date, suggest_sample_name_from_folder

    seq_date = get_sample_seq_date(sample_folder, config.sequence_date)
    suggested = suggest_sample_name_from_folder(sample_folder)

    if config.sample_name:
        try:
            safe_name = sanitize_sample_name(config.sample_name)
        except InvalidSampleNameError as exc:
            print(f"\n[오류] {exc}")
            return None, seq_date
        print(f"\n[안내] 사용자 지정 시료명 '{safe_name}' 사용")
        return safe_name, seq_date

    if config.allow_prompt:
        return (
            prompt_sample_name(seq_date, has_existing_files=False, default_name=suggested or ""),
            seq_date,
        )

    reason = "confirm_folder" if suggested else "auto_sequence"
    print(
        f"\n[오류] 시료명 확인 필요 — "
        f"{'기본 제안: ' + suggested if suggested else '폴더가 자동 시퀀스명이라 직접 지정 필요'}"
    )
    print(
        f'       예: python gc_automation.py --sample-name '
        f'"{suggested or "YYYYMMDD DRE(x.x%)@xxxC 시료"}" --force'
    )
    detail = format_watch_sample_name_required_message(
        seq_date,
        reason=reason,
        suggested_name=suggested or "",
    )
    print(detail)
    return None, seq_date


def determine_sample_name(
    cycle_peaks_list: List[List[dict]],
    sequence_folder_path: str,
    config: AppConfig,
) -> Tuple[Optional[str], str]:
    """
    시료명과 시퀀스 날짜 결정. 엑셀 파일명은 시료명만 사용 (날짜 접두 없음).

    Returns:
        (sample_name, seq_date) — sample_name 이 None 이면 처리 불가
    """
    seq_date = get_sequence_date(sequence_folder_path, config.sequence_date)
    state_path = config.send_state_file
    existing_files = list_excel_files_for_date(
        config.excel_output_dir, seq_date, state_path=state_path
    )

    matched = find_matching_sample_name(
        cycle_peaks_list,
        seq_date,
        config.excel_output_dir,
        state_path=state_path,
    )
    if matched:
        return matched, seq_date

    if config.sample_name:
        try:
            safe_name = sanitize_sample_name(config.sample_name)
        except InvalidSampleNameError as exc:
            print(f"\n[오류] {exc}")
            return None, seq_date
        if existing_files:
            print(f"\n[안내] 패턴 불일치 → CLI 시료명 '{safe_name}' 사용")
        else:
            print(f"\n[안내] 새 시료 '{safe_name}' 으로 저장")
        return safe_name, seq_date

    from gc_state import get_seq_sample_name

    persisted = get_seq_sample_name(state_path, seq_date)
    if persisted:
        print(f"\n[안내] 이전에 지정한 시료명 재사용 → '{persisted}'")
        return persisted, seq_date

    if config.allow_prompt:
        from gc_chemstation import suggest_sample_name_from_folder

        default_name = suggest_sample_name_from_folder(sequence_folder_path) or ""
        return prompt_sample_name(seq_date, bool(existing_files), default_name=default_name), seq_date

    if is_new_sequence_date(config.excel_output_dir, seq_date, state_path=state_path):
        print(f"\n[오류] 새 날짜({seq_date}) 시퀀스 — 시료명을 반드시 지정해야 합니다.")
    else:
        print(
            f"\n[오류] 날짜 {seq_date} — KCH 기존 파일과 RT 패턴 불일치. "
            f"다른 시료이면 시료명을 지정해야 합니다."
        )
    print('       예: python gc_automation.py --sequence-date', seq_date, '--sample-name "시료이름" --force')
    print("       (자동 --watch 는 시료명 입력 불가 → 수동 실행 필요)")
    return None, seq_date


def build_stacked_dataframe(cycle_peaks_list: List[List[dict]]) -> pd.DataFrame:
    """
    KCH 레이아웃: 1주입은 peak만, 2주입부터 헤더 행 + peak 반복.
    """
    rows = []
    for idx, peaks in enumerate(cycle_peaks_list):
        if idx > 0:
            rows.append(HEADER_ROW.copy())
        rows.extend(peaks)
    return pd.DataFrame(rows, columns=CHEMSTATION_COLUMNS)


def build_output_filename(excel_output_dir: str, sample_name: str, seq_date: str) -> str:
    return build_safe_output_filename(excel_output_dir, sample_name, seq_date)


def build_stacked_dataframe_chem32(cycle_peaks_list: List[List[dict]]) -> pd.DataFrame:
    """GC3 레이아웃 — 매 주입마다 헤더 + 피크 (피크 개수 가변)."""
    rows = []
    for peaks in cycle_peaks_list:
        rows.append(CHEM32_HEADER_ROW.copy())
        rows.extend(peaks)
    return pd.DataFrame(rows, columns=CHEM32_COLUMNS)


def write_chem32_excel(
    output_path: str,
    fid_cycles: List[List[dict]],
    tcd_cycles: List[List[dict]],
) -> None:
    """FID / TCD 각각 별도 시트."""
    with pd.ExcelWriter(output_path, engine="openpyxl") as writer:
        build_stacked_dataframe_chem32(fid_cycles).to_excel(
            writer,
            sheet_name=CHEM32_FID_SHEET,
            index=False,
            header=False,
        )
        build_stacked_dataframe_chem32(tcd_cycles).to_excel(
            writer,
            sheet_name=CHEM32_TCD_SHEET,
            index=False,
            header=False,
        )


def resolve_sample_name(
    config: AppConfig,
    sample_folder: str,
    script_dir: str,
    default_from_folder: str,
) -> str:
    if config.sample_name:
        try:
            return sanitize_sample_name(config.sample_name)
        except InvalidSampleNameError as exc:
            print(f"[오류] {exc}")
            return ""
    load_dotenv_files(script_dir, config.excel_output_dir)
    env_name = os.getenv("SAMPLE_NAME", "").strip()
    if env_name:
        try:
            return sanitize_sample_name(env_name)
        except InvalidSampleNameError as exc:
            print(f"[오류] {exc}")
            return ""
    try:
        return sanitize_sample_name(default_from_folder)
    except InvalidSampleNameError as exc:
        print(f"[오류] 시료 폴더명 사용 불가 — {exc}")
        return ""
