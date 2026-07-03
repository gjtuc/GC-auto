# -*- coding: utf-8 -*-
"""O1 — .opju 경로 probe (읽기만, originpro import 금지)."""

from __future__ import annotations

import os
from pathlib import Path

from data_pc_origin.o0_types import ProbeResult
from data_pc_origin.o1_env import experiment_data_root


def normalize_g_path(path: str) -> str:
    """g: → G: 정규화."""
    text = path.strip()
    if len(text) >= 2 and text[0].lower() == "g" and text[1] == ":":
        return "G:" + text[2:]
    return text


def probe_path_nonempty(path: str) -> ProbeResult:
    if not (path or "").strip():
        return ProbeResult(False, "path empty", "P01")
    return ProbeResult(True, "ok", "P01")


def probe_path_exists(path: str) -> ProbeResult:
    if os.path.islink(path) and not os.path.exists(path):
        return ProbeResult(False, "broken symlink", "P02")
    if not os.path.isfile(path):
        return ProbeResult(False, "file not found", "P02")
    return ProbeResult(True, "ok", "P02")


def probe_path_is_file(path: str) -> ProbeResult:
    if os.path.isdir(path):
        return ProbeResult(False, "path is directory", "P03")
    return ProbeResult(True, "ok", "P03")


def probe_suffix_opju(path: str) -> ProbeResult:
    suffix = Path(path).suffix.lower()
    if suffix != ".opju":
        return ProbeResult(False, f"invalid suffix {suffix!r}", "P04")
    return ProbeResult(True, "ok", "P04")


def probe_on_g_drive(path: str) -> ProbeResult:
    norm = normalize_g_path(path)
    if not norm.startswith("G:"):
        return ProbeResult(False, "not on G: drive", "P05")
    return ProbeResult(True, "ok", "P05")


def probe_g_drive_root_accessible() -> ProbeResult:
    root = experiment_data_root()
    try:
        ok = os.path.isdir(root)
    except OSError as exc:
        return ProbeResult(False, f"G: root error: {root} ({exc})", "P06")
    if not ok:
        return ProbeResult(False, f"G: root not accessible: {root}", "P06")
    return ProbeResult(True, "ok", "P06")


def probe_opju_path(path: str) -> ProbeResult:
    """P01→P06 순서; 첫 실패 반환."""
    steps = (
        probe_path_nonempty,
        probe_path_exists,
        probe_path_is_file,
        probe_suffix_opju,
        probe_on_g_drive,
    )
    for step in steps:
        result = step(path)
        if not result.ok:
            return result
    root = probe_g_drive_root_accessible()
    if not root.ok:
        return root
    return ProbeResult(True, "", "")
