# -*- coding: utf-8 -*-
"""
gc_gc1.py — GC1 YL6500GC PDF 보고서 파싱 · 엑셀 · trim · 정리

=============================================================================
[데이터 소스 — GC1 vs GC2/GC3]
=============================================================================

  GC2/GC3: ChemStation injection 폴더의 .D / .ch / acam / Report
  GC1:     Autochro 가 만든 **PDF** (주입당 보통 3페이지)

  **GC1 장비 PC (은규) 전용.** 계산·Origin → **은규 PC** (data_pc/촉매 반응 계산.py)

    페이지 1 — YL6500GC A (FID)  → CH4, C2H6, C2H4
    페이지 2 — YL6500GC B (크로마만, 피크 표 없음 — 마지막 주입 완료 판별용)
    페이지 3 — YL6500GC C (TCD)  → H2, CO, CO2

  PDF 텍스트는 PyMuPDF(fitz)로 추출. 피크 **이름이 비어 있어도** RT·Area 로 파싱.

=============================================================================
[피크 표 overflow 페이지]
=============================================================================

  환원 등 피크가 많으면 C 채널 적분 표가 **다음 페이지**로 이어집니다.
  overflow 페이지에는 채널 헤더·「분석 보고서」가 없고 피크 번호만 이어짐.

  parse_peak_table_continuation() + _merge_peak_continuation_pages() 로
  직전 채널 페이지와 **같은 수집 채널**로 병합합니다. (CO/CO2 누락 방지)

=============================================================================
[주입 → 엑셀 행 — trim 파이프라인]
=============================================================================

  parse_gc1_pdf_path()
    → _collect_gc1_cycles_from_pages()  FID/TCD 주입별 피크
    → maybe_drop_last_incomplete_gc1_cycle()  마지막 주입 B 채널 전압선 길이
    → trim_reduction_and_first_reaction()  GC1 비즈니스 규칙

  trim 규칙 (H2 area 기준, env 로 임계값 조정):
    · 사전 노이즈 제거
    · 환원 구간 제거 (GC1 환원은 엑셀에 넣지 않음)
    · 전환(환원→반응 사이) 1주입 제거
    · **첫 반응 1주입 포함** — GC1 전용 (GC2/GC3 는 첫 반응 제외 규칙 유지)

  마지막 주입 incomplete:
    · 항상 제거하지 않음. YL6500GC B 페이지 벡터에서 **전압선 x축 끝(분)** 측정.
    · GC1_LAST_CYCLE_MIN_SCAN_MIN(기본 18분) 미만이면 A/B/C 3페이지 분 drop.

=============================================================================
[파일 정리 cleanup_superseded_gc1_files]
=============================================================================

  · 잘못된 stem (임시 pdf, 옛 템플릿명, Autochro 제목 파싱 오류로 잘린 이름)
  · 같은 실험·반응 fingerprint 인데 주입 수 적은 PDF → 많은 쪽 유지
  · 삭제 PDF 에 대응하는 구식 xlsx 도 삭제

=============================================================================
[엑셀 형식]
=============================================================================

  GC2 Width 열 대신 **「분석된 원소」** 열에 CH4/H2 등 기록. FID·TCD 2시트.

관련: gc_autochro.py (PDF 생성), gc_pipeline.run_processing_gc1(), gc_watch (GC1 분기)
"""

from __future__ import annotations

import glob
import os
import re
import time
from dataclasses import dataclass
from datetime import datetime
from typing import Dict, List, Optional, Tuple

from gc_config import CHEM32_FID_SHEET, CHEM32_TCD_SHEET

try:
    import fitz  # PyMuPDF
except ImportError:
    fitz = None

CHANNEL_A = "YL6500GC A"
CHANNEL_B = "YL6500GC B"
CHANNEL_C = "YL6500GC C"

DEFAULT_FID_WINDOWS: Tuple[Tuple[str, float, float], ...] = (
    ("CH4", 1.4, 0.35),
    ("C2H6", 1.9, 0.35),
    ("C2H4", 2.3, 0.35),
)
DEFAULT_TCD_WINDOWS: Tuple[Tuple[str, float, float], ...] = (
    ("H2", 2.0, 0.35),
    ("CO", 6.6, 0.8),
    ("CO2", 16.2, 1.2),
)
# TIME 구간 변경 시 data_pc/촉매 반응 계산.py GC1_TIME_* 도 동기화 (deploy/STEP7_gc1_calib.md)

# 엑셀에 포함할 검출 성분 (지정하지 않은 피크는 제외)
GC1_FID_COMPOUNDS: Tuple[str, ...] = tuple(compound for compound, _, _ in DEFAULT_FID_WINDOWS)
GC1_TCD_COMPOUNDS: Tuple[str, ...] = tuple(compound for compound, _, _ in DEFAULT_TCD_WINDOWS)

# GC1 엑셀 — Width 대신 「분석된 원소」열에 성분명(CH4 등)
GC1_EXCEL_COLUMNS = ["#", "Time", "Area", "Height", "분석된 원소", "Area%", "Symmetry"]
GC1_HEADER_ROW = {
    "#": "#",
    "Time": "Time",
    "Area": "Area",
    "Height": "Height",
    "분석된 원소": "분석된 원소",
    "Area%": "Area%",
    "Symmetry": "Symmetry",
}


@dataclass
class Gc1InjectionAnalysis:
    injection: int
    h2_area: Optional[float]
    co_area: Optional[float]
    classification: str


@dataclass
class Gc1PdfReport:
    pdf_path: str
    fid_cycles: List[List[dict]]
    tcd_cycles: List[List[dict]]
    analysis_date: str
    default_sample_name: str
    total_injections: int = 0
    skipped_last_incomplete_count: int = 0
    skipped_pre_reduction_count: int = 0
    skipped_reduction_count: int = 0
    skipped_transition_count: int = 0
    skipped_first_reaction_count: int = 0
    skipped_first_reaction: bool = False


def _require_fitz():
    if fitz is None:
        raise ImportError("PyMuPDF 미설치 — pip install pymupdf")


def _parse_float(value: str) -> Optional[float]:
    try:
        return float(value.strip())
    except (TypeError, ValueError):
        return None


