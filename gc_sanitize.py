# -*- coding: utf-8 -*-
"""시료명·출력 경로 안전 검증 (path traversal 방지)."""
from __future__ import annotations

import os
import re
from typing import Optional

_WIN_INVALID_CHARS = re.compile(r'[<>:"\\|?*\x00-\x1f]')
_SEQ_DATE_RE = re.compile(r'^\d{8}$')
MAX_SAMPLE_NAME_LEN = 120

# ChemStation 자동 시퀀스 폴더명 — 사용자가 시료명을 안 정한 경우
_AUTO_SEQUENCE_FOLDER_RE = re.compile(
    r"sequence\s+\d{4}-\d{2}-\d{2}",
    re.IGNORECASE,
)
# Data 압축형: 20260724DRE(1.5)600CNi5-Al2O3  /  20260724DRE(1.5%)@600CNi5-Al2O3
_COMPACT_SAMPLE_FOLDER_RE = re.compile(
    r"^(?P<date>20\d{6})"
    r"(?P<rxn>DRE|DRM|DRME)"
    r"\((?P<conc>[^)]+)\)"
    r"@?"
    r"(?P<temp>\d{3,4})C?"
    r"(?P<rest>.*)$",
    re.IGNORECASE,
)
# 이미 띄어쓴 형태: 20260724 DRE(1.5%)@600C Ni5-Al2O3
_SPACED_SAMPLE_FOLDER_RE = re.compile(
    r"^(?P<date>20\d{6})\s+"
    r"(?P<rxn>DRE|DRM|DRME)"
    r"\((?P<conc>[^)]+)\)"
    r"(?:@(?P<temp>\d{3,4})C?)?"
    r"(?P<rest>.*)$",
    re.IGNORECASE,
)


def is_chemstation_auto_sequence_name(folder_name: str) -> bool:
    """`20251221 sequence 2026-07-24 15-23-24` 처럼 자동 시퀀스명인지."""
    name = (folder_name or "").strip()
    if not name:
        return False
    return bool(_AUTO_SEQUENCE_FOLDER_RE.search(name))


def normalize_gc2_folder_sample_name(folder_name: str) -> Optional[str]:
    """
    Data 시료 폴더명 → 엑셀 기본 시료명.

    예: ``20260724DRE(1.5)600CNi5-Al2O3``
      → ``20260724 DRE(1.5%)@600C Ni5-Al2O3``

    자동 시퀀스명(``… sequence YYYY-MM-DD …``)이면 None (사용자 입력 필수).
    """
    name = (folder_name or "").strip()
    if not name:
        return None
    if is_chemstation_auto_sequence_name(name):
        return None

    match = _SPACED_SAMPLE_FOLDER_RE.match(name)
    if not match:
        match = _COMPACT_SAMPLE_FOLDER_RE.match(re.sub(r"\s+", "", name))
    if not match:
        loose = re.match(
            r"^(?P<date>20\d{6})\s+(?P<body>.+)$",
            name,
            re.IGNORECASE,
        )
        if not loose:
            return None
        body = loose.group("body").strip()
        if not body or is_chemstation_auto_sequence_name(body):
            return None
        if not re.search(r"(DRE|DRM|DRME)", body, re.IGNORECASE):
            return None
        return f"{loose.group('date')} {body}".strip()

    date = match.group("date")
    rxn = match.group("rxn").upper()
    conc = (match.group("conc") or "").strip()
    if conc and not conc.endswith("%"):
        conc = f"{conc}%"
    temp = (match.groupdict().get("temp") or "").strip()
    rest = (match.group("rest") or "").strip()
    rest = re.sub(r"^[@\s_\-]+", "", rest)
    if rest.upper().startswith("C") and len(rest) > 1 and not rest[1].isdigit():
        # "@600 CNi…" 잔여 C 제거 (온도 C 가 rest 로 남은 경우)
        if temp:
            rest = rest[1:].lstrip()

    core = f"{date} {rxn}({conc})"
    if temp:
        core = f"{core}@{temp}C"
    if rest:
        return f"{core} {rest}".strip()
    return core


class InvalidSampleNameError(ValueError):
    pass


def sanitize_sample_name(raw: str) -> str:
    """
    KCH 엑셀 파일명에 쓸 시료명.

    Windows 파일명 불가 문자는 제거하고, ``/`` 만 ``-`` 로 치환한다.
    (사용자가 슬래시로 구분한 이름은 하이픈으로 보존)
    """
    name = str(raw).strip()
    if not name:
        raise InvalidSampleNameError('sample_name is empty')
    name = name.replace('/', '-')
    name = _WIN_INVALID_CHARS.sub('', name)
    while '..' in name:
        name = name.replace('..', '')
    name = name.rstrip('. ')
    if not name:
        raise InvalidSampleNameError('sample_name is empty after sanitize')
    if len(name) > MAX_SAMPLE_NAME_LEN:
        name = name[:MAX_SAMPLE_NAME_LEN]
    return name


def sanitize_seq_date(raw: str) -> str:
    date_tag = str(raw).strip()
    if not _SEQ_DATE_RE.match(date_tag):
        raise InvalidSampleNameError(f'invalid seq_date: {raw!r}')
    return date_tag


def ensure_path_under_dir(base_dir: str, target_path: str) -> str:
    base = os.path.normpath(os.path.abspath(base_dir))
    target = os.path.normpath(os.path.abspath(target_path))
    try:
        common = os.path.commonpath([base, target])
    except ValueError:
        raise InvalidSampleNameError(f'output path escapes base directory: {target_path}') from None
    if common != base:
        raise InvalidSampleNameError(f'output path escapes base directory: {target_path}')
    return target


class InvalidSequenceFolderError(ValueError):
    pass


def validate_sequence_folder(sequence_folder: str, data_path: str) -> str:
    """ChemStation Data 루트 하위 시퀀스 폴더만 허용."""
    if not sequence_folder or not str(sequence_folder).strip():
        raise InvalidSequenceFolderError('sequence_folder is empty')
    folder = os.path.normpath(os.path.abspath(sequence_folder.strip()))
    base = os.path.normpath(os.path.abspath(data_path))
    if not os.path.isdir(base):
        raise InvalidSequenceFolderError(f'ChemStation data path missing: {data_path}')
    if not os.path.isdir(folder):
        raise InvalidSequenceFolderError(f'sequence folder not found: {sequence_folder}')
    try:
        common = os.path.commonpath([base, folder])
    except ValueError:
        raise InvalidSequenceFolderError(
            f'sequence folder must be under ChemStation data path: {data_path}'
        ) from None
    if common != base:
        raise InvalidSequenceFolderError(
            f'sequence folder must be under ChemStation data path: {data_path}'
        )
    return folder


def build_safe_output_filename(excel_output_dir: str, sample_name: str, seq_date: str = "") -> str:
    """엑셀 파일명 = 시료명만 (날짜 접두 없음). ``seq_date`` 는 검증만 하고 경로에 쓰지 않음."""
    safe_name = sanitize_sample_name(sample_name)
    if seq_date and str(seq_date).strip():
        sanitize_seq_date(seq_date)
    path = os.path.join(excel_output_dir, f"{safe_name}.xlsx")
    return ensure_path_under_dir(excel_output_dir, path)
