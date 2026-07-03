# -*- coding: utf-8 -*-
"""
L0 데이터 프로브 — DN (데이터명) · MTD (분석방법) (Ω.A.L0.DN.*, MTD.*).

``gc_autochro`` 의 ``tree_label_matches_data_name``, ``resolve_analysis_method_mtd_path``,
제목·트리 데이터명 읽기 **순수 함수** 이전 (T32). UI 탭 전환(W32) 은 L3.
"""

from __future__ import annotations

import os
import re
from typing import Mapping, Sequence

from gc1_runtime.layer0_config import read_analysis_method_dir

# Ω.A.L0.DN-T.05a / MTD date6
_DATE6_PREFIX = re.compile(r"^\d{6}")
# Ω.A.L0.DN-T.05b / MTD.01b
_DATE8_PREFIX = re.compile(r"^(\d{8})")
_TITLE_AUTOCHRO_RX = re.compile(r"\s[-–]\s+.*[Aa]utochro")
_DEFAULT_INSTRUMENT_MARKERS = ("YL6500 GC", "YL6500GC")


def normalize_tree_label(text: str) -> str:
    """L1.03 보조 — 트리·데이터명 비교용 공백 정규화."""
    return re.sub(r"\s+", " ", (text or "").strip().lower())


def tree_label_matches_data_name(tree_line: str, data_name: str) -> bool:
    """
    Ω.A.L1.03 / L0-DN — 분석목록 트리 시료명 ↔ 제어목록 데이터명.

    접미사 `` - 상온-1`` 등 허용 (``gc_autochro`` 와 동일).
    """
    line = normalize_tree_label(tree_line)
    name = normalize_tree_label(data_name)
    if not line or not name:
        return False
    if line == name:
        return True
    if line.startswith(name + " ") or line.startswith(name + "-"):
        return True
    compact_line = re.sub(r"\s+", "", line)
    compact_name = re.sub(r"\s+", "", name)
    if compact_line == compact_name or compact_line.startswith(compact_name):
        return True
    return tree_fuzzy_matches_data_name(tree_line, data_name)


def tree_fuzzy_matches_data_name(text: str, data_name: str) -> bool:
    """OCR·트리 잡음 — 동일 날짜 + dre/ni 등 특징 공유."""
    line_c = re.sub(r"\s+", "", (text or "").lower())
    name_c = re.sub(r"\s+", "", (data_name or "").lower())
    target_date = extract_date8_from_data_name(data_name)
    if not target_date or target_date not in line_c:
        return False
    if len(line_c) < len(target_date) + 3:
        return False
    markers = ("dre", "ni", "ce", "la", "환원", "수열")
    for part in markers:
        if part in name_c and part in line_c:
            return True
    prefix = name_c[: min(14, len(name_c))]
    return prefix in line_c or line_c[:14] in name_c


def extract_date8_from_data_name(data_name: str) -> str:
    """데이터명 앞 8자리 날짜 (20260630)."""
    compact = re.sub(r"\s+", "", (data_name or "").strip())
    match8 = _DATE8_PREFIX.match(compact)
    if match8:
        return match8.group(1)
    match6 = re.match(r"^(\d{6})", compact)
    if match6:
        return f"20{match6.group(1)}"
    return ""


def rank_tree_line_for_data_name(line: str, data_name: str) -> float:
    """
    분석목록 트리 후보 점수 — 날짜가 다른 시료는 제외.

    MTD·적분은 선택한 트리 노드에 저장되므로 제어목록 데이터명과 동일 노드 필수.
    """
    if not tree_label_matches_data_name(line, data_name):
        return -1.0
    line_c = re.sub(r"\s+", "", line.lower())
    name_c = re.sub(r"\s+", "", data_name.lower())
    target_date = extract_date8_from_data_name(data_name)
    score = 0.0
    line_dates = re.findall(r"20\d{6}", line_c)
    if target_date:
        if target_date in line_dates or target_date in line_c:
            score += 100.0
        elif line_dates:
            return -1.0
    if line_c.startswith(name_c[: min(20, len(name_c))]):
        score += 50.0
    if normalize_tree_label(line) == normalize_tree_label(data_name):
        score += 30.0
    return score


def analysis_tree_matching_lines(
    lines: Sequence[str], data_name: str
) -> list[str]:
    """분석목록 트리에서 데이터명과 매칭되는 줄."""
    return [
        (line or "").strip()
        for line in lines
        if (line or "").strip() and tree_label_matches_data_name(line, data_name)
    ]


def analysis_tree_has_control_overlap(
    lines: Sequence[str], data_name: str
) -> bool:
    """
    제어목록 잔상이 분석목록 왼쪽 트리에 겹친 상태.

    같은 시료명이 트리에 2줄 이상 보이면 True — MTD·우클릭이 잘못된 노드로 감.
    """
    return len(analysis_tree_matching_lines(lines, data_name)) >= 2


def analysis_tree_line_has_control_ghost(line: str) -> bool:
    """
    분석목록 트리 한 줄에 제어목록 잔상.

    pywinauto 는 중복을 한 줄로 합쳐 읽을 수 있음 — 예: ``| 제어목록 | @ 20260630...``
    탭 라벨만 섞인 ``제어목록`` 단독·짧은 줄은 잔상 아님 (W32 오탐).
    """
    s = (line or "").strip()
    if "제어목록" not in s:
        return False
    if re.fullmatch(r"제어목록\s*", s):
        return False
    # 실제 잔상: 제어목록 탭 UI가 트리 노드와 한 줄로 겹침
    if "@" in s and re.search(r"20\d{6}", s):
        return True
    if re.search(r"[|│].*제어목록", s) or re.search(r"제어목록.*[|│]", s):
        return True
    return False


