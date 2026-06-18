# -*- coding: utf-8 -*-
"""
gc_chem32.py — Chem32 / GC7890 (GC3) Data 경로·Report 파싱

=============================================================================
[어느 PC / GC]
=============================================================================

  **GC3 장비 PC (차헌) 전용.** env: GC_INSTANCE=gc3, CHEMSTATION_MODE=chem32.
  계산·Origin은 **차헌 PC** (Desktop\\.cursor). 본 PC는 gc_automation.py 만.

GC3 폴더 구조:
  DATA / {시료 폴더} / {REACTION 시퀀스} / 001F0101.D / Report.TXT, REPORT01/02.CSV

피크 개수는 가변 — FID·TCD 각각 Report 에 있는 만큼만 사용.
출력·메일 흐름은 GC2와 동일 (Desktop\\KCH).
"""

from __future__ import annotations

import csv
import glob
import os
import re
from datetime import datetime
from typing import Dict, List, Optional, Tuple

from gc_config import AREA_MATCH_TOLERANCE, RT_TOLERANCE
from gc_chemstation import drop_first_cycle_if_startup_noise

REACTION_DT = re.compile(
    r"REACTION\s+(\d{4})-(\d{2})-(\d{2})\s+(\d{2})-(\d{2})-(\d{2})",
    re.IGNORECASE,
)
CHEM32_INJECTION_RE = re.compile(r"^001F(\d+)\.D$", re.IGNORECASE)
SAMPLE_FOLDER_DATE_RE = re.compile(r"^(\d{8})\s+(.+)$")
REPORT_PEAK_LINE = re.compile(
    r"^\s*(\d+)\s+([\d.]+)\s+(\S+)\s+([\d.]+)\s+([\d.eE+-]+)\s+([\d.]+)\s+([\d.]+)\s*$"
)


def resolve_chemstation_mode(data_path: str, mode: str) -> str:
    """auto | chem32 | 8860"""
    if mode in ("chem32", "8860"):
        return mode
    if "chem32" in data_path.replace("/", "\\").lower():
        return "chem32"
    if not os.path.isdir(data_path):
        return "8860"
    for entry in os.scandir(data_path):
        if not entry.is_dir():
            continue
        if _folder_contains_reaction_sequences(entry.path):
            return "chem32"
    return "8860"


def _folder_contains_reaction_sequences(folder_path: str) -> bool:
    try:
        for entry in os.scandir(folder_path):
            if entry.is_dir() and _is_sequence_folder(entry.path):
                return True
    except OSError:
        return False
    return False


def _is_sequence_folder(folder_path: str) -> bool:
    try:
        for entry in os.scandir(folder_path):
            if entry.is_dir() and CHEM32_INJECTION_RE.match(entry.name):
                return True
    except OSError:
        return False
    return False


def find_sample_folders(data_path: str) -> List[str]:
    folders = []
    try:
        for entry in os.scandir(data_path):
            if entry.is_dir() and _folder_contains_reaction_sequences(entry.path):
                folders.append(entry.path)
    except OSError:
        return []
    return sorted(folders, key=os.path.getmtime, reverse=True)


def find_active_sample_folder(
    data_path: str,
    sequence_folder: Optional[str] = None,
) -> Optional[str]:
    if sequence_folder:
        path = os.path.abspath(sequence_folder)
        if _is_sequence_folder(path):
            return os.path.dirname(path)
        if _folder_contains_reaction_sequences(path):
            return path
        parent = os.path.dirname(path)
        if _folder_contains_reaction_sequences(parent):
            return parent

    samples = find_sample_folders(data_path)
    if samples:
        chosen = samples[0]
        print(f"[안내] Chem32 시료 폴더 자동 선택: {chosen}")
        return chosen
    return None


