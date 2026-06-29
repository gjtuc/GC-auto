# -*- coding: utf-8
"""Live E2E — opju 폴더 companion xlsx → df · sample_name (O1→O9 bridge)."""

from __future__ import annotations

import importlib.util
import os
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Optional, Tuple

IdentityKey = Tuple[str, str]


@dataclass(frozen=True)
class LiveJobContext:
    opju_path: str
    xlsx_path: str
    sample_name: str
    identity_key: IdentityKey
    df: Any
    row_count: int
    columns: tuple[str, ...]


def _load_catalyst_module():
    root = Path(__file__).resolve().parent.parent
    path = root / "촉매 반응 계산.py"
    spec = importlib.util.spec_from_file_location("catalyst_calc", path)
    if spec is None or spec.loader is None:
        raise ImportError(f"cannot load {path}")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def find_companion_xlsx(opju_path: str) -> Optional[str]:
    """opju 와 같은 폴더의 계산 xlsx (임시 ~$ 제외, 장비 토큰 우선 · 최신 mtime)."""
    folder = Path(opju_path).parent
    if not folder.is_dir():
        return None
    candidates: list[Path] = []
    for p in folder.glob("*.xlsx"):
        if p.name.startswith("~$"):
            continue
        candidates.append(p)
    if not candidates:
        return None

    def _sort_key(p: Path) -> tuple[int, float]:
        # _GC2_/_GC3_ 계산완료 파일 우선 — equipment_from_output_file 용
        has_eq = 0 if re.search(r"_GC[123]_", p.name, re.I) else 1
        return (has_eq, -p.stat().st_mtime)

    return str(sorted(candidates, key=_sort_key)[0])


def _infer_equipment(catalyst: Any, opju_path: str, xlsx: str) -> Optional[str]:
    """
    Origin Comments 장비 접미사 — 파일명 _GC2_/_GC3_ → 폴더 내 형제 xlsx → env 기본값.

    companion xlsx 가 KCH stem 만 있을 때(장비 토큰 없음) DATA_PC_DEFAULT_EQUIPMENT 로 보완.
    """
    if hasattr(catalyst, "equipment_from_output_file"):
        eq = catalyst.equipment_from_output_file(xlsx)
        if eq:
            return eq
        folder = Path(opju_path).parent
        for p in sorted(folder.glob("*.xlsx"), key=lambda x: -x.stat().st_mtime):
            if p.name.startswith("~$"):
                continue
            eq = catalyst.equipment_from_output_file(str(p))
            if eq:
                return eq
    env = os.getenv("DATA_PC_DEFAULT_EQUIPMENT", "").strip().upper()
    if env in ("GC1", "GC2", "GC3"):
        return env
    return None


def resolve_live_job(opju_path: str, *, xlsx_path: Optional[str] = None) -> LiveJobContext:
    """실험 폴더 xlsx 로드 — 촉매 generate_sample_name / identity_key 재사용."""
    import pandas as pd

    xlsx = (xlsx_path or find_companion_xlsx(opju_path) or "").strip()
    if not xlsx or not os.path.isfile(xlsx):
        raise FileNotFoundError(f"companion xlsx not found for {opju_path!r}")

    catalyst = _load_catalyst_module()
    df = pd.read_excel(xlsx)
    eq = _infer_equipment(catalyst, opju_path, xlsx)
    sn_result = catalyst.generate_sample_name(xlsx, equipment=eq)
    sample_name = sn_result[0] if isinstance(sn_result, tuple) else sn_result
    needs_input = sn_result[2] if isinstance(sn_result, tuple) and len(sn_result) > 2 else False
    if not sample_name:
        detail = sn_result[3] if isinstance(sn_result, tuple) and len(sn_result) > 3 else ""
        raise ValueError(
            f"Origin Comments 해석 불가: {xlsx}"
            + (f" — {detail}" if detail else "")
            + ("" if eq else " (장비: DATA_PC_DEFAULT_EQUIPMENT=GC2|GC3)")
        )
    if needs_input:
        raise ValueError(f"Origin Comments 사용자 입력 필요: {xlsx}")
    identity_key = catalyst._experiment_identity_key(xlsx)
    cols = tuple(str(c) for c in df.columns)
    return LiveJobContext(
        opju_path=opju_path,
        xlsx_path=xlsx,
        sample_name=sample_name,
        identity_key=identity_key,
        df=df,
        row_count=len(df),
        columns=cols,
    )
