# -*- coding: utf-8 -*-
"""run_gc1_mod_pipeline.py — MOD T70~T86 일괄 점검 (T87)

Usage:
  python scripts/run_gc1_mod_pipeline.py
  python scripts/run_gc1_mod_pipeline.py --json deploy/gc1_mod_slots.json
  python scripts/run_gc1_mod_pipeline.py --no-apply-plan
"""
from __future__ import annotations

import argparse
import os
import sys

_REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _REPO not in sys.path:
    sys.path.insert(0, _REPO)

from gc1_runtime.mod_pipeline import run_mod_pipeline  # noqa: E402
from gc1_runtime.mod_registry import DEFAULT_MOD_SLOTS_PATH  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description="GC1 MOD pipeline check (no atom patch)")
    parser.add_argument("--json", default=DEFAULT_MOD_SLOTS_PATH)
    parser.add_argument(
        "--no-apply-plan",
        action="store_true",
        help="Skip apply plan step (validate + summary only)",
    )
    args = parser.parse_args()

    path = os.path.abspath(args.json)
    if not os.path.isfile(path):
        print(f"[FAIL] not found: {path}", file=sys.stderr)
        return 1

    report = run_mod_pipeline(path, run_apply_plan=not args.no_apply_plan)

    print(f"=== MOD pipeline: {os.path.basename(path)} ===\n")
    for step in report.steps:
        mark = "OK" if step.ok else "FAIL"
        print(f"  [{mark}] {step.name}: {step.detail}")

    if report.ready_mod_ids:
        print(f"\nready: {', '.join(report.ready_mod_ids)}")
    if report.pending_mod_ids:
        print(f"pending: {', '.join(report.pending_mod_ids)}")
    if report.implemented_mod_ids:
        print(f"implemented: {', '.join(report.implemented_mod_ids)}")

    if report.hints:
        print("\nhints:")
        for h in report.hints:
            print(f"  - {h}")

    print()
    if report.ok:
        print("[PASS] MOD pipeline check")
        return 0
    print("[FAIL] MOD pipeline check")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
