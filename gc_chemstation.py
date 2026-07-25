# -*- coding: utf-8 -*-
"""
gc_chemstation.py — ChemStation Data 폴더 탐색 및 sequence.acam_ 파싱

=============================================================================
[어느 PC / GC]
=============================================================================

  **GC2/GC3 장비 PC (차헌) 전용.** GC1은 Autochro PDF(gc_autochro/gc_gc1), GC3은 gc_chem32.

[데이터 소스]
  ChemStation 8860: .D 주입 폴더 안 ACAML XML `sequence.acam_` 에 통합 피크.
  Report.txt 는 사용하지 않습니다.

  Data 루트: gc_config.DEFAULT_CHEMSTATION_DATA (보통 Public\\Documents\\ChemStation\\1\\Data)
  출력: Desktop\\KCH\\시료명.xlsx → gc_mailer → 차헌 PC 메일

[GC2 시료 폴더 규칙]
  · Data\\{시료폴더}\\{시퀀스…}\\F-YYYY-MM-DD-….D\\sequence.acam_
  · 활성 시료 = 가장 최근 F- 주입 시각이 들어 있는 Data 직계 폴더
  · 시료 폴더 안 시퀀스 여러 개 → 시간순 병합 + 분석 중단(갭) 행 (GC3와 동일 계약)
  · 폴더명 정규화: 20260724DRE(1.5)600CNi… → 20260724 DRE(1.5%)@600C Ni…
  · `… sequence YYYY-MM-DD …` 자동명은 시료명으로 쓰지 않음 (사용자 확인 필수)
"""

from __future__ import annotations

import glob
import os
import re
import statistics
import xml.etree.ElementTree as ET
from datetime import datetime
from typing import Dict, List, Optional, Tuple

from gc_config import RT_TOLERANCE
from gc_sanitize import (
    InvalidSequenceFolderError,
    is_chemstation_auto_sequence_name,
    normalize_gc2_folder_sample_name,
    validate_sequence_folder,
)

# F-2026-06-13-16-12-55-... 형식에서 주입 시각 추출 (정렬용)
INJECTION_FOLDER_DT = re.compile(
    r"F-(\d{4})-(\d{2})-(\d{2})-(\d{2})-(\d{2})-(\d{2})",
    re.IGNORECASE,
)

# ChemStation가 저장하는 ACAML 파일명 후보
ACAM_FILENAMES = ("sequence.acam_", "sequence.acam", "Sequence.acam_", "Sequence.acam")


# ---------------------------------------------------------------------------
# XML 유틸 — namespace 무시, local tag 이름만 사용
# ---------------------------------------------------------------------------


def _local_tag(element) -> str:
    """`{urn:...}Peak` → `Peak`"""
    tag = element.tag
    return tag.split("}", 1)[-1] if "}" in tag else tag


def _child_text(element, local_name: str, default: str = "") -> str:
    for child in element:
        if _local_tag(child) == local_name:
            return (child.text or default).strip()
    return default


def _child_float(element, local_name: str, default=None):
    """`<RetentionTime val="6.337" />` 또는 텍스트 노드 모두 처리."""
    for child in element:
        if _local_tag(child) != local_name:
            continue
        if "val" in child.attrib:
            try:
                return float(child.attrib["val"])
            except ValueError:
                return default
        try:
            return float((child.text or "").strip())
        except ValueError:
            return default
    return default


# ---------------------------------------------------------------------------
# 시퀀스 / 주입 폴더
# ---------------------------------------------------------------------------
#
# 레이아웃 (둘 다 지원):
#   (A) 기존 flat
#       Data\20251221 sequence 2026-07-01 10-00-07\F-....D\sequence.acam_
#   (B) 중첩 wrapper
#       Data\20260710DRM(...)\20251221 sequence 2026-07-10 ...\F-....D\sequence.acam_
#


def _is_injection_dir_name(name: str) -> bool:
    """F- 로 시작하고 .d 로 끝나는 ChemStation 주입 폴더명."""
    lower = name.lower()
    return lower.endswith(".d") and name.upper().startswith("F-")


