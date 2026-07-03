# -*- coding: utf-8 -*-
"""extract_gc1_rt_from_xlsx.py — GC1 KCH xlsx 에서 피크 RT(분) 요약 (Step 7.2)

**GC1 장비 PC**에서 gc_automation.py 가 만든 FID/TCD 2시트 xlsx 를 읽습니다.
PASS/FAIL 검증은 ``scripts/validate_gc1_rt.py`` (T82).

Usage:
  python scripts/extract_gc1_rt_from_xlsx.py "path\\to\\file.xlsx"
  python scripts/validate_gc1_rt.py "path\\to\\file.xlsx"   # ±0.1분 검증
"""
from __future__ import annotations

import argparse
import os
import sys

_REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _REPO not in sys.path:
    sys.path.insert(0, _REPO)

from gc1_rt_validate import extract_rt_summaries  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description="GC1 KCH xlsx RT summary (Step 7.2)")
    parser.add_argument("xlsx", help="GC1 KCH original xlsx path")
    parser.add_argument("--sheet", action="append", help="Sheet name (default: FID and TCD)")
    args = parser.parse_args()

    path = os.path.abspath(args.xlsx)
    if not os.path.isfile(path):
        print(f"[오류] 파일 없음: {path}", file=sys.stderr)
        return 1

    summaries = extract_rt_summaries(path, sheets=args.sheet)
    print(f"=== GC1 RT summary: {os.path.basename(path)} ===\n")
    if not summaries:
        print("피크를 찾지 못했습니다. FID/TCD 시트·Time/Area 열을 확인하세요.")
        return 1

    for r in sorted(summaries, key=lambda x: (x.detector, x.gas)):
        lo, hi = r.ref_window
        print(
            f"[{r.sheet}] {r.gas:5s}  n={r.count:3d}  "
            f"RT mean={r.rt_mean:.3f}  min={r.rt_min:.3f}  max={r.rt_max:.3f}  "
            f"ref=({lo:.2f}-{hi:.2f})"
        )

    print("\n→ validate: python scripts/validate_gc1_rt.py", repr(path))
    print("→ deploy/STEP7_gc1_calib.md Step 7.2: ref 와 0.1분 이상 차이면 GC1_TIME_* 수정")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