def _is_number(value: str) -> bool:
    return _parse_float(value) is not None


def parse_peak_table(lines: List[str]) -> List[dict]:
    """PDF 텍스트(세로 셀)에서 적분 결과 표 추출."""
    start = None
    for i, line in enumerate(lines):
        if line.strip() == "농도[ppm]":
            start = i + 1
            break
    if start is None:
        return []
    return _parse_peak_rows(lines, start)


def parse_peak_table_continuation(lines: List[str]) -> List[dict]:
    """적분 결과 2페이지 이후 — 헤더·채널 없이 피크 번호부터 이어짐."""
    if any("분석 보고서" in line for line in lines[:10]):
        return []
    if any(re.search(r"YL6500GC\s+[ABC]", line, re.I) for line in lines[:20]):
        return []
    return _parse_peak_rows(lines, 0)


def _parse_peak_rows(lines: List[str], start: int) -> List[dict]:
    peaks: List[dict] = []
    i = start
    while i < len(lines):
        line = lines[i].strip()
        if not line or line.startswith("합계"):
            break
        if not line.isdigit():
            i += 1
            continue

        peak_num = int(line)
        i += 1
        name = ""
        if i < len(lines) and not _is_number(lines[i]):
            name = lines[i].strip()
            i += 1
        if i + 3 > len(lines):
            break
        if not all(_is_number(lines[i + j]) for j in range(4)):
            break

        rt = float(lines[i].strip())
        area = float(lines[i + 1].strip())
        height = float(lines[i + 2].strip())
        i += 4
        peaks.append(
            {
                "#": peak_num,
                "name": name,
                "Time": rt,
                "Area": area,
                "Height": height,
            }
        )
    return peaks


def parse_pdf_page(text: str) -> dict:
    lines = [line.rstrip() for line in text.splitlines()]
    channel = None
    analysis_time = None
    raw_file = None

    for line in lines:
        match = re.search(r"(\d+)\.\s*(YL6500GC\s+[ABC])", line, re.I)
        if match:
            channel = match.group(2).upper().replace("  ", " ")
        if re.fullmatch(r"\d+\.RAW", line.strip(), re.I):
            raw_file = line.strip()
        if re.search(r"\d{4}-\d{2}-\d{2}", line):
            analysis_time = line.strip()

    peaks = parse_peak_table(lines)
    is_continuation = False
    if channel is None and raw_file is None and not peaks:
        cont_peaks = parse_peak_table_continuation(lines)
        if cont_peaks:
            peaks = cont_peaks
            is_continuation = True

    return {
        "channel": channel,
        "raw_file": raw_file,
        "analysis_time": analysis_time,
        "peaks": peaks,
        "is_continuation": is_continuation,
    }


def _merge_peak_continuation_pages(pages: List[dict]) -> List[dict]:
    """
    YL6500 PDF: C 채널 피크가 많으면 다음 페이지에 번호만 이어짐(is_continuation).

    parse_gc1_pdf_path() 에서 _collect 전에 호출. 병합 후 주입당 A/B/C 3페이지 구조 유지.
    """
    merged: List[dict] = []
    for page in pages:
        if page.get("is_continuation"):
            if not merged:
                continue
            extra = page.get("peaks") or []
            if not extra:
                continue
            prev = merged[-1]
            combined = list(prev.get("peaks") or []) + extra
            merged[-1] = {**prev, "peaks": combined}
            continue
        merged.append(dict(page))
    return merged


def _channel_kind(channel: Optional[str]) -> Optional[str]:
    if not channel:
        return None
    upper = channel.upper()
    if "YL6500GC A" in upper:
        return "fid"
    if "YL6500GC C" in upper:
        return "tcd"
    if "YL6500GC B" in upper:
        return "skip"
    return None


def peaks_to_gc1_excel_rows(peaks: List[dict]) -> List[dict]:
    """Width 열 대신 분석된 원소(CH4, H2 등)를 기록."""
    rows = []
    for peak in peaks:
        compound = peak.get("name", "")
        rows.append(
            {
                "#": peak["#"],
                "name": compound,
                "Time": peak["Time"],
                "Area": peak["Area"],
                "Height": peak["Height"],
                "분석된 원소": compound,
                "Area%": "",
                "Symmetry": "",
            }
        )
    return rows


def build_gc1_stacked_dataframe(cycle_peaks_list: List[List[dict]]):
    import pandas as pd

    rows = []
    for peaks in cycle_peaks_list:
        rows.append(GC1_HEADER_ROW.copy())
        rows.extend(peaks)
    return pd.DataFrame(rows, columns=GC1_EXCEL_COLUMNS)


def write_gc1_excel(
    output_path: str,
    fid_cycles: List[List[dict]],
    tcd_cycles: List[List[dict]],
) -> None:
    """GC1 — FID/TCD 시트, E열=분석된 원소."""
    import pandas as pd

    with pd.ExcelWriter(output_path, engine="openpyxl") as writer:
        build_gc1_stacked_dataframe(fid_cycles).to_excel(
            writer,
            sheet_name=CHEM32_FID_SHEET,
            index=False,
            header=False,
        )
        build_gc1_stacked_dataframe(tcd_cycles).to_excel(
            writer,
            sheet_name=CHEM32_TCD_SHEET,
            index=False,
            header=False,
        )