def list_direct_injection_folders(folder_path: str) -> List[str]:
    """한 폴더의 직계 자식 중 F-*.D 만 (정렬 없음)."""
    injections: List[str] = []
    try:
        for entry in os.scandir(folder_path):
            if entry.is_dir() and _is_injection_dir_name(entry.name):
                injections.append(entry.path)
    except OSError:
        return []
    return injections


def resolve_sequence_work_folder(sequence_folder_path: str) -> str:
    """
    실제 F-*.D 가 있는 시퀀스 작업 폴더로 해석.

    - flat: 인자 경로에 주입이 있으면 그대로
    - nested: 인자(wrapper) 바로 아래 자식 중 주입이 있는 폴더를 선택
    - 없으면 인자 경로 그대로 (호출측에서 주입 없음 처리)
    """
    if not sequence_folder_path or not os.path.isdir(sequence_folder_path):
        return sequence_folder_path

    if list_direct_injection_folders(sequence_folder_path):
        return sequence_folder_path

    nested: List[str] = []
    try:
        for entry in os.scandir(sequence_folder_path):
            if not entry.is_dir():
                continue
            if list_direct_injection_folders(entry.path):
                nested.append(entry.path)
    except OSError:
        return sequence_folder_path

    if not nested:
        return sequence_folder_path
    if len(nested) == 1:
        return nested[0]

    def _nested_score(path: str) -> float:
        latest = None
        for inj in list_direct_injection_folders(path):
            acam = find_sequence_acam_file(inj)
            if not acam:
                continue
            mtime = os.path.getmtime(acam)
            if latest is None or mtime > latest:
                latest = mtime
        return latest if latest is not None else os.path.getmtime(path)

    return max(nested, key=_nested_score)


def _sequence_activity_mtime(folder_path: str) -> float:
    """시퀀스(또는 wrapper)의 최신 활동 시각 — acam mtime 우선."""
    work = resolve_sequence_work_folder(folder_path)
    latest = None
    for inj in list_direct_injection_folders(work):
        acam = find_sequence_acam_file(inj)
        if not acam:
            continue
        mtime = os.path.getmtime(acam)
        if latest is None or mtime > latest:
            latest = mtime
    if latest is not None:
        return latest
    try:
        return os.path.getmtime(folder_path)
    except OSError:
        return 0.0


def _finalize_sequence_folder(chosen: str, *, label: str) -> str:
    """중첩이면 작업 폴더로 풀어 안내 후 반환."""
    resolved = resolve_sequence_work_folder(chosen)
    if os.path.normcase(os.path.abspath(resolved)) != os.path.normcase(os.path.abspath(chosen)):
        print(f"[안내] {label}: {chosen}")
        print(f"[안내] 중첩 시퀀스 해석 → {resolved}")
    else:
        print(f"[안내] {label}: {resolved}")
    return resolved


def get_latest_sequence_folder(base_path: str) -> Optional[str]:
    """
    Data 아래 가장 최근 시퀀스 폴더.

    주입(acam)이 있는 flat/중첩 후보를 우선하고, 최신 acam mtime 기준.
    """
    try:
        subfolders = [entry.path for entry in os.scandir(base_path) if entry.is_dir()]
    except OSError as exc:
        print(f"[오류] 최신 시퀀스 폴더 검색 실패: {exc}")
        return None
    if not subfolders:
        return None

    with_data = [
        path
        for path in subfolders
        if list_direct_injection_folders(resolve_sequence_work_folder(path))
    ]
    pool = with_data or subfolders
    chosen = max(pool, key=_sequence_activity_mtime)
    return resolve_sequence_work_folder(chosen)


