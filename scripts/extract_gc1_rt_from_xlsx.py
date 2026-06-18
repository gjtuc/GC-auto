# -*- coding: utf-8 -*-
"""extract_gc1_rt_from_xlsx.py — GC1 KCH xlsx 에서 피크 RT(분) 요약 (Step 7.2)

GC1 장비 PC에서 gc_automation.py 가 만든 FID/TCD 2시트 xlsx 를 읽어
각 성분 RT 분포를 출력합니다. gc_gc1.DEFAULT_*_WINDOWS 와 비교해 TIME 구간을 조정하세요.

Usage:
  python scripts/extract_gc1_rt_from_xlsx.py "path\\to\\file.xlsx"
  python scripts/extract_gc1_rt_from_xlsx.py "path\\to\\file.xlsx" --sheet TCD
"""
from __future__ import annotations

import argparse
import os
import sys

import pandas as pd

# gc_gc1.DEFAULT_*_WINDOWS 와 동기화 (center, half_width)
GC1_RT_REFERENCE = {
    "TCD": {
        "H2": (2.0, 0.35),
        "CO": (6.6, 0.8),
        "CO2": (16.2, 1.2),
    },
    "FID": {
        "CH4": (1.4, 0.35),
        "C2H6": (1.9, 0.35),
        "C2H4": (2.3, 0.35),
    },
}


def _window(center: float, half: float) -> tuple[float, float]:
    return (center - half, center + half)


def _load_sheet(path: str, sheet: str) -> pd.DataFrame:
    df = pd.read_excel(path, sheet_name=sheet)
    if df.empty:
        return df
    df.columns = df.columns.astype(str).str.strip()
    return df


def _assign_gas_by_rt(t: float, bounds: dict[str, tuple[float, float]]) -> str | None:
    for gas, (lo, hi) in bounds.items():
        if lo <= t <= hi:
            return gas
    return None


_GAS_MATCH_ORDER = ("C2H6", "C2H4", "CO2", "CH4", "H2", "CO")


def _assign_gas_by_element(row) -> str | None:
    col = row.get("분석된 원소") if hasattr(row, "get") else None
    if col is None or (isinstance(col, float) and pd.isna(col)):
        return None
    name = str(col).strip().upper()
    for gas in _GAS_MATCH_ORDER:
        if name == gas or name.endswith(gas) or name.startswith(gas + " "):
            return gas
    return None


def summarize_sheet(df: pd.DataFrame, detector: str) -> list[dict]:
    if df.empty or "Time" not in df.columns:
        return []
    ref = GC1_RT_REFERENCE.get(detector, {})
    bounds = {g: _window(c, h) for g, (c, h) in ref.items()}
    rows = []
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
        area = row.get("Area")
        rows.append({"gas": gas, "time": t, "area": area})
    if not rows:
        return []
    out = []
    rdf = pd.DataFrame(rows)
    for gas, grp in rdf.groupby("gas"):
        out.append({
            "detector": detector,
            "gas": gas,
            "count": len(grp),
            "rt_min": grp["time"].min(),
            "rt_max": grp["time"].max(),
            "rt_mean": grp["time"].mean(),
            "ref_window": bounds.get(gas),
        })
    return out


def main() -> int:
    parser = argparse.ArgumentParser(description="GC1 KCH xlsx RT summary (Step 7.2)")
    parser.add_argument("xlsx", help="GC1 KCH original xlsx path")
    parser.add_argument("--sheet", action="append", help="Sheet name (default: FID and TCD)")
    args = parser.parse_args()

    path = os.path.abspath(args.xlsx)
    if not os.path.isfile(path):
        print(f"[오류] 파일 없음: {path}", file=sys.stderr)
        return 1

    xls = pd.ExcelFile(path)
    sheets = args.sheet or [s for s in xls.sheet_names if s.upper() in ("FID", "TCD")]
    if not sheets:
        sheets = xls.sheet_names

    print(f"=== GC1 RT summary: {os.path.basename(path)} ===\n")
    all_rows = []
    for sn in sheets:
        det = sn.upper() if sn.upper() in ("FID", "TCD") else sn
        df = _load_sheet(path, sn)
        rows = summarize_sheet(df, det if det in GC1_RT_REFERENCE else "TCD")
        for r in rows:
            r["sheet"] = sn
            all_rows.append(r)

    if not all_rows:
        print("피크를 찾지 못했습니다. FID/TCD 시트·Time/Area 열을 확인하세요.")
        return 1

    for r in sorted(all_rows, key=lambda x: (x["detector"], x["gas"])):
        lo, hi = r["ref_window"] or (None, None)
        print(
            f"[{r['sheet']}] {r['gas']:5s}  n={r['count']:3d}  "
            f"RT mean={r['rt_mean']:.3f}  min={r['rt_min']:.3f}  max={r['rt_max']:.3f}  "
            f"ref=({lo:.2f}-{hi:.2f})" if lo is not None else f"[{r['sheet']}] {r['gas']}"
        )

    print("\n→ deploy/STEP7_gc1_calib.md Step 7.2: ref 와 0.1분 이상 차이면 GC1_TIME_* 수정")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