def find_sequence_folders(sample_folder: str) -> List[str]:
    sequences = []
    try:
        for entry in os.scandir(sample_folder):
            if entry.is_dir() and _is_sequence_folder(entry.path):
                sequences.append(entry.path)
    except OSError:
        return []
    return sorted(sequences, key=_sequence_sort_key)


def _sequence_sort_key(sequence_path: str) -> datetime:
    match = REACTION_DT.search(os.path.basename(sequence_path))
    if match:
        y, mo, d, h, mi, s = map(int, match.groups())
        return datetime(y, mo, d, h, mi, s)
    return datetime.fromtimestamp(os.path.getmtime(sequence_path))


def find_chem32_injection_folders(sequence_folder: str) -> List[str]:
    injections = []
    try:
        for entry in os.scandir(sequence_folder):
            if entry.is_dir() and CHEM32_INJECTION_RE.match(entry.name):
                injections.append(entry.path)
    except OSError:
        return []
    return sorted(injections, key=_injection_sort_key)


def _injection_sort_key(injection_path: str) -> Tuple[int, float]:
    name = os.path.basename(injection_path)
    match = CHEM32_INJECTION_RE.match(name)
    if match:
        return (int(match.group(1)), os.path.getmtime(injection_path))
    return (0, os.path.getmtime(injection_path))


def find_report_txt(injection_folder: str) -> Optional[str]:
    for name in ("Report.TXT", "Report.txt", "REPORT.TXT"):
        path = os.path.join(injection_folder, name)
        if os.path.isfile(path):
            return path
    matches = glob.glob(os.path.join(injection_folder, "Report*.txt"))
    matches = [path for path in matches if os.path.isfile(path)]
    return matches[0] if matches else None


def find_report_csv(injection_folder: str, index: int) -> Optional[str]:
    """REPORT01.CSV = FID, REPORT02.CSV = TCD (Chem32 기본)."""
    for pattern in (f"REPORT{index:02d}.CSV", f"Report{index:02d}.CSV"):
        path = os.path.join(injection_folder, pattern)
        if os.path.isfile(path):
            return path
    return None


def get_first_analysis_date(sample_folder: str) -> str:
    """시퀀스 최초 실행일 YYYYMMDD — 폴더명 REACTION 날짜 중 가장 이른 값."""
    earliest = None
    for sequence_path in find_sequence_folders(sample_folder):
        match = REACTION_DT.search(os.path.basename(sequence_path))
        if not match:
            continue
        y, mo, d, *_ = map(int, match.groups())
        dt = datetime(y, mo, d)
        if earliest is None or dt < earliest:
            earliest = dt
    if earliest:
        return earliest.strftime("%Y%m%d")
    folder_name = os.path.basename(sample_folder)
    head = re.match(r"^(\d{8})", folder_name)
    if head:
        return head.group(1)
    return datetime.fromtimestamp(os.path.getmtime(sample_folder)).strftime("%Y%m%d")


def default_sample_name_from_folder(sample_folder: str) -> str:
    name = os.path.basename(sample_folder)
    match = SAMPLE_FOLDER_DATE_RE.match(name)
    if match:
        return match.group(2).strip()
    return name.strip()


def _round_peak_value(value, decimals: int):
    if value is None or value == "":
        return ""
    try:
        return round(float(value), decimals)
    except (TypeError, ValueError):
        return value


def _peak_row(
    index: int,
    rt: float,
    width: float,
    area: float,
    height: float,
    area_pct: float,
) -> dict:
    return {
        "#": index,
        "Time": _round_peak_value(rt, 3),
        "Area": _round_peak_value(area, 1),
        "Height": _round_peak_value(height, 1),
        "Width": _round_peak_value(width, 4),
        "Area%": _round_peak_value(area_pct, 3),
        "Symmetry": "",
    }