def find_sequence_folder(
    base_path: str,
    sequence_date: Optional[str] = None,
    sequence_folder: Optional[str] = None,
) -> Optional[str]:
    """
    처리 대상 시퀀스 폴더 결정.

    우선순위:
      1) --sequence-folder 절대 경로 (중첩 wrapper 도 허용 → 작업 폴더로 해석)
      2) --sequence-date 가 폴더명 또는 수정일과 매칭
      3) base_path 아래 최신 폴더 (--watch 기본)

    flat·중첩 레이아웃 모두 실제 F-*.D 가 있는 작업 폴더를 반환.
    """
    if sequence_folder:
        try:
            safe_folder = validate_sequence_folder(sequence_folder, base_path)
        except InvalidSequenceFolderError as exc:
            print(f"[오류] {exc}")
            return None
        return _finalize_sequence_folder(safe_folder, label="지정된 시퀀스 폴더")

    if not sequence_date:
        latest = get_latest_sequence_folder(base_path)
        if latest:
            print(f"[안내] 최신 시퀀스 폴더 자동 선택: {latest}")
        return latest

    candidates = []
    for entry in os.scandir(base_path):
        if entry.is_dir() and sequence_date in entry.name:
            candidates.append(entry.path)

    if candidates:
        chosen = max(candidates, key=_sequence_activity_mtime)
        return _finalize_sequence_folder(
            chosen, label=f"날짜({sequence_date}) 포함 시퀀스"
        )

    try:
        target_date = datetime.strptime(sequence_date, "%Y%m%d").date()
    except ValueError:
        print(f"[오류] --sequence-date 형식은 YYYYMMDD: {sequence_date}")
        return None

    for entry in os.scandir(base_path):
        if not entry.is_dir():
            continue
        folder_date = datetime.fromtimestamp(os.path.getmtime(entry.path)).date()
        if folder_date == target_date:
            candidates.append(entry.path)

    if candidates:
        chosen = max(candidates, key=_sequence_activity_mtime)
        return _finalize_sequence_folder(
            chosen, label=f"수정일({target_date}) 기준 시퀀스"
        )

    print(f"[오류] 날짜 {sequence_date} 시퀀스를 찾을 수 없습니다.")
    return None


def get_sequence_date(sequence_folder_path: str, sequence_date: Optional[str] = None) -> str:
    """
    엑셀 파일명 접두사 YYYYMMDD.

    폴더명 예: `20251221 sequence 2026-06-13 16-12-52` → `20260613` (sequence 뒤 시작일)
    """
    if sequence_date:
        return sequence_date

    folder_name = os.path.basename(sequence_folder_path)
    seq_start = re.search(r"sequence\s+(\d{4})-(\d{2})-(\d{2})", folder_name, re.IGNORECASE)
    if seq_start:
        y, m, d = seq_start.groups()
        return f"{y}{m}{d}"

    anywhere = re.search(r"(20\d{6})", folder_name)
    if anywhere:
        return anywhere.group(1)

    return datetime.fromtimestamp(os.path.getmtime(sequence_folder_path)).strftime("%Y%m%d")


def _injection_sort_key(folder_path: str) -> datetime:
    """폴더명 F-YYYY-MM-DD-HH-MM-SS 기준 정렬, 실패 시 mtime."""
    name = os.path.basename(folder_path)
    match = INJECTION_FOLDER_DT.search(name)
    if match:
        return datetime(*map(int, match.groups()))
    return datetime.fromtimestamp(os.path.getmtime(folder_path))


def find_injection_folders(sequence_folder_path: str) -> List[str]:
    """
    시퀀스 내 주입(.D) 폴더를 주입 시각 순으로 반환.

    flat·중첩 wrapper 모두 resolve_sequence_work_folder 후
    F- 로 시작하고 .d 로 끝나는 폴더만 (method.M 등 제외).
    """
    work = resolve_sequence_work_folder(sequence_folder_path)
    injections = list_direct_injection_folders(work)
    return sorted(injections, key=_injection_sort_key)


def find_8860_sequence_folders(sample_folder: str) -> List[str]:
    """
    시료 폴더 아래 시퀀스 작업 폴더 목록 (F-*.D 보유).

    - 시료 폴더에 주입이 직접 있으면 그 폴더 1개 (flat)
    - 아니면 직계 자식 중 주입이 있는 폴더들 (중단 후 재시작 시 여러 개)
    """
    if not sample_folder or not os.path.isdir(sample_folder):
        return []
    if list_direct_injection_folders(sample_folder):
        return [sample_folder]

    sequences: List[str] = []
    try:
        for entry in os.scandir(sample_folder):
            if not entry.is_dir():
                continue
            work = resolve_sequence_work_folder(entry.path)
            if list_direct_injection_folders(work):
                sequences.append(work)
    except OSError:
        return []
    # 시퀀스 폴더명·활동 시각 순
    return sorted(sequences, key=lambda path: (_sequence_activity_mtime(path), path))


