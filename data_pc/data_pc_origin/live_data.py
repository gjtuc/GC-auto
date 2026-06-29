# -*- coding: utf-8
"""Live E2E — opju 폴더 companion xlsx → df · sample_name (O1→O9 bridge)."""

from __future__ import annotations

import importlib.util
import os
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
    """opju 와 같은 폴더의 계산 xlsx (임시 ~$ 제외, 최신 mtime)."""
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
    return str(max(candidates, key=lambda p: p.stat().st_mtime))


def resolve_live_job(opju_path: str, *, xlsx_path: Optional[str] = None) -> LiveJobContext:
    """실험 폴더 xlsx 로드 — 촉매 generate_sample_name / identity_key 재사용."""
    import pandas as pd

    xlsx = (xlsx_path or find_companion_xlsx(opju_path) or "").strip()
    if not xlsx or not os.path.isfile(xlsx):
        raise FileNotFoundError(f"companion xlsx not found for {opju_path!r}")

    catalyst = _load_catalyst_module()
    df = pd.read_excel(xlsx)
    eq = (
        catalyst.equipment_from_output_file(xlsx)
        if hasattr(catalyst, "equipment_from_output_file")
        else None
    )
    sn_result = catalyst.generate_sample_name(xlsx, equipment=eq)
    sample_name = sn_result[0] if isinstance(sn_result, tuple) else sn_result
    if not sample_name:
        raise ValueError(f"Origin Comments 해석 불가: {xlsx}")
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