def _collect_gc1_cycles_from_pages(
    pages: List[dict],
) -> Tuple[List[List[dict]], List[List[dict]], List[str]]:
    fid_cycles: List[List[dict]] = []
    tcd_cycles: List[List[dict]] = []
    analysis_times: List[str] = []

    i = 0
    while i < len(pages):
        page = pages[i]
        kind = _channel_kind(page.get("channel"))
        if kind != "fid":
            i += 1
            continue

        fid_page = page
        tcd_page = None
        tcd_idx = None
        fid_raw = list(fid_page.get("peaks") or [])
        k = i + 1
        while k < len(pages) and pages[k].get("is_continuation"):
            fid_raw.extend(pages[k].get("peaks") or [])
            k += 1

        j = k
        while j < len(pages):
            if pages[j].get("is_continuation"):
                j += 1
                continue
            next_kind = _channel_kind(pages[j].get("channel"))
            if next_kind == "tcd":
                tcd_page = pages[j]
                tcd_idx = j
                break
            if next_kind == "fid":
                break
            j += 1
            if j > i + 5:
                break

        if fid_page.get("analysis_time"):
            analysis_times.append(fid_page["analysis_time"])
        if tcd_page and tcd_page.get("analysis_time"):
            analysis_times.append(tcd_page["analysis_time"])

        fid_windows = load_rt_windows("GC1_FID", DEFAULT_FID_WINDOWS)
        tcd_windows = load_rt_windows("GC1_TCD", DEFAULT_TCD_WINDOWS)
        tcd_raw = list((tcd_page or {}).get("peaks") or [])
        if tcd_idx is not None:
            m = tcd_idx + 1
            while m < len(pages) and pages[m].get("is_continuation"):
                tcd_raw.extend(pages[m].get("peaks") or [])
                m += 1
        fid_filtered = filter_peaks_to_target_compounds(fid_raw, fid_windows)
        tcd_filtered = filter_peaks_to_target_compounds(tcd_raw, tcd_windows)
        fid_cycles.append(peaks_to_gc1_excel_rows(fid_filtered))
        tcd_cycles.append(peaks_to_gc1_excel_rows(tcd_filtered))
        i = _next_fid_page_index(pages, i)

    return fid_cycles, tcd_cycles, analysis_times


def _next_fid_page_index(pages: List[dict], fid_index: int) -> int:
    i = fid_index + 1
    while i < len(pages):
        if pages[i].get("is_continuation"):
            i += 1
            continue
        if _channel_kind(pages[i].get("channel")) == "fid":
            return i
        i += 1
    return len(pages)


def _pdf_env_float(name: str, default: float) -> float:
    raw = os.getenv(name, "").strip()
    if not raw:
        return default
    try:
        return float(raw)
    except ValueError:
        return default


def _find_last_channel_b_page_index(pages: List[dict]) -> Optional[int]:
    last_idx: Optional[int] = None
    for idx, page in enumerate(pages):
        channel = (page.get("channel") or "").upper()
        if "YL6500GC B" in channel:
            last_idx = idx
    return last_idx


def _detect_time_axis_max_minutes(page_text: str, default: float = 34.0) -> float:
    ticks = []
    for match in re.finditer(r"(?<![\d.])(\d{1,2}\.\d{2})(?![\d.])", page_text):
        value = float(match.group(1))
        if 0.0 <= value <= 60.0:
            ticks.append(value)
    if not ticks:
        return default
    # 크로마토그램 x축 눈금(보통 0~34분) — mV 축(200~2000) 제외
    time_ticks = [value for value in ticks if value <= 40.0]
    return max(time_ticks) if time_ticks else default


def measure_channel_b_scan_end_minutes(page, *, axis_max_min: Optional[float] = None) -> Optional[float]:
    """
    YL6500GC B 페이지 크로마토그램 — 전압선(베이스라인)이 x축 시간 어디까지 그어졌는지(분).

    Autochro 실시간 PDF: 분석 중이면 선이 짧고, 완료면 ~28–33분까지 이어짐.
    """
    text = page.get_text("text")
    if "YL6500GC B" not in text:
        return None

    axis_max = axis_max_min if axis_max_min is not None else _detect_time_axis_max_minutes(text)

    xs: List[float] = []
    horiz_max_x: List[float] = []
    for drawing in page.get_drawings():
        for item in drawing.get("items", []):
            if item[0] != "l":
                continue
            p1, p2 = item[1], item[2]
            xs.extend([p1.x, p2.x])
            if abs(p1.y - p2.y) <= 1.5:
                horiz_max_x.append(max(p1.x, p2.x))

    if not xs or not horiz_max_x:
        return None

    x_min, x_max = min(xs), max(xs)
    inner_right = x_max - 1.0
    trace_x_max = x_min
    for x in horiz_max_x:
        if x < inner_right:
            trace_x_max = max(trace_x_max, x)

    width = x_max - x_min
    if width <= 0 or trace_x_max <= x_min:
        return 0.0
    return (trace_x_max - x_min) / width * axis_max


def maybe_drop_last_incomplete_gc1_cycle(
    fid_cycles: List[List[dict]],
    tcd_cycles: List[List[dict]],
    pages: List[dict],
    doc,
    *,
    quiet: bool = False,
) -> int:
    """
    실험 중 PDF 저장 시 마지막 주입이 아직 끝나지 않았을 수 있음.

    YL6500GC B 페이지 PDF 벡터에서 크로마 전압선(수평선)의 x축 끝을 분 단위로 측정.
    GC1_LAST_CYCLE_MIN_SCAN_MIN(기본 18) 미만이면 fid/tcd 마지막 주입 제거.
    완주 run 은 ~32–33분; 28분대는 진행 중 저장일 수 있으나 현재 임계값은 18분.
    """
    if os.getenv("GC1_DROP_LAST_INCOMPLETE_CYCLE", "1").strip().lower() in (
        "0",
        "false",
        "no",
        "off",
    ):
        return 0
    if not fid_cycles and not tcd_cycles:
        return 0

    min_minutes = _pdf_env_float("GC1_LAST_CYCLE_MIN_SCAN_MIN", 18.0)
    b_idx = _find_last_channel_b_page_index(pages)
    if b_idx is None:
        return 0

    scan_minutes = measure_channel_b_scan_end_minutes(doc.load_page(b_idx))
    if scan_minutes is None:
        if not quiet:
            print("\n[GC1] 마지막 주입 B 채널 스캔 길이 확인 불가 — 주입 유지")
        return 0

    if scan_minutes >= min_minutes:
        if not quiet:
            print(
                f"\n[GC1] 마지막 주입 B 채널 전압선 {scan_minutes:.1f}분 ≥ {min_minutes:g}분 — 주입 유지"
            )
        return 0

    if fid_cycles:
        fid_cycles.pop()
    if tcd_cycles:
        tcd_cycles.pop()
    if not quiet:
        remaining = max(len(fid_cycles), len(tcd_cycles))
        print(
            f"\n[GC1] 마지막 주입 B 채널 전압선 {scan_minutes:.1f}분 < {min_minutes:g}분 "
            f"— 불완전 주입 1회 제외 (A/B/C) → {remaining}주입"
        )
    return 1


