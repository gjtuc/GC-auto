# -*- coding: utf-8 -*-
"""intake_gc1_mod.py — MOD 슬롯에 사용자 수정사항 기록 (T86)

Usage:
  python scripts/intake_gc1_mod.py --mod MOD-1 --title "..." --summary "..." --leaf "Ω.A.L4.P3.06"
  python scripts/intake_gc1_mod.py --mod MOD-2 --title "t" --summary "s" --leaf "Ω.A.L4.P4.08" --atom "Ω.A.L4.P4.08"
  python scripts/intake_gc1_mod.py --mod MOD-3 --status blocked --title "보류" --summary "나중에" --leaf "Ω.A.L4.P1.01"
"""
from __future__ import annotations

import argparse
import os
import sys

_REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _REPO not in sys.path:
    sys.path.insert(0, _REPO)

from gc1_runtime.mod_intake import ModIntakeRequest, intake_mod_slot, parse_leaf_list  # noqa: E402
from gc1_runtime.mod_registry import DEFAULT_MOD_SLOTS_PATH  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description="Record user MOD into gc1_mod_slots.json")
    parser.add_argument("--mod", required=True, help="MOD-ID e.g. MOD-1")
    parser.add_argument("--title", required=True)
    parser.add_argument("--summary", required=True)
    parser.add_argument(
        "--leaf",
        action="append",
        default=[],
        help="Leaf ID (repeat or comma-separated)",
    )
    parser.add_argument("--atom", action="append", default=[], help="Atom ID (optional)")
    parser.add_argument(
        "--status",
        default="ready",
        choices=("pending", "ready", "blocked"),
    )
    parser.add_argument("--r-change", action="store_true", help="Rule R change flagged")
    parser.add_argument("--json", default=DEFAULT_MOD_SLOTS_PATH)
    parser.add_argument(
        "--no-plan-check",
        action="store_true",
        help="Skip P0_P9 atom registry plan check",
    )
    args = parser.parse_args()

    path = os.path.abspath(args.json)
    if not os.path.isfile(path):
        print(f"[FAIL] not found: {path}", file=sys.stderr)
        return 1

    leaf_ids = parse_leaf_list(args.leaf)
    if not leaf_ids and args.status != "blocked":
        print("[FAIL] at least one --leaf required (unless --status blocked)", file=sys.stderr)
        return 1

    req = ModIntakeRequest(
        mod_id=args.mod,
        title=args.title,
        summary=args.summary,
        leaf_ids=leaf_ids,
        atom_ids=parse_leaf_list(args.atom),
        status=args.status,
        r_change=args.r_change,
    )
    result = intake_mod_slot(req, path, verify_plan=not args.no_plan_check)
    if not result.ok:
        print(f"[FAIL] {result.mod_id}: {result.message}", file=sys.stderr)
        for err in result.validation_errors:
            print(f"  - {err}", file=sys.stderr)
        return 1

    print(f"[OK] {result.mod_id} saved to {path}")
    if result.plan_atom_count:
        print(f"     apply plan: {result.plan_atom_count} atom(s) - run apply_gc1_mod.py --dry-run")
    print("     next: atom patch in layer4_* then close_gc1_mod.py")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