def analysis_tree_needs_paint_refresh(
    lines: Sequence[str],
    data_name: str,
    *,
    ocr_text: str = "",
) -> bool:
    """
    제어목록→분석목록 탭 새로고침이 필요한지.

    사람 눈에 2줄·컬러 아이콘 중복이어도 W32 ``tree.texts()`` 는 1줄일 수 있음.
    ``제어목록`` 단독·탭 라벨 bleed 는 제외 — ``| 제어목록 | @`` 형태·동일 시료 2줄만.
    """
    if any(analysis_tree_line_has_control_ghost(ln) for ln in lines):
        return True
    blob = (ocr_text or "").strip() or "\n".join(lines)
    if any(analysis_tree_line_has_control_ghost(ln) for ln in blob.splitlines()):
        return True
    if analysis_tree_has_control_overlap(lines, data_name):
        return True
    return False


def is_valid_data_name(name: str) -> bool:
    """Ω.A.L0.DN.99 — 비어 있지 않고 날짜 접두(6자리+) 있음."""
    stem = (name or "").strip().split(".")[0].strip()
    return bool(stem and _DATE6_PREFIX.match(stem))


def parse_data_name_from_window_title(title: str) -> str:
    """
    Ω.A.L0.DN-T.01~05 — 창 제목에서 데이터명.

    ``20260629 dre(3) - Autochro-3000`` → ``20260629 dre(3)``
    """
    text = (title or "").strip()
    match = _TITLE_AUTOCHRO_RX.search(text)
    if not match:
        return ""
    name = text[: match.start()].strip().split(".")[0].strip()
    return name if is_valid_data_name(name) else ""


def parse_data_name_from_tree_lines(
    lines: Sequence[str],
    *,
    selected: Sequence[str] | None = None,
    instrument_markers: Sequence[str] = _DEFAULT_INSTRUMENT_MARKERS,
) -> str:
    """
    Ω.A.L0.DN-R.01~04 — 제어목록 트리 **파란 선택** 데이터명.

    1) ``get_selected`` (사용자가 클릭한 시료)
    2) 없을 때만 YL6500 GC 바로 위 줄 (구 Autochro 고정 슬롯)
    """
    if selected:
        candidate = str(selected[0]).strip().split(".")[0].strip()
        if is_valid_data_name(candidate):
            return candidate
    items = [(line or "").strip() for line in lines if (line or "").strip()]
    for idx, line in enumerate(items):
        if any(marker in line for marker in instrument_markers) and idx > 0:
            candidate = items[idx - 1].split(".")[0].strip()
            if is_valid_data_name(candidate):
                return candidate
    return ""


def resolve_data_name(
    *,
    window_title: str = "",
    tree_lines: Sequence[str] | None = None,
    tree_selected: Sequence[str] | None = None,
    env_fallback: str = "",
) -> str:
    """
    Ω.A.L0.DN chain — title → tree → env fallback.

    모두 실패 시 ``ValueError`` (E_DATA_NAME).
    """
    for reader in (
        lambda: parse_data_name_from_window_title(window_title),
        lambda: parse_data_name_from_tree_lines(
            tree_lines or (),
            selected=tree_selected,
        ),
    ):
        name = reader()
        if name:
            return name
    fallback = (env_fallback or "").strip()
    if fallback:
        return fallback
    raise ValueError("제어목록 데이터명을 찾지 못함")


def extract_mtd_date_prefix(data_name: str) -> str:
    """Ω.A.L0.MTD.01 / 01b — 8자리 우선, 6자리면 20 접두."""
    compact = re.sub(r"\s+", "", (data_name or "").strip())
    match8 = _DATE8_PREFIX.match(compact)
    if match8:
        return match8.group(1)
    match6 = re.match(r"^(\d{6})", compact)
    if match6:
        return f"20{match6.group(1)}"
    raise ValueError(f"데이터명에서 날짜 추출 실패: {data_name!r}")


def build_analysis_method_mtd_path(data_name: str, mtd_dir: str) -> str:
    """Ω.A.L0.MTD.02 — ``{dir}/{YYYYMMDD} 분석방법.MTD`` (존재 검사 없음)."""
    date = extract_mtd_date_prefix(data_name)
    filename = f"{date} 분석방법.MTD"
    base = os.path.normpath(os.path.expanduser(mtd_dir))
    return os.path.join(base, filename)


def mtd_file_exists(path: str) -> bool:
    """Ω.A.L0.MTD.03.FS.isfile"""
    return os.path.isfile(path)


def resolve_analysis_method_mtd_path(
    data_name: str,
    *,
    mtd_dir: str | None = None,
    env: Mapping[str, str] | None = None,
) -> str:
    """
    MTD full chain — dir from ``mtd_dir`` or B-CFG ``AUTOCHRO_ANALYSIS_METHOD_DIR``.

    없으면 ``FileNotFoundError`` (E_MTD_MISSING).
    """
    directory = mtd_dir if mtd_dir is not None else read_analysis_method_dir(env)
    path = build_analysis_method_mtd_path(data_name, directory)
    if not mtd_file_exists(path):
        raise FileNotFoundError(f"분석방법 MTD 없음: {path}")
    return path
