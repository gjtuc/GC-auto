# -*- coding: utf-8
"""P2 — Stage4 opju 경로 검증·저장 경로 (O1·O8 위임, originpro 금지)."""

from __future__ import annotations

from dataclasses import dataclass

from data_pc_origin.o0_types import ProbeResult
from data_pc_origin.o1_opju_path import normalize_g_path, probe_opju_path, probe_suffix_opju
from data_pc_origin.o8_save import resolve_save_path


@dataclass(frozen=True)
class Stage4Paths:
    """4단계 Origin open/save 경로."""

    source_opju: str
    save_path: str
    save_in_place: bool
    probe: ProbeResult


def normalize_opju_path(path: str) -> str:
    """G: 정규화 + strip (촉매 L2228–2230)."""
    return normalize_g_path((path or "").strip())


def is_g_drive_path(path: str) -> bool:
    norm = normalize_opju_path(path)
    return norm.startswith("G:")


def probe_stage4_opju(path: str) -> ProbeResult:
    """
    4단계 opju 사전 검사 — O1 `probe_opju_path` 위임.

    파일·G: root 검사는 live 환경에서만 PASS; 게이트는 suffix 등 순수 probe 병행.
    """
    norm = normalize_opju_path(path)
    return probe_opju_path(norm)


def probe_stage4_suffix(path: str) -> ProbeResult:
    """파일 없이 suffix 만 검사 (P2-P 게이트용)."""
    return probe_suffix_opju(normalize_opju_path(path))


def resolve_stage4_save_path(opju_path: str, save_in_place: bool) -> str:
    """O8 save — 촉매 `--opju` vs G: archive 분기."""
    return resolve_save_path(normalize_opju_path(opju_path), save_in_place)


def build_stage4_paths(opju_path: str, *, save_in_place: bool) -> Stage4Paths:
    """source · save · probe 한 번에."""
    source = normalize_opju_path(opju_path)
    probe = probe_stage4_opju(source)
    save = resolve_stage4_save_path(source, save_in_place)
    return Stage4Paths(
        source_opju=source,
        save_path=save,
        save_in_place=save_in_place,
        probe=probe,
    )
