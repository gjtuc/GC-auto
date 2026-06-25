# -*- coding: utf-8 -*-
"""
gc_chem32.py — Chem32 / GC7890 (GC3) Data 경로·Report 파싱

=============================================================================
[어느 PC / GC]
=============================================================================

  **GC3 장비 PC (차헌) 전용.** env: GC_INSTANCE=gc3, CHEMSTATION_MODE=chem32.
  계산·Origin은 **차헌 PC** (Desktop\\.cursor). 본 PC는 gc_automation.py 만.

GC3 폴더 구조:
  DATA / {시료 폴더} / {REACTION 시퀀스} / 001F0101.D·002F0201.D … / Report.TXT

피크 개수는 가변 — FID·TCD 각각 Report 에 있는 만큼만 사용.
출력·메일 흐름은 GC2와 동일 (Desktop\\KCH).

[병합 규칙 — gc_chem32.build_merged_injection_cycles]
  · 1주입 = FID+TCD 1쌍 (둘 다 Report 에 피크 있을 때만)
  · 진행 중 주입: 폴더만 있고 Report 없음 → 제외 (다음 watch 에 포함)
  · TCD sliding match: 직전 주입 대비 RT·Area (DRM 장주기 drift 대응)
  · Area% 과학적 표기(1.000e2) 파싱 지원

[시료 폴더 선택 — find_active_sample_folder]
  1) DATA 아래 시료 폴더(시퀀스 하위 폴더 보유) 전부 스캔
  2) 각 시료의 **최신 시퀀스 실행 시각** = 시퀀스 폴더명 끝 YYYY-MM-DD HH-MM-SS
     (20260608, REACTION, TCD-FID 등 방법명 접두는 무시)
  3) 그 시각이 가장 늦은 시료 폴더 1개 선택 (동률 시 Report mtime → 폴더 mtime)
  4) 선택된 시료 안 모든 시퀀스를 시각순 병합 → 엑셀 1개 + 메일

[분석 중단 구간 — detect_analysis_gaps]
  · 주입 Report.TXT 의 **Injection Date** (실제 주입 시각) 사용 — 파일 mtime 아님
  · 연속 주입 사이 공백만 검사 (시퀀스 폴더 경계와 무관)
  · 주입 Report 시각 간 중앙값 = 사이클 1회 소요 시간(추정)
  · floor(공백 / 추정간격) = 미수집 사이클, 나머지 분·초는 버림

[엑셀 갭 행 — gap_marker_cycle / insert_analysis_gap_markers]
  · 메일 본문 + FID/TCD 시트 모두에 공백 표시 (차헌 PC는 **엑셀만** 읽음)
  · `#`=중단, Time=약 N사이클 미수집, Symmetry=GC_GAP:N=N → data_pc/gc_gap_contract.py
  · Area=공백 기간·폴더명(002F0209→001F0101)은 사람용; 차헌 PC 파서는 Time/Symmetry 만 사용
  · 갭 인덱스는 collect_reported_injections(전체 Report) 기준 — 엑셀은 sliding 통과분만
    있으므로 _gap_marker_excel_position 으로 “마지막 실측 주입” 뒤에 삽입 (002F FID 미완료 등)
  · 검증: scripts/verify_cheon_pc_gap.py (촉매 반응 계산.parse_gc_sheet E2E)
"""

from __future__ import annotations

import csv
import glob
import os
import re
import statistics
from dataclasses import dataclass
from datetime import datetime
from itertools import groupby
from typing import Dict, List, Optional, Tuple

from gc_config import AREA_MATCH_TOLERANCE, RT_TOLERANCE
from gc_chemstation import drop_first_cycle_if_startup_noise