def _open_chem32_text(path: str):
    """Chem32 Report 파일 — UTF-16 LE(Windows) 또는 UTF-8."""
    with open(path, "rb") as raw_file:
        bom = raw_file.read(4)
    if bom.startswith(b"\xff\xfe") or bom.startswith(b"\xfe\xff"):
        encoding = "utf-16"
    elif bom.startswith(b"\xef\xbb\xbf"):
        encoding = "utf-8-sig"
    else:
        encoding = "utf-8"
    return open(path, encoding=encoding, errors="replace")


def parse_report_csv(csv_path: str) -> List[dict]:
    peaks = []
    with _open_chem32_text(csv_path) as csv_file:
        for row in csv.reader(csv_file):
            if len(row) < 7:
                continue
            try:
                peaks.append(
                    _peak_row(
                        int(row[0]),
                        float(row[1]),
                        float(row[3]),
                        float(row[4]),
                        float(row[5]),
                        float(row[6]),
                    )
                )
            except ValueError:
                continue
    peaks.sort(key=lambda item: float(item["Time"]))
    for index, peak in enumerate(peaks, start=1):
        peak["#"] = index
    return peaks


def parse_report_txt(report_path: str) -> Dict[str, List[dict]]:
    """Report.TXT → {"FID": [...], "TCD": [...]} (피크 개수 가변)."""
    result: Dict[str, List[dict]] = {"FID": [], "TCD": []}
    current = None
    peak_index = 0

    with _open_chem32_text(report_path) as report_file:
        for line in report_file:
            if line.startswith("Signal "):
                upper = line.upper()
                if "FID" in upper:
                    current = "FID"
                elif "TCD" in upper:
                    current = "TCD"
                else:
                    current = None
                peak_index = 0
                continue
            if current is None:
                continue
            match = REPORT_PEAK_LINE.match(line.rstrip())
            if not match:
                continue
            peak_index += 1
            result[current].append(
                _peak_row(
                    peak_index,
                    float(match.group(2)),
                    float(match.group(4)),
                    float(match.group(5)),
                    float(match.group(6)),
                    float(match.group(7)),
                )
            )
    return result


def parse_injection_reports(injection_folder: str) -> Dict[str, List[dict]]:
    report_txt = find_report_txt(injection_folder)
    if report_txt:
        parsed = parse_report_txt(report_txt)
        if parsed["FID"] or parsed["TCD"]:
            return parsed

    fid_csv = find_report_csv(injection_folder, 1)
    tcd_csv = find_report_csv(injection_folder, 2)
    return {
        "FID": parse_report_csv(fid_csv) if fid_csv else [],
        "TCD": parse_report_csv(tcd_csv) if tcd_csv else [],
    }


def get_latest_report_mtime(sample_folder: str) -> Optional[float]:
    latest = None
    for sequence_path in find_sequence_folders(sample_folder):
        for injection_path in find_chem32_injection_folders(sequence_path):
            report_path = find_report_txt(injection_path)
            if not report_path:
                continue
            mtime = os.path.getmtime(report_path)
            if latest is None or mtime > latest:
                latest = mtime
    return latest


def collect_reported_injections(sample_folder: str) -> List[Tuple[str, str]]:
    """(injection_path, sequence_path) — Report 있는 주입만, 시간순."""
    collected = []
    for sequence_path in find_sequence_folders(sample_folder):
        for injection_path in find_chem32_injection_folders(sequence_path):
            if find_report_txt(injection_path):
                collected.append((injection_path, sequence_path))
    collected.sort(key=lambda item: (_sequence_sort_key(item[1]), _injection_sort_key(item[0])))
    return collected


def _cycle_signature(peaks: List[dict]) -> Tuple[Tuple[float, float], ...]:
    return tuple(
        (round(float(peak["Time"]), 3), round(float(peak["Area"]), 1)) for peak in peaks
    )


