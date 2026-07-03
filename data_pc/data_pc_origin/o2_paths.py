# -*- coding: utf-8 -*-
"""O2 — KCH 경로·락 파일 경로."""

from __future__ import annotations

from pathlib import Path

_PACKAGE_DIR = Path(__file__).resolve().parent
DEFAULT_KCH_DIR = _PACKAGE_DIR.parent / "KCH"


def kch_dir() -> Path:
    return DEFAULT_KCH_DIR


def pipeline_lock_path(base: Path | None = None) -> str:
    root = base if base is not None else kch_dir()
    return str(root / ".data_pc_pipeline.lock")


def origin_lock_path(base: Path | None = None) -> str:
    root = base if base is not None else kch_dir()
    return str(root / ".origin_update.lock")