def collect_acam_injections(sample_folder: str) -> List[Tuple[str, str]]:
    """시료 폴더 아래 모든 시퀀스의 (주입경로, 시퀀스경로) — F- 시각 순."""
    items: List[Tuple[str, str]] = []
    for sequence_path in find_8860_sequence_folders(sample_folder):
        for injection_path in find_injection_folders(sequence_path):
            if find_sequence_acam_file(injection_path):
                items.append((injection_path, sequence_path))
    return sorted(items, key=lambda item: _injection_sort_key(item[0]))


def newest_injection_datetime(sample_folder: str) -> Optional[datetime]:
    """시료 폴더 안 F-YYYY-MM-DD-HH-MM-SS 중 가장 늦은 시각."""
    best: Optional[datetime] = None
    for sequence_path in find_8860_sequence_folders(sample_folder):
        for injection_path in find_injection_folders(sequence_path):
            stamp = _injection_sort_key(injection_path)
            if best is None or stamp > best:
                best = stamp
    return best


def _is_8860_sample_candidate(folder_path: str) -> bool:
    return bool(find_8860_sequence_folders(folder_path))


def find_active_sample_folder_8860(
    data_path: str,
    sequence_folder: Optional[str] = None,
) -> Optional[str]:
    """
    Data 아래 활성 **시료** 폴더.

    가장 최근 F- 주입 시각이 들어 있는 Data 직계 폴더를 고른다.
    (시퀀스 내부 폴더가 아니라 실험 단위 wrapper)
    """
    if sequence_folder:
        try:
            safe = validate_sequence_folder(sequence_folder, data_path)
        except InvalidSequenceFolderError as exc:
            print(f"[오류] {exc}")
            return None
        parent = os.path.dirname(safe)
        data_abs = os.path.normcase(os.path.abspath(data_path))
        parent_abs = os.path.normcase(os.path.abspath(parent))
        if parent_abs == data_abs:
            return safe
        if _is_8860_sample_candidate(parent):
            return parent
        if _is_8860_sample_candidate(safe):
            return safe
        return safe

    try:
        children = [entry.path for entry in os.scandir(data_path) if entry.is_dir()]
    except OSError as exc:
        print(f"[오류] 시료 폴더 검색 실패: {exc}")
        return None

    candidates = [path for path in children if _is_8860_sample_candidate(path)]
    if not candidates:
        print("[오류] Data 아래 주입(F-*.D)이 있는 시료 폴더가 없습니다.")
        return None

    def _score(path: str) -> Tuple[datetime, float]:
        newest = newest_injection_datetime(path) or datetime.min
        try:
            mtime = os.path.getmtime(path)
        except OSError:
            mtime = 0.0
        return (newest, mtime)

    chosen = max(candidates, key=_score)
    print(f"[안내] 활성 시료 폴더: {chosen}")
    print(f"       (최신 F- 주입: {newest_injection_datetime(chosen)})")
    return chosen


def suggest_sample_name_from_folder(sample_folder: str) -> Optional[str]:
    """시료 폴더명 → 정규화 기본 시료명 (자동 시퀀스명이면 None)."""
    return normalize_gc2_folder_sample_name(os.path.basename(sample_folder.rstrip("\\/")))


def get_sample_seq_date(sample_folder: str, sequence_date: Optional[str] = None) -> str:
    """엑셀·상태용 YYYYMMDD — 폴더 선두 날짜 또는 최신 F- 날짜."""
    if sequence_date:
        return sequence_date
    name = os.path.basename(sample_folder.rstrip("\\/"))
    if not is_chemstation_auto_sequence_name(name):
        leading = re.match(r"^(20\d{6})", name)
        if leading:
            return leading.group(1)
    newest = newest_injection_datetime(sample_folder)
    if newest is not None:
        return newest.strftime("%Y%m%d")
    return get_sequence_date(sample_folder, None)


def get_latest_injection_acam_mtime_under_sample(sample_folder: str) -> Optional[float]:
    """시료 폴더(복수 시퀀스) 전체에서 최신 acam mtime."""
    latest: Optional[float] = None
    for injection_path, _seq in collect_acam_injections(sample_folder):
        acam = find_sequence_acam_file(injection_path)
        if not acam:
            continue
        mtime = os.path.getmtime(acam)
        if latest is None or mtime > latest:
            latest = mtime
    return latest


