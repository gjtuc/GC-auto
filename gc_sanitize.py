# -*- coding: utf-8 -*-
"""시료명·출력 경로 안전 검증 (path traversal 방지)."""
from __future__ import annotations

import os
import re

_WIN_INVALID_CHARS = re.compile(r'[<>:"\\|?*\x00-\x1f]')
_SEQ_DATE_RE = re.compile(r'^\d{8}$')
MAX_SAMPLE_NAME_LEN = 120


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


def build_safe_output_filename(excel_output_dir: str, sample_name: str, seq_date: str) -> str:
    safe_name = sanitize_sample_name(sample_name)
    safe_date = sanitize_seq_date(seq_date)
    path = os.path.join(excel_output_dir, f'{safe_date} {safe_name}.xlsx')
    return ensure_path_under_dir(excel_output_dir, path)
