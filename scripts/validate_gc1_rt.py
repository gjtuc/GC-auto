# -*- coding: utf-8 -*-
"""validate_gc1_rt.py — GC1 RT 검증 CLI (T82 / Step 7.2)

Usage:
  python scripts/validate_gc1_rt.py --sync-check
  python scripts/validate_gc1_rt.py "path\\to\\GC1_KCH.xlsx"
  python scripts/validate_gc1_rt.py "file.xlsx" --tolerance 0.15
"""
from __future__ import annotations

import argparse
import os
import sys

_REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _REPO not in sys.path:
    sys.path.insert(0, _REPO)

from gc1_rt_validate import (  # noqa: E402
    DEFAULT_RT_TOLERANCE_MIN,
    extract_rt_summaries,
    validate_rt_summaries,
    verify_repo_rt_sync,
)


def _print_summaries(summaries) -> None:
    for r in sorted(summaries, key=lambda x: (x.detector, x.gas)):
        lo, hi = r.ref_window
        print(
            f"[{r.sheet or r.detector}] {r.gas:5s}  n={r.count:3d}  "
            f"RT mean={r.rt_mean:.3f}  ref_center={r.ref_center:.2f}  "
            f"window=({lo:.2f}-{hi:.2f})"
        )


def main() -> int:
    parser = argparse.ArgumentParser(
        description="GC1 RT validation — repo sync + xlsx vs STEP7 reference",
    )
    parser.add_argument("xlsx", nargs="?", help="GC1 KCH original xlsx (optional with --sync-check)")
    parser.add_argument(
        "--sync-check",
        action="store_true",
        help="gc_gc1 · data_pc GC1_TIME_* · GC1_RT_REFERENCE 일치만 검사 (xlsx 불필요)",
    )
    parser.add_argument(
        "--tolerance",
        type=float,
        default=DEFAULT_RT_TOLERANCE_MIN,
        help=f"기준 중심 RT 허용 편차(분), 기본 {DEFAULT_RT_TOLERANCE_MIN}",
    )
    parser.add_argument("--sheet", action="append", help="시트 이름 (반복 가능, 기본 FID+TCD)")
    args = parser.parse_args()

    if args.sync_check or not args.xlsx:
        sync = verify_repo_rt_sync()
        if sync.ok:
            print("[OK] repo RT windows in sync (gc_gc1 · data_pc GC1_TIME_*)")
        else:
            print("[FAIL] repo RT window mismatch:")
            for line in sync.mismatches:
                print(f"  - {line}")
        if not args.xlsx:
            return 0 if sync.ok else 1

    path = os.path.abspath(args.xlsx)
    if not os.path.isfile(path):
        print(f"[오류] 파일 없음: {path}", file=sys.stderr)
        return 1

    print(f"=== GC1 RT validate: {os.path.basename(path)} (±{args.tolerance} min) ===\n")
    summaries = extract_rt_summaries(path, sheets=args.sheet)
    if not summaries:
        print("[FAIL] 피크 요약 없음 — FID/TCD·Time·분석된 원소 열 확인")
        return 1

    _print_summaries(summaries)
    result = validate_rt_summaries(summaries, tolerance_min=args.tolerance)
    print()
    if result.ok:
        print("[PASS] RT within tolerance - deploy/STEP7_gc1_calib.md 7.2")
        return 0

    print("[FAIL] RT validation:")
    for issue in result.issues:
        print(f"  - {issue.message}")
    print("\n-> GC1_TIME_TCD / GC1_TIME_FID or gc_gc1 DEFAULT_*_WINDOWS update")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