def _pdf_env_int(name: str, default: int) -> int:
    raw = os.getenv(name, "").strip()
    if not raw:
        return default
    try:
        return int(raw)
    except ValueError:
        return default


def _pdf_readable(pdf_path: str) -> bool:
    """파일 잠금 해제·헤더·페이지 수 확인 (한컴 저장 직후 Acrobat 오류 방지)."""
    try:
        with open(pdf_path, "rb") as handle:
            if handle.read(5) != b"%PDF-":
                return False
        _require_fitz()
        doc = fitz.open(pdf_path)
        ok = doc.page_count > 0
        doc.close()
        return ok
    except Exception:
        return False


def wait_for_pdf_file_ready(
    pdf_path: str,
    *,
    max_wait_sec: Optional[float] = None,
    stable_sec: float = 2.0,
    poll_sec: float = 0.5,
    only_if_recent_sec: Optional[float] = 300,
    log_fn=None,
) -> bool:
    """
    PDF 가 디스크에 완전히 쓰이고 열릴 때까지 대기.

    한컴 PDF 창이 닫혀도 OS/뷰어(Acrobat)가 파일을 잠그면 isfile() 만으로는 부족합니다.
    크기 안정 + fitz 열기 성공까지 폴링합니다.
    """
    if max_wait_sec is None:
        max_wait_sec = float(_pdf_env_int("GC1_PDF_READY_WAIT_SEC", 90))

    def _log(msg: str) -> None:
        if log_fn:
            log_fn(msg)

    deadline = time.time() + max_wait_sec
    while time.time() < deadline and not os.path.isfile(pdf_path):
        time.sleep(poll_sec)
    if not os.path.isfile(pdf_path):
        return False

    if only_if_recent_sec is not None:
        try:
            age = time.time() - os.path.getmtime(pdf_path)
        except OSError:
            age = 0.0
        if age > only_if_recent_sec and _pdf_readable(pdf_path):
            return True
        if age > only_if_recent_sec and not _pdf_readable(pdf_path):
            return False

    last_size = -1
    stable_start: Optional[float] = None
    logged_wait = False
    while time.time() < deadline:
        if _pdf_readable(pdf_path):
            return True
        try:
            size = os.path.getsize(pdf_path)
        except OSError:
            size = -1
            stable_start = None
            time.sleep(poll_sec)
            continue
        if size > 0 and size == last_size:
            if stable_start is None:
                stable_start = time.time()
            elif time.time() - stable_start >= stable_sec:
                if not logged_wait:
                    _log(
                        f"PDF 파일 잠금 해제 대기 (최대 {int(max_wait_sec)}초) — "
                        "저장 중 열면 Acrobat 오류가 날 수 있어 기다립니다"
                    )
                    logged_wait = True
                if _pdf_readable(pdf_path):
                    return True
        else:
            last_size = size
            stable_start = None
        time.sleep(poll_sec)
    return _pdf_readable(pdf_path)


def parse_gc1_pdf_path(
    pdf_path: str,
    *,
    quiet: bool = False,
    skip_ready_wait: bool = False,
) -> Gc1PdfReport:
    """PDF 1개 → FID/TCD 주입별 피크 목록."""
    _require_fitz()
    if not os.path.isfile(pdf_path):
        raise FileNotFoundError(pdf_path)

    if not skip_ready_wait and not wait_for_pdf_file_ready(pdf_path):
        raise RuntimeError(
            f"PDF 를 아직 열 수 없음 — 다른 프로그램(Acrobat/한컴)이 사용 중일 수 있습니다: {pdf_path}"
        )

    doc = fitz.open(pdf_path)
    pages = [parse_pdf_page(doc.load_page(i).get_text("text")) for i in range(doc.page_count)]
    pages = _merge_peak_continuation_pages(pages)

    fid_cycles, tcd_cycles, analysis_times = _collect_gc1_cycles_from_pages(pages)

    total_injections = len(fid_cycles)
    skipped_last = maybe_drop_last_incomplete_gc1_cycle(
        fid_cycles,
        tcd_cycles,
        pages,
        doc,
        quiet=quiet,
    )
    doc.close()
    (
        fid_cycles,
        tcd_cycles,
        skipped_pre,
        skipped_reduction,
        skipped_transition,
        skipped_first,
        found_first,
    ) = trim_reduction_and_first_reaction(
        fid_cycles,
        tcd_cycles,
        quiet=quiet,
    )

    analysis_date = infer_analysis_date(pdf_path, analysis_times)
    return Gc1PdfReport(
        pdf_path=pdf_path,
        fid_cycles=fid_cycles,
        tcd_cycles=tcd_cycles,
        analysis_date=analysis_date,
        default_sample_name=infer_sample_name_from_pdf(pdf_path, analysis_date),
        total_injections=total_injections,
        skipped_last_incomplete_count=skipped_last,
        skipped_pre_reduction_count=skipped_pre,
        skipped_reduction_count=skipped_reduction,
        skipped_transition_count=skipped_transition,
        skipped_first_reaction_count=skipped_first,
        skipped_first_reaction=skipped_first > 0,
    )


def infer_analysis_date(pdf_path: str, analysis_times: Optional[List[str]] = None) -> str:
    filename = os.path.basename(pdf_path)
    match = re.match(r"(\d{6})\s", filename)
    if match:
        yymmdd = match.group(1)
        return f"20{yymmdd}"

    for text in analysis_times or []:
        dt_match = re.search(r"(\d{4})-(\d{2})-(\d{2})", text)
        if dt_match:
            return f"{dt_match.group(1)}{dt_match.group(2)}{dt_match.group(3)}"

    return datetime.now().strftime("%Y%m%d")


def infer_sample_name_from_pdf(pdf_path: str, analysis_date: str) -> str:
    stem = os.path.splitext(os.path.basename(pdf_path))[0].strip()
    if stem[:8].isdigit() and len(stem) > 8:
        return stem[8:].strip()
    if stem[:6].isdigit() and len(stem) > 6:
        return stem[6:].strip()
    if analysis_date and stem.startswith(analysis_date):
        return stem[len(analysis_date) :].strip()
    return stem