def _injection_timestamp_sec(injection_path: str) -> Optional[float]:
    name = os.path.basename(injection_path)
    match = INJECTION_FOLDER_DT.search(name)
    if match:
        return datetime(*map(int, match.groups())).timestamp()
    try:
        return os.path.getmtime(injection_path)
    except OSError:
        return None


def detect_analysis_gaps_acam(sample_folder: str):
    """
    GC2 acam 주입 시각(F- 폴더명) 기준 분석 중단 갭 — GC3 계약과 동일 마커.
    """
    from gc_chem32 import AnalysisGap, estimate_missing_cycles_floor

    injections = collect_acam_injections(sample_folder)
    timed: List[Tuple[int, str, str, float]] = []
    for index, (injection_path, sequence_path) in enumerate(injections):
        stamp = _injection_timestamp_sec(injection_path)
        if stamp is not None:
            timed.append((index, injection_path, sequence_path, stamp))

    if len(timed) < 2:
        return [], None

    deltas = [timed[i][3] - timed[i - 1][3] for i in range(1, len(timed)) if timed[i][3] > timed[i - 1][3]]
    if not deltas:
        return [], None
    interval_sec = float(statistics.median(deltas))
    if interval_sec <= 0:
        return [], interval_sec

    gaps = []
    for pos in range(1, len(timed)):
        prev_index, _prev_path, prev_seq, prev_stamp = timed[pos - 1]
        curr_index, _curr_path, curr_seq, curr_stamp = timed[pos]
        gap_sec = curr_stamp - prev_stamp
        if gap_sec <= 0:
            continue
        missing, remainder = estimate_missing_cycles_floor(gap_sec, interval_sec)
        if missing < 2:
            continue
        gaps.append(
            AnalysisGap(
                after_injection_index=prev_index,
                before_injection_index=curr_index,
                after_sequence=os.path.basename(prev_seq),
                before_sequence=os.path.basename(curr_seq),
                gap_sec=gap_sec,
                interval_sec=interval_sec,
                missing_cycles=missing,
                remainder_sec=remainder,
                after_last_at=datetime.fromtimestamp(prev_stamp),
                before_first_at=datetime.fromtimestamp(curr_stamp),
            )
        )
    return gaps, interval_sec


def insert_analysis_gap_markers_acam(
    cycles: List[List[dict]],
    matched_injection_paths: List[str],
    analysis_gaps,
    all_injections: List[Tuple[str, str]],
) -> List[List[dict]]:
    """단일 Sheet1 사이클 목록에 GC3와 같은 중단 마커 행 삽입."""
    from gc_chem32 import _gap_marker_excel_position, gap_marker_cycle

    if not analysis_gaps or not matched_injection_paths:
        return cycles

    out = list(cycles)
    pending: List[Tuple[int, List[dict]]] = []
    for gap in analysis_gaps:
        pos = _gap_marker_excel_position(gap, matched_injection_paths, all_injections)
        if pos is None or pos < 0 or pos > len(out):
            print(
                f"[경고] 갭 행 삽입 생략 — 엑셀 위치 {pos} "
                f"(갭 #{gap.after_injection_index + 1}→#{gap.before_injection_index + 1})"
            )
            continue
        after_folder = os.path.basename(all_injections[gap.after_injection_index][0])
        before_folder = os.path.basename(all_injections[gap.before_injection_index][0])
        marker = gap_marker_cycle(
            gap,
            after_folder=after_folder,
            before_folder=before_folder,
        )
        # GC2 컬럼에 Type 자리 맞춤
        for row in marker:
            row.setdefault(" Type", "")
        pending.append((pos, marker))
        print(
            f"[안내] 엑셀 갭 행 삽입 위치 #{pos + 1} — "
            f"약 {gap.missing_cycles}사이클 미수집 "
            f"({after_folder}→{before_folder})"
        )

    for pos, marker in sorted(pending, key=lambda item: item[0], reverse=True):
        out.insert(pos, marker)
    return out