REACTION_DT = re.compile(
    r"REACTION\s+(\d{4})-(\d{2})-(\d{2})\s+(\d{2})-(\d{2})-(\d{2})",
    re.IGNORECASE,
)
# 시퀀스 폴더명 끝의 실행 시각 — 방법명 접두(20260608, TCD-FID 등) 무시
SEQUENCE_TRAILING_DT = re.compile(
    r"(\d{4})-(\d{2})-(\d{2})\s+(\d{2})-(\d{2})-(\d{2})\s*$",
)
CHEM32_INJECTION_RE = re.compile(r"^(\d{3})F(\d+)\.D$", re.IGNORECASE)
SAMPLE_FOLDER_DATE_RE = re.compile(r"^(\d{8})\s+(.+)$")
SAMPLE_FOLDER_YYMMDD_RE = re.compile(r"^(\d{6})_(.+)$")
REPORT_PEAK_LINE = re.compile(
    r"^\s*(\d+)\s+([\d.]+)\s+(\S+)\s+([\d.]+)\s+([\d.eE+-]+)\s+([\d.eE+-]+)\s+([\d.eE+-]+)\s*$"
)
INJECTION_DATE_LINE = re.compile(
    r"^Injection Date\s*:\s*(.+?)(?:\s+Inj\s*:|$)",
    re.IGNORECASE,
)
INJECTION_DATE_FORMATS = (
    "%m/%d/%Y %I:%M:%S %p",
    "%m/%d/%Y %H:%M:%S",
    "%d/%m/%Y %I:%M:%S %p",
    "%d/%m/%Y %H:%M:%S",
    "%Y-%m-%d %H:%M:%S",
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


def parse_sequence_datetime(sequence_path: str) -> Optional[datetime]:
    """시퀀스 폴더명 끝 YYYY-MM-DD HH-MM-SS → datetime (방법명 접두 무시)."""
    match = SEQUENCE_TRAILING_DT.search(os.path.basename(sequence_path))
    if not match:
        return None
    y, mo, d, h, mi, s = map(int, match.groups())
    return datetime(y, mo, d, h, mi, s)


def get_latest_sequence_datetime(sample_folder: str) -> Optional[datetime]:
    """시료 폴더 안 시퀀스 중 가장 늦은 실행 시각."""
    latest: Optional[datetime] = None
    for sequence_path in find_sequence_folders(sample_folder):
        dt = parse_sequence_datetime(sequence_path)
        if dt is None:
            try:
                dt = datetime.fromtimestamp(os.path.getmtime(sequence_path))
            except OSError:
                continue
        if latest is None or dt > latest:
            latest = dt
    return latest


def _sample_rank_key(sample_path: str) -> Tuple[datetime, float, float]:
    """시료 폴더 우선순위: 최신 시퀀스 시각 → Report mtime → 폴더 mtime."""
    seq_dt = get_latest_sequence_datetime(sample_path) or datetime.min
    report_mtime = get_latest_report_mtime(sample_path) or 0.0
    try:
        folder_mtime = os.path.getmtime(sample_path)
    except OSError:
        folder_mtime = 0.0
    return (seq_dt, report_mtime, folder_mtime)


def find_sample_folders(data_path: str) -> List[str]:
    folders = []
    try:
        for entry in os.scandir(data_path):
            if entry.is_dir() and _folder_contains_reaction_sequences(entry.path):
                folders.append(entry.path)
    except OSError:
        return []
    return sorted(folders, key=_sample_rank_key, reverse=True)


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
        latest = get_latest_sequence_datetime(chosen)
        when = latest.strftime("%Y-%m-%d %H:%M:%S") if latest else "시퀀스 시각 없음"
        print(
            f"[안내] Chem32 시료 폴더 자동 선택: {chosen}\n"
            f"       (DATA 내 {len(samples)}개 시료 중 최신 시퀀스 {when})"
        )
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
    dt = parse_sequence_datetime(sequence_path)
    if dt is not None:
        return dt
    return datetime.fromtimestamp(os.path.getmtime(sequence_path))


def _parse_injection_folder_name(folder_name: str) -> Optional[Tuple[int, int]]:
    """001F0199.D → (1, 199), 002F0201.D → (2, 201) — 시퀀스 줄 번호 롤오버."""
    match = CHEM32_INJECTION_RE.match(folder_name)
    if not match:
        return None
    return int(match.group(1)), int(match.group(2))


def find_chem32_injection_folders(sequence_folder: str) -> List[str]:
    injections = []
    try:
        for entry in os.scandir(sequence_folder):
            if entry.is_dir() and CHEM32_INJECTION_RE.match(entry.name):
                injections.append(entry.path)
    except OSError:
        return []
    return sorted(injections, key=_injection_sort_key)


def _injection_sort_key(injection_path: str) -> Tuple[int, int, float]:
    name = os.path.basename(injection_path)
    parsed = _parse_injection_folder_name(name)
    if parsed:
        batch, number = parsed
        return (batch, number, os.path.getmtime(injection_path))
    return (0, 0, os.path.getmtime(injection_path))


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
    """시퀀스 최초 실행일 YYYYMMDD — 시퀀스 폴더명 끝 날짜 중 가장 이른 값."""
    earliest = None
    for sequence_path in find_sequence_folders(sample_folder):
        dt = parse_sequence_datetime(sequence_path)
        if dt is None:
            continue
        day = datetime(dt.year, dt.month, dt.day)
        if earliest is None or day < earliest:
            earliest = day
    if earliest:
        return earliest.strftime("%Y%m%d")
    folder_name = os.path.basename(sample_folder)
    head = re.match(r"^(\d{8})", folder_name)
    if head:
        return head.group(1)
    yymmdd = SAMPLE_FOLDER_YYMMDD_RE.match(folder_name)
    if yymmdd:
        yy = int(yymmdd.group(1)[:2])
        century = 2000 if yy < 80 else 1900
        return f"{century + yy}{yymmdd.group(1)[2:]}"
    return datetime.fromtimestamp(os.path.getmtime(sample_folder)).strftime("%Y%m%d")


def default_sample_name_from_folder(sample_folder: str) -> str:
    name = os.path.basename(sample_folder)
    match = SAMPLE_FOLDER_DATE_RE.match(name)
    if match:
        return match.group(2).strip()
    yymmdd = SAMPLE_FOLDER_YYMMDD_RE.match(name)
    if yymmdd:
        return yymmdd.group(2).strip()
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


def injection_report_complete(reports: Dict[str, List[dict]]) -> bool:
    """완료된 분석 — FID·TCD 피크가 Report 에 모두 있어야 함 (1주입 = 1쌍)."""
    return bool(reports.get("FID")) and bool(reports.get("TCD"))


def _log_in_progress_injections(sample_folder: str) -> None:
    """GC 가 아직 Report 를 쓰는 중인 주입 — 폴더만 있고 Report 없음."""
    for sequence_path in find_sequence_folders(sample_folder):
        for injection_path in find_chem32_injection_folders(sequence_path):
            if find_report_txt(injection_path):
                continue
            label = os.path.basename(injection_path)
            seq_name = os.path.basename(sequence_path)
            print(
                f"[진행중] {label} ({seq_name}): 폴더만 있음 — "
                "GC 생성 중, Report 미작성 (다음 watch 에 포함)"
            )


def _filter_complete_injection_pairs(
    injections: List[Tuple[str, str]],
) -> Tuple[List[Tuple[str, str]], int]:
    """Report 파일은 있으나 FID/TCD 중 하나만 있는 미완료 주입 제외."""
    complete: List[Tuple[str, str]] = []
    skipped = 0
    for injection_path, sequence_path in injections:
        reports = parse_injection_reports(injection_path)
        label = os.path.basename(injection_path)
        if injection_report_complete(reports):
            complete.append((injection_path, sequence_path))
            continue
        skipped += 1
        fid_n = len(reports.get("FID", []))
        tcd_n = len(reports.get("TCD", []))
        print(
            f"[건너뜀] {label}: Report 미완료 "
            f"(FID {fid_n}피크 / TCD {tcd_n}피크 — 완료 후 재처리)"
        )
    return complete, skipped


def collect_reported_injections(sample_folder: str) -> List[Tuple[str, str]]:
    """(injection_path, sequence_path) — Report 있는 주입만, 시간순."""
    collected = []
    for sequence_path in find_sequence_folders(sample_folder):
        for injection_path in find_chem32_injection_folders(sequence_path):
            if find_report_txt(injection_path):
                collected.append((injection_path, sequence_path))
    collected.sort(
        key=lambda item: (
            _sequence_sort_key(item[1]),
            _injection_sort_key(item[0]),
        )
    )
    return collected


@dataclass(frozen=True)
class AnalysisGap:
    """연속 주입 사이 분석 중단 — floor(공백/간격) 만큼 사이클 미수집 추정."""

    after_injection_index: int
    before_injection_index: int
    after_sequence: str
    before_sequence: str
    gap_sec: float
    interval_sec: float
    missing_cycles: int
    remainder_sec: float
    after_last_at: datetime
    before_first_at: datetime


def analysis_gaps_email_lines(
    gaps: List[AnalysisGap],
    interval_sec: Optional[float],
    injections: Optional[List[Tuple[str, str]]] = None,
) -> List[str]:
    """메일 본문용 분석 중단 구간 요약 (주입 번호·폴더명 선택)."""
    if interval_sec is None:
        return []
    lines = [
        "",
        f"[분석 중단] 사이클 간격 추정(중앙값): {format_duration_korean(interval_sec)}",
        "  (Report.TXT Injection Date 기준, 연속 주입 사이 2사이클 이상 공백)",
    ]
    if not gaps:
        lines.append("  시퀀스 간 긴 공백(미수집 사이클) 없음")
        return lines
    total = sum(gap.missing_cycles for gap in gaps)
    lines.append(
        f"  추정 미수집 사이클 합계: 약 {total}개 "
        "(공백÷간격 floor, 나머지 분·초는 버림)"
    )
    for index, gap in enumerate(gaps, start=1):
        inj_note = ""
        if injections:
            try:
                after_folder = os.path.basename(injections[gap.after_injection_index][0])
                before_folder = os.path.basename(injections[gap.before_injection_index][0])
                inj_note = (
                    f"  [#{gap.after_injection_index + 1} {after_folder} → "
                    f"#{gap.before_injection_index + 1} {before_folder}]"
                )
            except (IndexError, TypeError):
                pass
        lines.append(
            f"  {index}. {gap.after_last_at.strftime('%m-%d %H:%M')} → "
            f"{gap.before_first_at.strftime('%m-%d %H:%M')}  "
            f"공백 {format_duration_korean(gap.gap_sec)} → "
            f"약 {gap.missing_cycles}사이클 "
            f"(잔여 {format_duration_korean(gap.remainder_sec)} 버림)"
            + (f"\n     {inj_note.strip()}" if inj_note else "")
        )
    return lines


def format_duration_korean(sec: float) -> str:
    """초 → 'N시간 M분 S초' (0이 아닌 단위만)."""
    total = max(0, int(round(sec)))
    hours, rem = divmod(total, 3600)
    minutes, seconds = divmod(rem, 60)
    parts: List[str] = []
    if hours:
        parts.append(f"{hours}시간")
    if minutes:
        parts.append(f"{minutes}분")
    if seconds or not parts:
        parts.append(f"{seconds}초")
    return " ".join(parts)


def estimate_missing_cycles_floor(gap_sec: float, interval_sec: float) -> Tuple[int, float]:
    """
    나눗셈 여몫 버림 — floor(공백/간격) = 미수집 사이클, 나머지 초는 오차로 폐기.

    예: 3시간 15분 / 58분 23초 → 3사이클, 잔여 약 19분
    """
    if interval_sec <= 0 or gap_sec <= 0:
        return 0, max(0.0, gap_sec)
    missing = int(gap_sec // interval_sec)
    remainder = gap_sec - missing * interval_sec
    return missing, remainder


def parse_report_injection_datetime(report_path: str) -> Optional[datetime]:
    """Report.TXT 헤더 Injection Date → 실제 주입 시각 (Chem32 표준)."""
    try:
        with _open_chem32_text(report_path) as report_file:
            for line in report_file:
                match = INJECTION_DATE_LINE.match(line.strip())
                if not match:
                    continue
                raw = match.group(1).strip()
                for fmt in INJECTION_DATE_FORMATS:
                    try:
                        return datetime.strptime(raw, fmt)
                    except ValueError:
                        continue
    except OSError:
        return None
    return None


def _injection_analysis_timestamp(injection_path: str) -> Optional[float]:
    """주입 시각(초) — Injection Date 우선, 없으면 Report mtime."""
    report_path = find_report_txt(injection_path)
    if not report_path:
        return None
    injected = parse_report_injection_datetime(report_path)
    if injected is not None:
        return injected.timestamp()
    try:
        return os.path.getmtime(report_path)
    except OSError:
        return None


def _injection_report_mtime(injection_path: str) -> Optional[float]:
    report_path = find_report_txt(injection_path)
    if not report_path:
        return None
    try:
        return os.path.getmtime(report_path)
    except OSError:
        return None


def median_injection_interval_sec(
    injections: List[Tuple[str, str]],
    *,
    min_delta_sec: float = 60.0,
) -> Optional[float]:
    """연속 주입 Injection Date 차이의 중앙값(초) — 사이클 1회 소요 추정."""
    times: List[float] = []
    for injection_path, _sequence_path in injections:
        stamp = _injection_analysis_timestamp(injection_path)
        if stamp is not None:
            times.append(stamp)
    times.sort()
    deltas = [
        times[index] - times[index - 1]
        for index in range(1, len(times))
        if times[index] > times[index - 1] and (times[index] - times[index - 1]) >= min_delta_sec
    ]
    if not deltas:
        return None
    return float(statistics.median(deltas))


def detect_analysis_gaps(sample_folder: str) -> Tuple[List[AnalysisGap], Optional[float]]:
    """
    연속 주입 사이 긴 공백 → floor 나눗셈으로 미수집 사이클 수 추정.

    시퀀스 폴더가 바뀌어도, 실제 마지막·다음 주입 시각(Injection Date)만 본다.

    Returns:
        (gaps, median_interval_sec)
    """
    injections = collect_reported_injections(sample_folder)
    interval_sec = median_injection_interval_sec(injections)
    if not interval_sec or len(injections) < 2:
        return [], interval_sec

    timed: List[Tuple[int, str, str, float]] = []
    for index, (injection_path, sequence_path) in enumerate(injections):
        stamp = _injection_analysis_timestamp(injection_path)
        if stamp is not None:
            timed.append((index, injection_path, sequence_path, stamp))

    gaps: List[AnalysisGap] = []
    for pos in range(1, len(timed)):
        prev_index, prev_path, prev_seq, prev_stamp = timed[pos - 1]
        curr_index, curr_path, curr_seq, curr_stamp = timed[pos]
        gap_sec = curr_stamp - prev_stamp
        if gap_sec <= 0:
            continue
        missing, remainder = estimate_missing_cycles_floor(gap_sec, interval_sec)
        # 정상 주입 간격(≈1사이클)은 제외 — 2사이클 이상 비었을 때만 분석 중단
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


def sequence_folder_of_injection(injection_path: str) -> str:
    """001F0101.D 주입 폴더 경로 → REACTION 시퀀스 폴더 basename."""
    return os.path.basename(os.path.dirname(injection_path))


def gap_marker_cycle(
    gap: AnalysisGap,
    *,
    after_folder: str = "",
    before_folder: str = "",
) -> List[dict]:
    """
    엑셀 1주입 자리 — 분석 중단·미수집 사이클 표시 행 (FID/TCD 시트 공통 1행).

    차헌 PC 계약 (data_pc/gc_gap_contract.py):
      · 머신 파싱: Time ``약 {N}사이클 미수집`` 또는 Symmetry ``GC_GAP:N={N}``
      · parse_gc_sheet 가 N칸 Cycle 을 비우고 Origin 열 정렬
    Area 의 ``· 폴더A→폴더B`` 는 표시 전용 — 파서는 무시.
    """
    n = gap.missing_cycles
    where = ""
    if after_folder and before_folder:
        where = f" · {after_folder}→{before_folder}"
    return [
        {
            "#": "중단",
            "Time": f"약 {n}사이클 미수집",
            "Area": f"공백 {format_duration_korean(gap.gap_sec)}{where}",
            "Height": f"잔여 {format_duration_korean(gap.remainder_sec)} 버림",
            "Width": gap.after_last_at.strftime("%m-%d %H:%M"),
            "Area%": gap.before_first_at.strftime("%m-%d %H:%M"),
            "Symmetry": f"GC_GAP:N={n}",
        }
    ]


def _gap_marker_excel_position(
    gap: AnalysisGap,
    matched_injection_paths: List[str],
    all_injections: List[Tuple[str, str]],
) -> Optional[int]:
    """
    갭 행을 넣을 엑셀 주입 목록 인덱스.

  gap.after_injection_index 는 collect_reported_injections 기준이고,
  엑셀에는 sliding·미완료 필터를 통과한 주입만 있으므로, 갭 직전까지
  실측에 포함된 마지막 주입 뒤에 삽입한다.
    """
    path_to_all_index = {path: index for index, (path, _) in enumerate(all_injections)}
    insert_pos = 0
    matched_before_gap = False
    for excel_pos, matched_path in enumerate(matched_injection_paths):
        all_index = path_to_all_index.get(matched_path)
        if all_index is None or all_index > gap.after_injection_index:
            continue
        insert_pos = excel_pos + 1
        matched_before_gap = True
    if not matched_before_gap:
        return 0
    return insert_pos


def insert_analysis_gap_markers(
    fid_cycles: List[List[dict]],
    tcd_cycles: List[List[dict]],
    matched_injection_paths: List[str],
    analysis_gaps: List[AnalysisGap],
    all_injections: Optional[List[Tuple[str, str]]] = None,
) -> Tuple[List[List[dict]], List[List[dict]]]:
    """
    연속 주입 사이 공백을 엑셀 주입 목록에 ``중단`` 표시 행으로 삽입.

    all_injections: collect_reported_injections() — 갭 #번호·메일과 동일 기준.
    matched_*: build_merged_injection_cycles() 통과분만 (002F FID 미완료 등은 여기 없음).

    예: 실측 … Cycle99 → [중단 2사이클] → 실측 Cycle102 …
    """
    if not analysis_gaps or not matched_injection_paths:
        return fid_cycles, tcd_cycles
    if len(fid_cycles) != len(tcd_cycles) != len(matched_injection_paths):
        raise ValueError("FID/TCD/경로 개수 불일치")

    if all_injections is None:
        all_injections = [(path, "") for path in matched_injection_paths]

    fid_out = list(fid_cycles)
    tcd_out = list(tcd_cycles)
    pending: List[Tuple[int, List[dict]]] = []
    for gap in analysis_gaps:
        pos = _gap_marker_excel_position(gap, matched_injection_paths, all_injections)
        if pos is None or pos < 0 or pos > len(fid_out):
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
        pending.append((pos, marker))
        print(
            f"[안내] 엑셀 갭 행 삽입 위치 #{pos + 1} — "
            f"약 {gap.missing_cycles}사이클 미수집 "
            f"({after_folder}→{before_folder})"
        )

    for pos, marker in sorted(pending, key=lambda item: item[0], reverse=True):
        fid_out.insert(pos, marker)
        tcd_out.insert(pos, marker)
    return fid_out, tcd_out


def log_analysis_gaps(gaps: List[AnalysisGap], interval_sec: Optional[float]) -> None:
    """분석 중단 구간 — 콘솔 안내."""
    if not interval_sec:
        return
    print(
        f"[안내] 사이클 간격 추정(중앙값): {format_duration_korean(interval_sec)} "
        f"({interval_sec:.0f}초)"
    )
    if not gaps:
        print("[안내] 시퀀스 간 긴 분석 중단(미수집 사이클) 없음")
        return
    total_missing = sum(gap.missing_cycles for gap in gaps)
    print(f"[안내] 분석 중단 구간 {len(gaps)}곳 — 추정 미수집 사이클 합계 {total_missing}개")
    for index, gap in enumerate(gaps, start=1):
        print(
            f"  ({index}) {gap.after_last_at.strftime('%m-%d %H:%M')} → "
            f"{gap.before_first_at.strftime('%m-%d %H:%M')}  "
            f"공백 {format_duration_korean(gap.gap_sec)}  "
            f"→ 약 {gap.missing_cycles}사이클 미수집 "
            f"(잔여 {format_duration_korean(gap.remainder_sec)} 버림)"
        )


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


def describe_cycle_mismatch(
    reference: List[dict],
    candidate: List[dict],
    rt_tolerance: float = RT_TOLERANCE,
    area_tolerance: float = AREA_MATCH_TOLERANCE,
) -> str:
    """불일치 사유 — 검증 로그용."""
    if not reference or not candidate:
        return "피크 없음"
    if len(reference) != len(candidate):
        return f"피크 수 {len(candidate)} vs 직전 {len(reference)}"
    worst_rt = 0.0
    worst_area = 0.0
    worst_peak = 0
    for index, (ref_peak, new_peak) in enumerate(zip(reference, candidate), start=1):
        rt_diff = abs(float(ref_peak["Time"]) - float(new_peak["Time"]))
        ref_area = float(ref_peak["Area"])
        new_area = float(new_peak["Area"])
        area_diff = abs(ref_area - new_area) / max(abs(ref_area), 1e-9)
        if rt_diff > worst_rt:
            worst_rt = rt_diff
        if area_diff > worst_area:
            worst_area = area_diff
            worst_peak = index
    if worst_rt > rt_tolerance:
        return f"RT 불일치 피크#{worst_peak} Δ{worst_rt:.3f}min (허용 {rt_tolerance})"
    if worst_area > area_tolerance:
        return (
            f"Area 불일치 피크#{worst_peak} "
            f"{worst_area * 100:.1f}% (허용 {area_tolerance * 100:.0f}%, 직전 주입 대비)"
        )
    return "불일치"


def _resolve_reference_index(
    peaks_list: List[List[dict]],
    labels: List[str],
    detector_key: str,
) -> int:
    """첫 주입이 startup(피크 수·패턴 다름)이면 2주입 또는 다수 패턴으로 기준 이동."""
    if not peaks_list:
        return 0
    if len(peaks_list) == 1:
        return 0
    if cycles_match(peaks_list[0], peaks_list[1]):
        return 0
    if len(peaks_list) >= 3 and cycles_match(peaks_list[1], peaks_list[2]):
        print(
            f"[안내] startup 노이즈 — {labels[0]} 제외, "
            f"{labels[1]} 부터 {detector_key} 기준"
        )
        return 1
    from collections import Counter

    mode_count = Counter(len(peaks) for peaks in peaks_list).most_common(1)[0][0]
    for index, peaks in enumerate(peaks_list):
        if len(peaks) == mode_count:
            if index > 0:
                print(
                    f"[안내] {labels[0]}~{labels[index - 1]} 제외 — "
                    f"피크 {mode_count}개 패턴 기준 ({labels[index]}, {detector_key})"
                )
            return index
    return 0


def _build_detector_cycles_chunk(
    injections: List[Tuple[str, str]],
    detector_key: str,
) -> Tuple[List[List[dict]], List[str], int]:
    """
    단일 REACTION 시퀀스 안에서 detector 사이클 수집.

    startup 제외 후 **직전 주입(sliding)** 과 RT·Area 비교 — DRM 장시간 반응에서
    초기 주입 대비 누적 Area drift 로 중간부터 잘리는 문제 방지.
    """
    collected: List[Tuple[str, List[dict], str]] = []
    for injection_path, _sequence_path in injections:
        reports = parse_injection_reports(injection_path)
        peaks = reports.get(detector_key, [])
        if not peaks:
            continue
        collected.append((injection_path, peaks, os.path.basename(injection_path)))

    if not collected:
        return [], [], 0

    peaks_only = [item[1] for item in collected]
    labels = [item[2] for item in collected]
    ref_index = _resolve_reference_index(peaks_only, labels, detector_key)

    cycles: List[List[dict]] = []
    matched_paths: List[str] = []
    skipped = 0
    chain_ref: Optional[List[dict]] = None

    for index, (injection_path, peaks, label) in enumerate(collected):
        if index < ref_index:
            skipped += 1
            print(
                f"[건너뜀] {label} {detector_key}: startup/기준 전 주입 "
                f"({len(peaks)}피크)"
            )
            continue
        if index == ref_index:
            cycles.append(peaks)
            matched_paths.append(injection_path)
            chain_ref = peaks
            print(f"[진행] {label} {detector_key}: 피크 {len(peaks)}개 (기준)")
            continue
        assert chain_ref is not None
        if len(peaks) != len(chain_ref):
            skipped += 1
            print(
                f"[건너뜀] {label} {detector_key}: 피크 수 변경 "
                f"({len(peaks)} vs 직전 {len(chain_ref)})"
            )
            continue
        if cycles_match(chain_ref, peaks):
            cycles.append(peaks)
            matched_paths.append(injection_path)
            chain_ref = peaks
            print(f"[진행] {label} {detector_key}: 피크 {len(peaks)}개")
        else:
            skipped += 1
            reason = describe_cycle_mismatch(chain_ref, peaks)
            print(f"[건너뜀] {label} {detector_key}: {reason}")

    if skipped:
        print(f"[안내] {detector_key} — startup·패턴 불일치로 {skipped}주입 제외")

    if len(cycles) >= 2:
        first_label = os.path.basename(matched_paths[0]) if matched_paths else None
        cycles, skipped_first, _ = drop_first_cycle_if_startup_noise(
            cycles,
            first_injection_label=first_label,
        )
        if skipped_first and matched_paths:
            matched_paths = matched_paths[1:]
            skipped += 1

    return cycles, matched_paths, skipped


def build_detector_cycles(
    injections: List[Tuple[str, str]],
    detector_key: str,
) -> Tuple[List[List[dict]], List[str], int]:
    """
    TCD/FID Report 에서 같은 실험 주입만 모음 (시퀀스별 sliding RT+Area).

    Returns:
        (cycles, matched_injection_paths, skipped_mismatch_count)
    """
    from itertools import groupby

    cycles: List[List[dict]] = []
    matched_paths: List[str] = []
    skipped = 0
    for _sequence_path, group in groupby(injections, key=lambda item: item[1]):
        chunk_cycles, chunk_paths, chunk_skipped = _build_detector_cycles_chunk(
            list(group),
            detector_key,
        )
        cycles.extend(chunk_cycles)
        matched_paths.extend(chunk_paths)
        skipped += chunk_skipped
    return cycles, matched_paths, skipped


def build_merged_injection_cycles(
    sample_folder: str,
) -> Tuple[List[List[dict]], List[List[dict]], List[str], int]:
    """
    시료 폴더 아래 모든 시퀀스·주입에서 FID/TCD 사이클 수집.

    완료된 주입(FID+TCD 모두 Report 에 있음)만 TCD sliding 으로 선별하고,
    동일 주입에서 FID/TCD 를 1:1 쌍으로 엑셀에 적재.
    """
    _log_in_progress_injections(sample_folder)
    injections = collect_reported_injections(sample_folder)
    if not injections:
        return [], [], [], 0, []

    print(f"[안내] Report 있는 주입 {len(injections)}개 (시퀀스 {len(find_sequence_folders(sample_folder))}개)")

    analysis_gaps, _interval = detect_analysis_gaps(sample_folder)
    log_analysis_gaps(analysis_gaps, _interval)

    complete_injections, incomplete_skipped = _filter_complete_injection_pairs(injections)
    if not complete_injections:
        return [], [], [], incomplete_skipped, []

    tcd_cycles, matched_paths, skipped = build_detector_cycles(complete_injections, "TCD")
    skipped += incomplete_skipped
    if not tcd_cycles:
        fid_cycles, matched_paths, skipped_fid = build_detector_cycles(complete_injections, "FID")
        skipped += skipped_fid
        return fid_cycles, [], matched_paths, skipped, matched_paths

    fid_cycles: List[List[dict]] = []
    for injection_path in matched_paths:
        reports = parse_injection_reports(injection_path)
        fid_peaks = reports.get("FID", [])
        label = os.path.basename(injection_path)
        if not fid_peaks:
            raise RuntimeError(
                f"내부 오류: TCD 통과 주입 {label} 에 FID 없음 — complete 필터 버그"
            )
        fid_cycles.append(fid_peaks)
        print(f"[진행] {label} FID: 피크 {len(fid_peaks)}개")

    if len(fid_cycles) != len(tcd_cycles):
        raise RuntimeError(
            f"FID/TCD 사이클 수 불일치: FID {len(fid_cycles)} vs TCD {len(tcd_cycles)}"
        )

    matched_labels = [os.path.basename(path) for path in matched_paths]
    return fid_cycles, tcd_cycles, matched_labels, skipped, matched_paths