GC1_OBSOLETE_FILE_MARKERS = ("임시 pdf", "반응(농도)@온도 시료이름")
GC1_COMPARE_COMPOUNDS: Tuple[str, ...] = GC1_FID_COMPOUNDS + GC1_TCD_COMPOUNDS


def _area_values_close(left: float, right: float, rel_tol: float = 0.002, abs_tol: float = 1.0) -> bool:
    if abs(left - right) <= abs_tol:
        return True
    scale = max(abs(left), abs(right), 1.0)
    return abs(left - right) / scale <= rel_tol


def _reaction_cycle_area_map(fid_cycle: List[dict], tcd_cycle: List[dict]) -> Dict[str, float]:
    areas: Dict[str, float] = {}
    for compound in GC1_FID_COMPOUNDS:
        value = get_compound_area(fid_cycle, compound)
        if value is not None:
            areas[compound] = value
    for compound in GC1_TCD_COMPOUNDS:
        value = get_compound_area(tcd_cycle, compound)
        if value is not None:
            areas[compound] = value
    return areas


def _reaction_cycles_match(cycle_a: Tuple[List[dict], List[dict]], cycle_b: Tuple[List[dict], List[dict]]) -> bool:
    left = _reaction_cycle_area_map(cycle_a[0], cycle_a[1])
    right = _reaction_cycle_area_map(cycle_b[0], cycle_b[1])
    if not left or not right:
        return False
    keys = set(left.keys()) | set(right.keys())
    for key in keys:
        if key not in left or key not in right:
            return False
        if not _area_values_close(left[key], right[key]):
            return False
    return True


def _reaction_cycle_pairs(report: Gc1PdfReport) -> List[Tuple[List[dict], List[dict]]]:
    return list(zip(report.fid_cycles, report.tcd_cycles))


def _same_experiment_reaction_data(
    cycles_a: List[Tuple[List[dict], List[dict]]],
    cycles_b: List[Tuple[List[dict], List[dict]]],
) -> bool:
    """반응(엑셀) 주입 — 짧은 쪽이 긴 쪽의 area prefix 와 같으면 동일 실험."""
    if not cycles_a or not cycles_b:
        return False
    short, long = (cycles_a, cycles_b) if len(cycles_a) <= len(cycles_b) else (cycles_b, cycles_a)
    if len(long) < len(short):
        return False
    for idx, short_cycle in enumerate(short):
        if not _reaction_cycles_match(long[idx], short_cycle):
            return False
    return True


def _try_parse_gc1_pdf_quiet(pdf_path: str) -> Optional[Gc1PdfReport]:
    try:
        return parse_gc1_pdf_path(pdf_path, quiet=True, skip_ready_wait=True)
    except Exception:
        return None


def _related_xlsx_paths(pdf_path: str, report: Gc1PdfReport, output_dir: str) -> List[str]:
    sample = infer_sample_name_from_pdf(pdf_path, report.analysis_date)
    exact = os.path.join(output_dir, f"{report.analysis_date} {sample}.xlsx")
    if os.path.isfile(exact):
        return [exact]
    return []


def _experiment_group_key(stem: str) -> str:
    """날짜 + 반응@(농도) 까지 — 시료명·대소문자 차이 무시."""
    normalized = re.sub(r"\s+", " ", stem.strip().lower())
    match = re.match(r"^(\d{6})\s+([a-z0-9.]+@\([^)]+\))", normalized)
    if match:
        return f"{match.group(1)} {match.group(2)}"
    match = re.match(r"^(\d{6})([a-z0-9.]+@\([^)]+\))", normalized.replace(" ", ""))
    if match:
        return f"{match.group(1)} {match.group(2)}"
    if len(normalized) >= 6 and normalized[:6].isdigit():
        return normalized[:6]
    return normalized


def _is_obsolete_gc1_stem(stem: str) -> bool:
    return any(marker in stem for marker in GC1_OBSOLETE_FILE_MARKERS)


def _is_truncated_gc1_stem(shorter: str, correct: str) -> bool:
    """이름이 잘린 PDF (예: ... ni → ... ni-ce)."""
    if shorter == correct or not correct.startswith(shorter):
        return False
    if len(correct) <= len(shorter):
        return False
    if len(correct) >= 6 and correct[:6].isdigit() and not shorter.startswith(correct[:6]):
        return False
    tail = correct[len(shorter) :]
    return not tail or tail[0] in (" ", "-", "_")


def cleanup_superseded_gc1_files(
    output_dir: str,
    kept_pdf_path: str,
    *,
    log_fn=None,
) -> Tuple[int, str]:
    """
    잘못된/중복 PDF·엑셀 정리.

    - placeholder·잘린 파일명
    - 반응 주입 area 가 같고 사이클 수가 더 적은 PDF (이름·날짜 달라도)
    """
    surviving = os.path.normpath(os.path.abspath(kept_pdf_path))
    surviving_stem = os.path.splitext(os.path.basename(surviving))[0]
    removed = 0
    reports: Dict[str, Gc1PdfReport] = {}

    def _log(msg: str) -> None:
        if log_fn:
            log_fn(msg)

    def _report_for(path: str) -> Optional[Gc1PdfReport]:
        norm = os.path.normpath(os.path.abspath(path))
        if norm not in reports:
            reports[norm] = _try_parse_gc1_pdf_quiet(path)
        return reports[norm]

    def _remove_path(path: str, reason: str) -> None:
        nonlocal removed
        try:
            os.remove(path)
            _log(f"{reason}: {os.path.basename(path)}")
            removed += 1
        except OSError as exc:
            _log(f"파일 삭제 실패 ({os.path.basename(path)}): {exc}")

    if not os.path.isdir(output_dir):
        return 0, surviving

    pdf_paths = [
        os.path.normpath(os.path.abspath(path))
        for path in glob.glob(os.path.join(output_dir, "*.pdf"))
        if not os.path.basename(path).startswith("~$")
    ]

    delete_pdfs: set[str] = set()

    for path in pdf_paths:
        if path == surviving:
            continue
        stem = os.path.splitext(os.path.basename(path))[0]
        if _is_obsolete_gc1_stem(stem) or _is_truncated_gc1_stem(stem, surviving_stem):
            delete_pdfs.add(path)

    seed_report = _report_for(surviving)
    seed_cycles = _reaction_cycle_pairs(seed_report) if seed_report else []
    seed_key = _experiment_group_key(surviving_stem)

    group = {surviving}
    for path in pdf_paths:
        if path == surviving:
            continue
        other_report = _report_for(path)
        if not other_report:
            continue
        other_cycles = _reaction_cycle_pairs(other_report)
        if seed_cycles and other_cycles and _same_experiment_reaction_data(seed_cycles, other_cycles):
            group.add(path)
            continue
        other_stem = os.path.splitext(os.path.basename(path))[0]
        if _experiment_group_key(other_stem) == seed_key and (seed_cycles or other_cycles):
            group.add(path)

    if len(group) > 1:
        best_path = surviving
        best_count = len(seed_cycles)
        for path in group:
            report = _report_for(path)
            if not report:
                continue
            count = len(_reaction_cycle_pairs(report))
            if count > best_count:
                best_path = path
                best_count = count

        for path in group:
            if path != best_path:
                delete_pdfs.add(path)
        surviving = best_path
        surviving_stem = os.path.splitext(os.path.basename(surviving))[0]

    for path in sorted(delete_pdfs):
        report = _report_for(path)
        _remove_path(path, "중복/구버전 PDF 삭제")
        if report:
            for xlsx_path in _related_xlsx_paths(path, report, output_dir):
                if os.path.isfile(xlsx_path):
                    _remove_path(xlsx_path, "짝 엑셀 삭제")

    for pattern in ("*.xlsx",):
        for path in glob.glob(os.path.join(output_dir, pattern)):
            if os.path.basename(path).startswith("~$"):
                continue
            stem = os.path.splitext(os.path.basename(path))[0]
            if _is_obsolete_gc1_stem(stem):
                _remove_path(path, "잘못된 파일 삭제")

    return removed, surviving


