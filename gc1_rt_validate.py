# -*- coding: utf-8 -*-
"""
gc1_rt_validate.py — GC1 RT(분) 검증 라이브러리 (T82 / Step 7.2)

``gc_gc1.DEFAULT_*_WINDOWS`` · ``data_pc`` ``GC1_TIME_*`` · xlsx 실측 RT 를 한곳에서 검증.

정적: ``verify_repo_rt_sync()`` — repo 내 TIME 구간 일치
실행: ``validate_rt_summaries()`` — xlsx 요약 vs 기준 중심 RT (기본 ±0.1분)

CLI: ``scripts/validate_gc1_rt.py``
"""
from __future__ import annotations

import importlib.util
import os
import sys
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Sequence, Tuple

import pandas as pd

from gc_gc1 import DEFAULT_FID_WINDOWS, DEFAULT_TCD_WINDOWS

# (center_min, half_width) — gc_gc1.DEFAULT_*_WINDOWS 와 동기화
GC1_RT_REFERENCE: Dict[str, Dict[str, Tuple[float, float]]] = {
    "TCD": {gas: (center, half) for gas, center, half in DEFAULT_TCD_WINDOWS},
    "FID": {gas: (center, half) for gas, center, half in DEFAULT_FID_WINDOWS},
}

DEFAULT_RT_TOLERANCE_MIN = 0.1  # deploy/STEP7_gc1_calib.md §7.2

_GAS_MATCH_ORDER = ("C2H6", "C2H4", "CO2", "CH4", "H2", "CO")


@dataclass
class RtSummaryRow:
    """시트 1개·성분 1개 RT 요약."""

    detector: str
    gas: str
    count: int
    rt_min: float
    rt_max: float
    rt_mean: float
    ref_center: float
    ref_window: Tuple[float, float]
    sheet: str = ""


@dataclass
class RtValidationIssue:
    detector: str
    gas: str
    rt_mean: float
    ref_center: float
    delta_min: float
    tolerance_min: float
    message: str


@dataclass
class RtValidationResult:
    ok: bool
    summaries: List[RtSummaryRow] = field(default_factory=list)
    issues: List[RtValidationIssue] = field(default_factory=list)


@dataclass
class RepoRtSyncResult:
    """repo 내 TIME 구간 동기화 검사."""

    ok: bool
    mismatches: List[str] = field(default_factory=list)


def _window(center: float, half: float) -> Tuple[float, float]:
    return (center - half, center + half)


def _bounds_close(
    a: Tuple[float, float],
    b: Tuple[float, float],
    *,
    places: int = 2,
) -> bool:
    """부동소수 RT 구간 비교 — STEP7 표는 소수 둘째 자리."""
    return round(a[0], places) == round(b[0], places) and round(a[1], places) == round(b[1], places)


def windows_tuple_to_bounds(
    windows: Sequence[Tuple[str, float, float]],
) -> Dict[str, Tuple[float, float]]:
    return {gas: _window(center, half) for gas, center, half in windows}


