# -*- coding: utf-8 -*-
"""apply_gc1_mod.py — MOD ready 슬롯 → atom 구현 계획 (T71 dry-run)

Usage:
  python scripts/apply_gc1_mod.py --dry-run
  python scripts/apply_gc1_mod.py --dry-run --mod MOD-2
  python scripts/apply_gc1_mod.py --dry-run --json deploy/gc1_mod_slots.json
"""
from __future__ import annotations

import argparse
import os
import sys

_REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _REPO not in sys.path:
    sys.path.insert(0, _REPO)

from gc1_runtime.mod_apply import plan_from_json  # noqa: E402
from gc1_runtime.mod_registry import DEFAULT_MOD_SLOTS_PATH, get_slot, load_mod_slots  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(
        description="GC1 MOD apply plan (dry-run — no atom code changes)",
    )
    parser.add_argument("--json", default=DEFAULT_MOD_SLOTS_PATH)
    parser.add_argument("--mod", help="Single MOD-ID (e.g. MOD-2)")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print implementation plan only (default behaviour)",
    )
    args = parser.parse_args()

    path = os.path.abspath(args.json)
    if not os.path.isfile(path):
        print(f"[FAIL] not found: {path}", file=sys.stderr)
        return 1

    if args.mod:
        slots = load_mod_slots(path)
        slot = get_slot(slots, args.mod)
        if slot is None:
            print(f"[FAIL] unknown mod_id: {args.mod}", file=sys.stderr)
            return 1
        if slot.status != "ready" and not slot.is_ready_for_impl:
            print(f"[SKIP] {args.mod}: not ready (fill title/summary/leaf_ids, set status=ready)")
            return 0

    result = plan_from_json(path)

    if args.mod:
        result.plans = [p for p in result.plans if p.mod_id == args.mod]

    print(f"=== MOD apply dry-run: {os.path.basename(path)} ===\n")
    if not result.plans:
        print(f"[SKIP] no ready MOD plans (pending slots: {result.skipped_pending})")
        print("       Fill deploy/gc1_mod_slots.json then: validate_gc1_mod_slots.py")
        return 0 if not result.errors else 1

    for plan in result.plans:
        print(f"[PLAN] {plan.mod_id}: {plan.title}")
        print(f"  summary: {plan.summary}")
        print(f"  atoms:   {', '.join(plan.atom_ids)}")
        print(f"  phases:  {', '.join(plan.phases)}")
        for note in plan.notes:
            print(f"  note:    {note}")
        print()

    for err in result.errors:
        print(f"[FAIL] {err}")

    if result.ok:
        print("[OK] all ready MOD plans valid (implement atoms in layer4_* next)")
        return 0
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