def build_merged_acam_cycles(
    sample_folder: str,
    detector: str = "TCD",
) -> Tuple[List[List[dict]], List[str], List[str], List[str], int]:
    """
    시료 폴더 아래 모든 시퀀스 acam → 시간순 사이클 1목록.

    Returns:
        (cycles, injection_labels, matched_paths, missing_acam, skipped_startup)
    """
    from gc_chem32 import log_analysis_gaps

    all_injections = collect_acam_injections(sample_folder)
    sequences = find_8860_sequence_folders(sample_folder)
    print(
        f"[안내] 시퀀스 {len(sequences)}개 / acam 주입 {len(all_injections)}개 "
        f"(시료: {os.path.basename(sample_folder)})"
    )

    gaps, interval = detect_analysis_gaps_acam(sample_folder)
    log_analysis_gaps(gaps, interval)

    cycles: List[List[dict]] = []
    labels: List[str] = []
    matched_paths: List[str] = []
    missing_acam: List[str] = []

    # acam 없는 F- 도 안내
    for sequence_path in sequences:
        for injection_path in find_injection_folders(sequence_path):
            if find_sequence_acam_file(injection_path):
                continue
            missing_acam.append(os.path.basename(injection_path))
            print(f"[경고] sequence.acam_ 없음: {os.path.basename(injection_path)}")

    for injection_path, _sequence_path in all_injections:
        injection_name = os.path.basename(injection_path)
        acam_path = find_sequence_acam_file(injection_path)
        if not acam_path:
            continue
        peaks = parse_sequence_acam(acam_path, detector=detector)
        if peaks:
            cycles.append(peaks)
            labels.append(injection_name)
            matched_paths.append(injection_path)
            print(f"[진행] {injection_name}: 피크 {len(peaks)}개")
        else:
            print(f"[경고] 피크 없음: {injection_name}")

    skipped = 0
    if cycles:
        first_label = labels[0] if labels else None
        cycles, skipped_first, _info = drop_first_cycle_if_startup_noise(
            cycles,
            first_injection_label=first_label,
        )
        if skipped_first:
            skipped = 1
            labels = labels[1:]
            matched_paths = matched_paths[1:]

    if cycles and gaps:
        cycles = insert_analysis_gap_markers_acam(
            cycles,
            matched_paths,
            gaps,
            all_injections,
        )

    return cycles, labels, matched_paths, missing_acam, skipped


def find_sequence_acam_file(injection_folder_path: str) -> Optional[str]:
    """한 주입 폴더에서 sequence.acam_ 파일 경로."""
    for filename in ACAM_FILENAMES:
        candidate = os.path.join(injection_folder_path, filename)
        if os.path.isfile(candidate):
            return candidate
    matches = glob.glob(os.path.join(injection_folder_path, "sequence.acam*"))
    matches = [path for path in matches if os.path.isfile(path)]
    return matches[0] if matches else None


def get_latest_injection_acam_mtime(sequence_folder: str) -> Optional[float]:
    """시퀀스·시료 폴더 내 sequence.acam_ 중 가장 최근 수정 시각 (watch 새 데이터 판별)."""
    under = get_latest_injection_acam_mtime_under_sample(sequence_folder)
    if under is not None:
        return under
    # flat 단일 시퀀스 폴백
    latest_mtime = None
    for injection_path in find_injection_folders(sequence_folder):
        acam_path = find_sequence_acam_file(injection_path)
        if not acam_path:
            continue
        mtime = os.path.getmtime(acam_path)
        if latest_mtime is None or mtime > latest_mtime:
            latest_mtime = mtime
    return latest_mtime


# ---------------------------------------------------------------------------
# ACAML → 피크 dict 리스트 (KCH 엑셀 1사이클)
# ---------------------------------------------------------------------------


def _build_signal_detector_map(root) -> Dict[str, str]:
    """Signal id → 'TCD1 ...' 같은 메타 문자열."""
    mapping = {}
    for elem in root.iter():
        if _local_tag(elem) != "Signal":
            continue
        sig_id = elem.get("id")
        if not sig_id:
            continue
        sig_type = _child_text(elem, "Type")
        sig_name = _child_text(elem, "Name")
        mapping[sig_id] = (sig_type + " " + sig_name).upper()
    return mapping


def _signal_matches_detector(signal_id: str, signal_map: Dict[str, str], detector: str) -> bool:
    if not detector:
        return True
    meta = signal_map.get(signal_id, "")
    return detector.upper() in meta