def cycles_match(
    reference: List[dict],
    candidate: List[dict],
    rt_tolerance: float = RT_TOLERANCE,
    area_tolerance: float = AREA_MATCH_TOLERANCE,
) -> bool:
    if not reference or not candidate:
        return False
    if len(reference) != len(candidate):
        return False
    for ref_peak, new_peak in zip(reference, candidate):
        rt_diff = abs(float(ref_peak["Time"]) - float(new_peak["Time"]))
        if rt_diff > rt_tolerance:
            return False
        ref_area = float(ref_peak["Area"])
        new_area = float(new_peak["Area"])
        denom = max(abs(ref_area), 1e-9)
        if abs(ref_area - new_area) / denom > area_tolerance:
            return False
    return True


def build_detector_cycles(
    injections: List[Tuple[str, str]],
    detector_key: str,
) -> Tuple[List[List[dict]], List[str], int]:
    """
    TCD/FID Report 에서 같은 실험 주입만 모음 (RT + Area 허용, 피크 개수 가변).

    Returns:
        (cycles, matched_injection_paths, skipped_mismatch_count)
    """
    cycles: List[List[dict]] = []
    matched_paths: List[str] = []
    reference: Optional[List[dict]] = None
    skipped = 0

    for injection_path, _sequence_path in injections:
        reports = parse_injection_reports(injection_path)
        peaks = reports.get(detector_key, [])
        label = os.path.basename(injection_path)
        if not peaks:
            continue

        if reference is None:
            reference = peaks
            cycles.append(peaks)
            matched_paths.append(injection_path)
            print(f"[진행] {label} {detector_key}: 피크 {len(peaks)}개 (기준)")
            continue

        if cycles_match(reference, peaks):
            cycles.append(peaks)
            matched_paths.append(injection_path)
            print(f"[진행] {label} {detector_key}: 피크 {len(peaks)}개")
        else:
            skipped += 1
            print(
                f"[건너뜀] {label} {detector_key}: 패턴 불일치 "
                f"({len(peaks)}피크 vs 기준 {len(reference)}피크)"
            )

    if skipped:
        print(f"[안내] {detector_key} — 다른 실험으로 판단해 {skipped}주입 제외")

    if len(cycles) >= 2:
        first_label = os.path.basename(matched_paths[0]) if matched_paths else None
        cycles, skipped_first, _ = drop_first_cycle_if_startup_noise(
            cycles,
            first_injection_label=first_label,
        )
        if skipped_first and matched_paths:
            matched_paths = matched_paths[1:]

    return cycles, matched_paths, skipped


def build_merged_injection_cycles(
    sample_folder: str,
) -> Tuple[List[List[dict]], List[List[dict]], List[str], int]:
    """
    시료 폴더 아래 모든 시퀀스·주입에서 FID/TCD 사이클 수집.

    TCD 패턴으로 같은 실험 여부를 판별하고, 통과한 주입만 FID/TCD 각각 적재.
    """
    injections = collect_reported_injections(sample_folder)
    if not injections:
        return [], [], [], 0

    print(f"[안내] Report 있는 주입 {len(injections)}개 (시퀀스 {len(find_sequence_folders(sample_folder))}개)")

    tcd_cycles, matched_paths, skipped = build_detector_cycles(injections, "TCD")
    if not tcd_cycles:
        fid_cycles, matched_paths, skipped = build_detector_cycles(injections, "FID")
        return fid_cycles, [], matched_paths, skipped

    matched_set = set(matched_paths)
    fid_cycles: List[List[dict]] = []
    for injection_path, _ in injections:
        if injection_path not in matched_set:
            continue
        reports = parse_injection_reports(injection_path)
        fid_peaks = reports.get("FID", [])
        label = os.path.basename(injection_path)
        if fid_peaks:
            fid_cycles.append(fid_peaks)
            print(f"[진행] {label} FID: 피크 {len(fid_peaks)}개")
        else:
            print(f"[경고] {label} FID: Report 있으나 FID 피크 없음")

    matched_labels = [os.path.basename(path) for path in matched_paths]
    return fid_cycles, tcd_cycles, matched_labels, skipped
