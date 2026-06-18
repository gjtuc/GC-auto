# -*- coding: utf-8 -*-
"""suggest_gc1_calib.py — GC1 CALIB 계수 제안 (Step 7.3)

GC1은 GC3와 같이 ppm = Area / CALIB (나눗셈). 표준가스 1주입으로 CALIB 를 산출합니다.

Usage:
  python scripts/suggest_gc1_calib.py "file.xlsx" --gas H2 --ppm 50000 --cycle 1
  python scripts/suggest_gc1_calib.py "file.xlsx" --gas CH4 --ppm 10000 --sheet FID
"""
from __future__ import annotations

import argparse
import os
import re
import sys

import pandas as pd

# extract_gc1_rt_from_xlsx 와 동일
GC1_RT_REFERENCE = {
    "TCD": {"H2": (2.0, 0.35), "CO": (6.6, 0.8), "CO2": (16.2, 1.2)},
    "FID": {"CH4": (1.4, 0.35), "C2H6": (1.9, 0.35), "C2H4": (2.3, 0.35)},
}
TCD_GASES = frozenset({"H2", "CO", "CO2"})
FID_GASES = frozenset({"CH4", "C2H6", "C2H4"})


def _window(center: float, half: float) -> tuple[float, float]:
    return (center - half, center + half)


def _default_sheet(gas: str) -> str:
    return "TCD" if gas in TCD_GASES else "FID"


def _parse_cycles(df: pd.DataFrame) -> dict[int, pd.DataFrame]:
    """# 행 또는 문자 Time 행으로 사이클 분리 (촉매 반응 계산.py 와 유사)."""
    if df.empty:
        return {}
    df = df.copy()
    df.columns = df.columns.astype(str).str.strip()
    cycle = 1
    chunks: dict[int, list] = {1: []}
    for _, row in df.iterrows():
        t0 = str(row.iloc[0]) if len(row) else ""
        if t0.startswith("#") or (str(row.get("Time", "")).isalpha()):
            cycle += 1
            chunks.setdefault(cycle, [])
            continue
        chunks.setdefault(cycle, []).append(row)
    return {c: pd.DataFrame(rows) for c, rows in chunks.items() if rows}


def _find_area(df: pd.DataFrame, gas: str, bounds: tuple[float, float]) -> float | None:
    lo, hi = bounds
    best = None
    for _, row in df.iterrows():
        try:
            t = float(row["Time"])
            a = float(row["Area"])
        except (TypeError, ValueError):
            continue
        elem = str(row.get("분석된 원소", "") or "").strip().upper()
        if elem:
            for g in ("C2H6", "C2H4", "CO2", "CH4", "H2", "CO"):
                if elem == g:
                    return a
        if lo <= t <= hi:
            best = a
    return best


def main() -> int:
    parser = argparse.ArgumentParser(description="Suggest GC1 CALIB = Area / ppm")
    parser.add_argument("xlsx", help="GC1 KCH xlsx (standard gas or known feed)")
    parser.add_argument("--gas", required=True, choices=sorted(TCD_GASES | FID_GASES))
    parser.add_argument("--ppm", type=float, required=True, help="Known concentration (ppm)")
    parser.add_argument("--cycle", type=int, default=1, help="Injection cycle (1-based)")
    parser.add_argument("--sheet", help="FID or TCD (default: auto by gas)")
    args = parser.parse_args()

    path = os.path.abspath(args.xlsx)
    if not os.path.isfile(path):
        print(f"[오류] 파일 없음: {path}", file=sys.stderr)
        return 1
    if args.ppm <= 0:
        print("[오류] --ppm 은 양수여야 합니다.", file=sys.stderr)
        return 1

    gas = args.gas.upper()
    sheet = (args.sheet or _default_sheet(gas)).upper()
    det = sheet if sheet in ("FID", "TCD") else _default_sheet(gas)
    ref = GC1_RT_REFERENCE.get(det, {}).get(gas)
    if not ref:
        print(f"[오류] {gas} 에 대한 RT 참조 없음", file=sys.stderr)
        return 1
    bounds = _window(ref[0], ref[1])

    df = pd.read_excel(path, sheet_name=sheet)
    cycles = _parse_cycles(df)
    if args.cycle not in cycles:
        print(f"[오류] cycle {args.cycle} 없음 (available: {sorted(cycles.keys())})", file=sys.stderr)
        return 1

    area = _find_area(cycles[args.cycle], gas, bounds)
    if area is None or area <= 0:
        print(f"[오류] cycle {args.cycle} 에서 {gas} Area 를 찾지 못함 (RT {bounds[0]:.2f}-{bounds[1]:.2f})", file=sys.stderr)
        return 1

    calib = area / args.ppm
    print(f"=== GC1 CALIB suggestion ({gas}) ===")
    print(f"  file:   {os.path.basename(path)}")
    print(f"  sheet:  {sheet}  cycle: {args.cycle}")
    print(f"  Area:   {area:g}")
    print(f"  ppm:    {args.ppm:g}")
    print(f"  CALIB:  {calib:.6g}   # GC1_CALIB['{gas}'] = Area / ppm")
    print(f"  check:  ppm_calc = Area / CALIB = {area / calib:g}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