def resolve_gc1_pdf_dir(config) -> str:
    env_dir = os.getenv("GC1_PDF_DIR", "").strip()
    if env_dir:
        return os.path.normpath(os.path.expanduser(env_dir))
    if getattr(config, "sequence_folder", None) and str(config.sequence_folder).lower().endswith(".pdf"):
        return os.path.dirname(os.path.abspath(config.sequence_folder))
    return config.excel_output_dir


def list_pdf_files(pdf_dir: str) -> List[str]:
    pattern = os.path.join(pdf_dir, "*.pdf")
    files = [
        path
        for path in glob.glob(pattern)
        if not os.path.basename(path).startswith("~$")
    ]
    return sorted(files, key=os.path.getmtime, reverse=True)


def find_active_pdf(config, explicit_pdf: Optional[str] = None) -> Optional[str]:
    if explicit_pdf:
        path = os.path.normpath(explicit_pdf)
        return path if os.path.isfile(path) else None

    if config.sequence_folder and str(config.sequence_folder).lower().endswith(".pdf"):
        path = os.path.normpath(config.sequence_folder)
        return path if os.path.isfile(path) else None

    pdf_dir = resolve_gc1_pdf_dir(config)
    if not os.path.isdir(pdf_dir):
        return None

    pdfs = list_pdf_files(pdf_dir)
    return pdfs[0] if pdfs else None


def get_latest_pdf_mtime(pdf_path: str) -> Optional[float]:
    try:
        return os.path.getmtime(pdf_path)
    except OSError:
        return None


def load_rt_windows(prefix: str, default: Tuple[Tuple[str, float, float], ...]) -> Tuple[Tuple[str, float, float], ...]:
    """env 예: GC1_FID_CH4=1.4,0.35"""
    windows = []
    for compound, center, tolerance in default:
        env_key = f"{prefix}_{compound}"
        raw = os.getenv(env_key, "").strip()
        if raw:
            parts = [p.strip() for p in raw.split(",")]
            if len(parts) >= 2 and _parse_float(parts[0]) is not None and _parse_float(parts[1]) is not None:
                windows.append((compound, float(parts[0]), float(parts[1])))
                continue
        windows.append((compound, center, tolerance))
    return tuple(windows)


def match_peak_by_window(peaks: List[dict], center: float, tolerance: float) -> Optional[dict]:
    best = None
    best_dist = tolerance
    for peak in peaks:
        dist = abs(float(peak["Time"]) - center)
        if dist <= best_dist:
            best_dist = dist
            best = peak
    return best


def assign_compounds(
    peaks: List[dict],
    windows: Tuple[Tuple[str, float, float], ...],
) -> Dict[str, Optional[dict]]:
    assigned: Dict[str, Optional[dict]] = {compound: None for compound, _, _ in windows}
    used_indices: set[int] = set()

    for idx, peak in enumerate(peaks):
        name = peak.get("name", "").strip().upper()
        if not name:
            continue
        for compound, _, _ in windows:
            if name == compound.upper() and assigned[compound] is None:
                assigned[compound] = peak
                used_indices.add(idx)
                break

    for compound, center, tolerance in windows:
        if assigned[compound] is not None:
            continue
        best = None
        best_dist = tolerance
        best_idx = None
        for idx, peak in enumerate(peaks):
            if idx in used_indices:
                continue
            dist = abs(float(peak["Time"]) - center)
            if dist <= best_dist:
                best = peak
                best_dist = dist
                best_idx = idx
        if best is not None and best_idx is not None:
            assigned[compound] = best
            used_indices.add(best_idx)
    return assigned


def filter_peaks_to_target_compounds(
    peaks: List[dict],
    windows: Tuple[Tuple[str, float, float], ...],
) -> List[dict]:
    """PDF 피크 중 지정 성분만 남김 — RT 구간 또는 PDF 피크이름."""
    assigned = assign_compounds(peaks, windows)
    filtered: List[dict] = []
    for peak_num, (compound, _, _) in enumerate(windows, start=1):
        peak = assigned.get(compound)
        if peak is None:
            continue
        filtered.append(
            {
                "#": peak_num,
                "name": compound,
                "Time": peak["Time"],
                "Area": peak["Area"],
                "Height": peak["Height"],
            }
        )
    return filtered


DEFAULT_REDUCTION_H2_AREA = 20000.0
DEFAULT_REDUCTION_H2_TOL = 0.35
DEFAULT_NOISE_AREA_MAX = 100.0
DEFAULT_REACTION_CO_MIN = 100.0