def _load_catalyst_calc_module():
    repo = os.path.dirname(os.path.abspath(__file__))
    data_pc = os.path.join(repo, "data_pc")
    if data_pc not in sys.path:
        sys.path.insert(0, data_pc)
    path = os.path.join(data_pc, "촉매 반응 계산.py")
    spec = importlib.util.spec_from_file_location("catalyst_calc_rt", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load: {path}")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def verify_repo_rt_sync() -> RepoRtSyncResult:
    """
    정적 검증 — ``gc_gc1`` · ``GC1_RT_REFERENCE`` · ``data_pc`` ``GC1_TIME_*`` 일치.

    실측 xlsx 불필요 (GC8860·CI 에서 매번 실행 가능).
    """
    mismatches: List[str] = []
    fid_bounds = windows_tuple_to_bounds(DEFAULT_FID_WINDOWS)
    tcd_bounds = windows_tuple_to_bounds(DEFAULT_TCD_WINDOWS)

    for det, bounds in (("FID", fid_bounds), ("TCD", tcd_bounds)):
        ref = GC1_RT_REFERENCE.get(det, {})
        for gas, win in bounds.items():
            center, half = ref.get(gas, (None, None))
            if center is None:
                mismatches.append(f"GC1_RT_REFERENCE missing {det}/{gas}")
                continue
            if not _bounds_close(_window(center, half), win):
                mismatches.append(
                    f"GC1_RT_REFERENCE {det}/{gas} window {_window(center, half)} != gc_gc1 {win}"
                )

    try:
        calc = _load_catalyst_calc_module()
        for det, attr in (("TCD", "GC1_TIME_TCD"), ("FID", "GC1_TIME_FID")):
            time_map = getattr(calc, attr, {})
            gc_bounds = tcd_bounds if det == "TCD" else fid_bounds
            for gas, win in gc_bounds.items():
                calc_win = time_map.get(gas)
                if not _bounds_close(calc_win, win):
                    mismatches.append(
                        f"data_pc {attr}['{gas}']={calc_win} != gc_gc1 {win}"
                    )
    except Exception as exc:
        mismatches.append(f"data_pc GC1_TIME load: {exc}")

    return RepoRtSyncResult(ok=not mismatches, mismatches=mismatches)


def _load_sheet(path: str, sheet: str) -> pd.DataFrame:
    df = pd.read_excel(path, sheet_name=sheet)
    if df.empty:
        return df
    df.columns = df.columns.astype(str).str.strip()
    return df


def _assign_gas_by_rt(t: float, bounds: Dict[str, Tuple[float, float]]) -> Optional[str]:
    for gas, (lo, hi) in bounds.items():
        if lo <= t <= hi:
            return gas
    return None


def _assign_gas_by_element(row) -> Optional[str]:
    col = row.get("분석된 원소") if hasattr(row, "get") else None
    if col is None or (isinstance(col, float) and pd.isna(col)):
        return None
    name = str(col).strip().upper()
    for gas in _GAS_MATCH_ORDER:
        if name == gas or name.endswith(gas) or name.startswith(gas + " "):
            return gas
    return None


def summarize_sheet(df: pd.DataFrame, detector: str) -> List[RtSummaryRow]:
    """xlsx 시트 → 성분별 RT 요약 (extract 스크립트와 동일 로직)."""
    if df.empty or "Time" not in df.columns:
        return []
    ref = GC1_RT_REFERENCE.get(detector, {})
    bounds = {g: _window(c, h) for g, (c, h) in ref.items()}
    rows: List[dict] = []
    for _, row in df.iterrows():
        try:
            t = float(row["Time"])
        except (TypeError, ValueError):
            continue
        if pd.isna(t):
            continue
        gas = _assign_gas_by_element(row) or _assign_gas_by_rt(t, bounds)
        if not gas:
            continue
        rows.append({"gas": gas, "time": t})
    if not rows:
        return []
    out: List[RtSummaryRow] = []
    rdf = pd.DataFrame(rows)
    for gas, grp in rdf.groupby("gas"):
        center, half = ref[gas]
        out.append(
            RtSummaryRow(
                detector=detector,
                gas=gas,
                count=len(grp),
                rt_min=float(grp["time"].min()),
                rt_max=float(grp["time"].max()),
                rt_mean=float(grp["time"].mean()),
                ref_center=center,
                ref_window=bounds[gas],
            )
        )
    return out


def extract_rt_summaries(
    path: str,
    sheets: Optional[List[str]] = None,
) -> List[RtSummaryRow]:
    """GC1 KCH xlsx — FID/TCD 시트 RT 요약."""
    all_rows: List[RtSummaryRow] = []
    with pd.ExcelFile(path) as xls:
        use_sheets = sheets or [s for s in xls.sheet_names if s.upper() in ("FID", "TCD")]
        if not use_sheets:
            use_sheets = list(xls.sheet_names)
        for sn in use_sheets:
            det = sn.upper() if sn.upper() in ("FID", "TCD") else sn
            detector = det if det in GC1_RT_REFERENCE else "TCD"
            df = _load_sheet(path, sn)
            for row in summarize_sheet(df, detector):
                row.sheet = sn
                all_rows.append(row)
    return all_rows


def validate_rt_summaries(
    summaries: Sequence[RtSummaryRow],
    *,
    tolerance_min: float = DEFAULT_RT_TOLERANCE_MIN,
    require_all_gases: bool = False,
) -> RtValidationResult:
    """
    실행 검증 — RT mean 이 기준 중심에서 ``tolerance_min`` 분 초과 시 FAIL.

    ``require_all_gases=True`` 이면 FID 3종·TCD 3종 모두 요약에 있어야 PASS.
    """
    issues: List[RtValidationIssue] = []
    for row in summaries:
        delta = abs(row.rt_mean - row.ref_center)
        lo, hi = row.ref_window
        if delta > tolerance_min:
            issues.append(
                RtValidationIssue(
                    detector=row.detector,
                    gas=row.gas,
                    rt_mean=row.rt_mean,
                    ref_center=row.ref_center,
                    delta_min=delta,
                    tolerance_min=tolerance_min,
                    message=(
                        f"{row.detector}/{row.gas}: mean RT {row.rt_mean:.3f} vs ref "
                        f"{row.ref_center:.3f} (Δ={delta:.3f} > {tolerance_min})"
                    ),
                )
            )
        elif row.rt_mean < lo or row.rt_mean > hi:
            issues.append(
                RtValidationIssue(
                    detector=row.detector,
                    gas=row.gas,
                    rt_mean=row.rt_mean,
                    ref_center=row.ref_center,
                    delta_min=delta,
                    tolerance_min=tolerance_min,
                    message=(
                        f"{row.detector}/{row.gas}: mean RT {row.rt_mean:.3f} outside "
                        f"window ({lo:.2f}-{hi:.2f})"
                    ),
                )
            )

    if require_all_gases:
        expected = {("FID", g) for g in GC1_RT_REFERENCE["FID"]}
        expected |= {("TCD", g) for g in GC1_RT_REFERENCE["TCD"]}
        found = {(r.detector, r.gas) for r in summaries}
        for det, gas in sorted(expected - found):
            issues.append(
                RtValidationIssue(
                    detector=det,
                    gas=gas,
                    rt_mean=float("nan"),
                    ref_center=GC1_RT_REFERENCE[det][gas][0],
                    delta_min=float("nan"),
                    tolerance_min=tolerance_min,
                    message=f"missing peak summary for {det}/{gas}",
                )
            )

    return RtValidationResult(ok=not issues, summaries=list(summaries), issues=issues)
