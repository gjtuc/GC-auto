# -*- coding: utf-8 -*-
"""
gc_chemstation.py — ChemStation Data 폴더 탐색 및 sequence.acam_ 파싱

=============================================================================
[어느 PC / GC]
=============================================================================

  **GC2 (차헌) 장비 PC 전용.** GC1은 Autochro PDF(gc_autochro/gc_gc1), GC3은 gc_chem32.

[데이터 소스]
  ChemStation 8860: .D 주입 폴더 안 ACAML XML `sequence.acam_` 에 통합 피크.
  Report.txt 는 사용하지 않습니다.

  Data 루트: gc_config.DEFAULT_CHEMSTATION_DATA (보통 Public\\Documents\\ChemStation\\1\\Data)
  출력: Desktop\\KCH\\YYYYMMDD 시료.xlsx → gc_mailer → 데이터 PC 메일
"""

from __future__ import annotations

import glob
import os
import re
import xml.etree.ElementTree as ET
from datetime import datetime
from typing import Dict, List, Optional, Tuple

from gc_config import RT_TOLERANCE
from gc_sanitize import InvalidSequenceFolderError, validate_sequence_folder

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


def get_latest_sequence_folder(base_path: str) -> Optional[str]:
    """Data 아래 수정 시각이 가장 최근인 시퀀스 하위 폴더."""
    try:
        subfolders = [entry.path for entry in os.scandir(base_path) if entry.is_dir()]
        if not subfolders:
            return None
        return max(subfolders, key=os.path.getmtime)
    except OSError as exc:
        print(f"[오류] 최신 시퀀스 폴더 검색 실패: {exc}")
        return None


def find_sequence_folder(
    base_path: str,
    sequence_date: Optional[str] = None,
    sequence_folder: Optional[str] = None,
) -> Optional[str]:
    """
    처리 대상 시퀀스 폴더 결정.

    우선순위:
      1) --sequence-folder 절대 경로
      2) --sequence-date 가 폴더명 또는 수정일과 매칭
      3) base_path 아래 최신 폴더 (--watch 기본)
    """
    if sequence_folder:
        try:
            safe_folder = validate_sequence_folder(sequence_folder, base_path)
        except InvalidSequenceFolderError as exc:
            print(f"[오류] {exc}")
            return None
        print(f"[안내] 지정된 시퀀스 폴더: {safe_folder}")
        return safe_folder

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
        chosen = max(candidates, key=os.path.getmtime)
        print(f"[안내] 날짜({sequence_date}) 포함 시퀀스: {chosen}")
        return chosen

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
        chosen = max(candidates, key=os.path.getmtime)
        print(f"[안내] 수정일({target_date}) 기준 시퀀스: {chosen}")
        return chosen

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

    F- 로 시작하고 .d 로 끝나는 폴더만 (method.M 등 제외).
    """
    injections = []
    for entry in os.scandir(sequence_folder_path):
        if not entry.is_dir():
            continue
        if not entry.name.lower().endswith(".d"):
            continue
        if not entry.name.upper().startswith("F-"):
            continue
        injections.append(entry.path)
    return sorted(injections, key=_injection_sort_key)


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
    """시퀀스 내 sequence.acam_ 중 가장 최근 수정 시각 (watch 새 데이터 판별)."""
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