@dataclass(frozen=True)
class Gc1PhaseThresholds:
    reduction_h2_area: float = DEFAULT_REDUCTION_H2_AREA
    reduction_h2_tol: float = DEFAULT_REDUCTION_H2_TOL
    noise_area_max: float = DEFAULT_NOISE_AREA_MAX
    reaction_co_min: float = DEFAULT_REACTION_CO_MIN

    @property
    def reduction_h2_low(self) -> float:
        return self.reduction_h2_area * (1.0 - self.reduction_h2_tol)

    @property
    def reduction_h2_high(self) -> float:
        return self.reduction_h2_area * (1.0 + self.reduction_h2_tol)


def load_float_env(name: str, default: float) -> float:
    raw = os.getenv(name, "").strip()
    if not raw:
        return default
    parsed = _parse_float(raw)
    return default if parsed is None else parsed


def load_gc1_phase_thresholds() -> Gc1PhaseThresholds:
    return Gc1PhaseThresholds(
        reduction_h2_area=load_float_env("GC1_REDUCTION_H2_AREA", DEFAULT_REDUCTION_H2_AREA),
        reduction_h2_tol=load_float_env("GC1_REDUCTION_H2_TOL", DEFAULT_REDUCTION_H2_TOL),
        noise_area_max=load_float_env("GC1_NOISE_AREA_MAX", DEFAULT_NOISE_AREA_MAX),
        reaction_co_min=load_float_env("GC1_REACTION_CO_MIN", DEFAULT_REACTION_CO_MIN),
    )


def get_compound_area(cycle: List[dict], compound: str) -> Optional[float]:
    for row in cycle:
        name = (row.get("name") or row.get("분석된 원소") or "").strip()
        if name == compound:
            area = row.get("Area")
            if area is not None:
                return float(area)
    return None


def h2_area(tcd_cycle: List[dict]) -> Optional[float]:
    return get_compound_area(tcd_cycle, "H2")


def is_reduction_h2_area(area: Optional[float], thresholds: Gc1PhaseThresholds) -> bool:
    if area is None:
        return False
    return thresholds.reduction_h2_low <= area <= thresholds.reduction_h2_high


def is_reduction_injection(
    fid_cycle: List[dict],
    tcd_cycle: List[dict],
    thresholds: Optional[Gc1PhaseThresholds] = None,
) -> bool:
    """
    환원 구간: H2 area가 ~20000 대역이면 환원.
    FID/TCD 노이즈 피크(CH4, CO 등)가 함께 잡혀도 H2 area만 기준으로 판단.
    """
    thresholds = thresholds or load_gc1_phase_thresholds()
    return is_reduction_h2_area(h2_area(tcd_cycle), thresholds)


def is_reaction_injection(
    fid_cycle: List[dict],
    tcd_cycle: List[dict],
    thresholds: Optional[Gc1PhaseThresholds] = None,
) -> bool:
    """
    반응 시작: CO가 충분히 검출되고 H2가 환원 고정값(~20000)이 아님.
    """
    thresholds = thresholds or load_gc1_phase_thresholds()
    co = get_compound_area(tcd_cycle, "CO")
    if co is None or co < thresholds.reaction_co_min:
        return False
    return not is_reduction_h2_area(h2_area(tcd_cycle), thresholds)


def is_transition_injection(
    fid_cycle: List[dict],
    tcd_cycle: List[dict],
    thresholds: Optional[Gc1PhaseThresholds] = None,
) -> bool:
    """환원 직후 전환 구간: 환원 H2도 아니고 반응 신호(CO+H2 변동)도 아님."""
    thresholds = thresholds or load_gc1_phase_thresholds()
    if is_reduction_injection(fid_cycle, tcd_cycle, thresholds):
        return False
    if is_reaction_injection(fid_cycle, tcd_cycle, thresholds):
        return False
    return True


def _cycle_at(
    fid_cycles: List[List[dict]],
    tcd_cycles: List[List[dict]],
    idx: int,
) -> Tuple[List[dict], List[dict]]:
    fid_cycle = fid_cycles[idx] if idx < len(fid_cycles) else []
    tcd_cycle = tcd_cycles[idx] if idx < len(tcd_cycles) else []
    return fid_cycle, tcd_cycle


def _has_future_reduction(
    fid_cycles: List[List[dict]],
    tcd_cycles: List[List[dict]],
    start_idx: int,
    thresholds: Gc1PhaseThresholds,
) -> bool:
    count = max(len(fid_cycles), len(tcd_cycles))
    for idx in range(start_idx, count):
        fid_cycle, tcd_cycle = _cycle_at(fid_cycles, tcd_cycles, idx)
        if is_reduction_injection(fid_cycle, tcd_cycle, thresholds):
            return True
    return False


def find_reduction_streak(
    fid_cycles: List[List[dict]],
    tcd_cycles: List[List[dict]],
    thresholds: Optional[Gc1PhaseThresholds] = None,
) -> Tuple[Optional[int], Optional[int]]:
    thresholds = thresholds or load_gc1_phase_thresholds()
    count = max(len(fid_cycles), len(tcd_cycles))
    first_reduction: Optional[int] = None
    last_reduction: Optional[int] = None
    for idx in range(count):
        fid_cycle, tcd_cycle = _cycle_at(fid_cycles, tcd_cycles, idx)
        if is_reduction_injection(fid_cycle, tcd_cycle, thresholds):
            if first_reduction is None:
                first_reduction = idx
            last_reduction = idx
        elif first_reduction is not None:
            break
    return first_reduction, last_reduction