def _baseline_code_to_excel_type(baseline_code: str) -> str:
    """ACAML BaselineCode → KCH ` Type` 열 (앞에 공백 포함)."""
    code = (baseline_code or "BB").strip()
    return f" {code}  "


def parse_sequence_acam(acam_path: str, detector: str = "TCD") -> List[dict]:
    """
    sequence.acam_ 한 파일에서 피크 행 목록 추출.

    Returns:
        KCH 컬럼 키를 가진 dict 리스트 (RT 순 정렬, # 재부여)
    """
    try:
        tree = ET.parse(acam_path)
        root = tree.getroot()
    except ET.ParseError as exc:
        print(f"[오류] ACAML XML 파싱 실패 ({acam_path}): {exc}")
        return []

    signal_map = _build_signal_detector_map(root)
    peaks = []
    peak_index = 0

    for elem in root.iter():
        if _local_tag(elem) != "SignalResult":
            continue

        signal_id = None
        for child in elem:
            if _local_tag(child) == "Signal_ID":
                signal_id = child.get("id")
                break

        if detector and signal_id and not _signal_matches_detector(signal_id, signal_map, detector):
            continue

        for peak_elem in elem:
            if _local_tag(peak_elem) != "Peak":
                continue

            peak_index += 1
            rt = _child_float(peak_elem, "RetentionTime")
            area = _child_float(peak_elem, "Area")
            height = _child_float(peak_elem, "Height")
            width = _child_float(peak_elem, "WidthBase")
            area_pct = _child_float(peak_elem, "AreaPercent")
            symmetry = _child_float(peak_elem, "Symmetry")
            baseline_code = _child_text(peak_elem, "BaselineCode", "BB")

            if rt is None or area is None:
                continue

            peaks.append(
                {
                    "#": peak_index,
                    "Time": round(rt, 3),
                    " Type": _baseline_code_to_excel_type(baseline_code),
                    "Area": round(area, 1) if area is not None else area,
                    "Height": round(height, 1) if height is not None else height,
                    "Width": round(width, 4) if width is not None else width,
                    "Area%": round(area_pct, 3) if area_pct is not None else area_pct,
                    "Symmetry": round(symmetry, 3) if symmetry is not None else symmetry,
                }
            )

    peaks.sort(key=lambda row: row["Time"])
    for index, row in enumerate(peaks, start=1):
        row["#"] = index
    return peaks


# ---------------------------------------------------------------------------
# 1주입 startup 노이즈 제거
# ---------------------------------------------------------------------------


def _cycle_rt_tuple(peaks: List[dict]) -> Tuple[float, ...]:
    return tuple(round(float(p["Time"]), 3) for p in peaks)


def rt_patterns_match(rt_a: Tuple[float, ...], rt_b: Tuple[float, ...], rt_tolerance: float = RT_TOLERANCE) -> bool:
    if len(rt_a) != len(rt_b):
        return False
    return all(abs(a - b) <= rt_tolerance for a, b in zip(rt_a, rt_b))


def drop_first_cycle_if_startup_noise(
    cycle_peaks_list: List[List[dict]],
    first_injection_label: Optional[str] = None,
) -> Tuple[List[List[dict]], bool, Optional[dict]]:
    """
    1주입 RT 패턴이 2주입과 다르면 startup 노이즈로 보고 1주입 제외.

    Returns:
        (filtered_cycles, skipped_first, skip_info)
    """
    if len(cycle_peaks_list) < 2:
        return cycle_peaks_list, False, None

    first_rts = _cycle_rt_tuple(cycle_peaks_list[0])
    reference_rts = _cycle_rt_tuple(cycle_peaks_list[1])

    if rt_patterns_match(first_rts, reference_rts):
        return cycle_peaks_list, False, None

    label = first_injection_label or "1번째 주입"
    print(f"\n[안내] startup 노이즈로 판단 — {label} 제외, 2번째 주입부터 적재")
    print(f"       1주입 RT ({len(first_rts)}피크): {list(first_rts)}")
    print(f"       2주입 RT ({len(reference_rts)}피크): {list(reference_rts)}")
    skip_info = {
        "label": label,
        "first_rts": list(first_rts),
        "reference_rts": list(reference_rts),
    }
    return cycle_peaks_list[1:], True, skip_info