def classify_gc1_injections(
    fid_cycles: List[List[dict]],
    tcd_cycles: List[List[dict]],
    thresholds: Optional[Gc1PhaseThresholds] = None,
) -> List[Gc1InjectionAnalysis]:
    """주입별 H2/CO area와 구간 분류 (trim 로직과 동일)."""
    thresholds = thresholds or load_gc1_phase_thresholds()
    count = max(len(fid_cycles), len(tcd_cycles))
    first_reduction, last_reduction = find_reduction_streak(fid_cycles, tcd_cycles, thresholds)

    transition_idx: Optional[int] = None
    first_reaction_idx: Optional[int] = None
    if first_reduction is not None and last_reduction is not None:
        transition_idx = last_reduction + 1 if last_reduction + 1 < count else None
        if transition_idx is not None:
            reaction_scan = transition_idx + 1
            if reaction_scan < count:
                for idx in range(reaction_scan, count):
                    fid_cycle, tcd_cycle = _cycle_at(fid_cycles, tcd_cycles, idx)
                    if is_reaction_injection(fid_cycle, tcd_cycle, thresholds):
                        first_reaction_idx = idx
                        break

    analyses: List[Gc1InjectionAnalysis] = []
    for idx in range(count):
        fid_cycle, tcd_cycle = _cycle_at(fid_cycles, tcd_cycles, idx)
        h2 = h2_area(tcd_cycle)
        co = get_compound_area(tcd_cycle, "CO")

        if first_reduction is None:
            classification = "pre-reduction"
        elif idx < first_reduction:
            if _has_future_reduction(fid_cycles, tcd_cycles, idx, thresholds):
                classification = "pre-reduction"
            else:
                classification = "keep"
        elif idx <= last_reduction:
            classification = "reduction"
        elif transition_idx is not None and idx == transition_idx:
            classification = "transition"
        elif first_reaction_idx is not None and idx == first_reaction_idx:
            classification = "reaction-first"
        elif first_reaction_idx is not None and idx > first_reaction_idx:
            classification = "keep"
        elif transition_idx is not None and idx > transition_idx:
            classification = "transition"
        else:
            classification = "transition"

        analyses.append(
            Gc1InjectionAnalysis(
                injection=idx + 1,
                h2_area=h2,
                co_area=co,
                classification=classification,
            )
        )
    return analyses


def trim_reduction_and_first_reaction(
    fid_cycles: List[List[dict]],
    tcd_cycles: List[List[dict]],
    *,
    quiet: bool = False,
) -> Tuple[
    List[List[dict]],
    List[List[dict]],
    int,
    int,
    int,
    int,
    bool,
]:
    """
    H2 area 교차 검증으로 구간 분리:
      1) H2~20000 나오기 전 노이즈 + 환원(H2~20000) 제외
      2) 환원 직후 전환 1주입 제외 (CO 노이즈가 있어도 반응으로 보지 않음)
      3) 첫 반응 주입부터 엑셀 적재 — **GC1 전용** (GC2/GC3 는 첫 반응 1회 제외)
    """
    thresholds = load_gc1_phase_thresholds()
    count = max(len(fid_cycles), len(tcd_cycles))
    if count == 0:
        return fid_cycles, tcd_cycles, 0, 0, 0, 0, False

    idx = 0
    skipped_pre = 0
    skipped_reduction = 0
    skipped_transition = 0
    reduction_seen = False

    while idx < count:
        fid_cycle, tcd_cycle = _cycle_at(fid_cycles, tcd_cycles, idx)
        if is_reduction_injection(fid_cycle, tcd_cycle, thresholds):
            reduction_seen = True
            skipped_reduction += 1
            idx += 1
            continue
        if not reduction_seen:
            if _has_future_reduction(fid_cycles, tcd_cycles, idx, thresholds):
                skipped_pre += 1
                idx += 1
                continue
            break
        break

    if not reduction_seen:
        if not quiet:
            print(f"\n[GC1] H2~{thresholds.reduction_h2_area:.0f} 환원 구간 없음 - 반응 데이터 없음")
        return [], [], count, 0, 0, 0, False

    if idx < count:
        skipped_transition += 1
        idx += 1

    reaction_start: Optional[int] = None
    while idx < count:
        fid_cycle, tcd_cycle = _cycle_at(fid_cycles, tcd_cycles, idx)
        if is_reaction_injection(fid_cycle, tcd_cycle, thresholds):
            reaction_start = idx
            break
        skipped_transition += 1
        idx += 1

    if reaction_start is None:
        if not quiet:
            print(
                f"\n[GC1] 반응 시작 주입 없음 - "
                f"사전노이즈 {skipped_pre}, 환원 {skipped_reduction}, 전환 {skipped_transition}주입 제외"
            )
        return [], [], skipped_pre, skipped_reduction, skipped_transition, 0, False

    keep_from = reaction_start
    kept_count = count - keep_from
    if not quiet:
        print(
            f"\n[GC1] H2~{thresholds.reduction_h2_area:.0f} 기준 - "
            f"사전노이즈 {skipped_pre}, 환원 {skipped_reduction}, 전환 {skipped_transition}주입 제외, "
            f"첫 반응(#{reaction_start + 1}) 포함 → 엑셀 {kept_count}주입"
        )
    if kept_count <= 0:
        return [], [], skipped_pre, skipped_reduction, skipped_transition, 0, False

    kept_fid = fid_cycles[keep_from:]
    kept_tcd = tcd_cycles[keep_from:]
    return kept_fid, kept_tcd, skipped_pre, skipped_reduction, skipped_transition, 0, True


def summarize_assigned_compounds(report: Gc1PdfReport) -> None:
    fid_windows = load_rt_windows("GC1_FID", DEFAULT_FID_WINDOWS)
    tcd_windows = load_rt_windows("GC1_TCD", DEFAULT_TCD_WINDOWS)
    if not report.fid_cycles and not report.tcd_cycles:
        return

    print("\n[GC1] 검출 성분 요약 (엑셀 1번째 주입)")
    if report.fid_cycles:
        parts = []
        for compound in GC1_FID_COMPOUNDS:
            peak = next((row for row in report.fid_cycles[0] if row.get("name") == compound), None)
            if peak:
                parts.append(f"{compound}={float(peak['Time']):.3f}min")
            else:
                parts.append(f"{compound}=-")
        print("  FID: " + ", ".join(parts))
    if report.tcd_cycles:
        parts = []
        for compound in GC1_TCD_COMPOUNDS:
            peak = next((row for row in report.tcd_cycles[0] if row.get("name") == compound), None)
            if peak:
                parts.append(f"{compound}={float(peak['Time']):.3f}min")
            else:
                parts.append(f"{compound}=-")
        print("  TCD: " + ", ".join(parts))
