# -*- coding: utf-8 -*-
"""validate_gc1_mod_slots.py — MOD 슬롯 JSON 검증 CLI (T70)

Usage:
  python scripts/validate_gc1_mod_slots.py
  python scripts/validate_gc1_mod_slots.py --json deploy/gc1_mod_slots.json
"""
from __future__ import annotations

import argparse
import os
import sys

_REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _REPO not in sys.path:
    sys.path.insert(0, _REPO)

from gc1_runtime.mod_registry import (  # noqa: E402
    DEFAULT_MOD_SLOTS_PATH,
    load_mod_slots,
    pending_slots,
    ready_for_impl,
    validate_mod_registry,
)


def main() -> int:
    parser = argparse.ArgumentParser(description="GC1 MOD slot registry validation")
    parser.add_argument("--json", default=DEFAULT_MOD_SLOTS_PATH, help="gc1_mod_slots.json path")
    args = parser.parse_args()

    path = os.path.abspath(args.json)
    if not os.path.isfile(path):
        print(f"[FAIL] not found: {path}", file=sys.stderr)
        return 1

    slots = load_mod_slots(path)
    result = validate_mod_registry(slots)

    print(f"=== MOD registry: {os.path.basename(path)} ({len(slots)} slots) ===\n")
    for slot in slots:
        flag = "READY" if slot.is_ready_for_impl else slot.status.upper()
        print(f"  {slot.mod_id}  [{flag}]  task={slot.queue_task}")
        if slot.title:
            print(f"    title: {slot.title}")
        if slot.leaf_ids:
            print(f"    leaf_ids: {', '.join(slot.leaf_ids)}")

    pending = pending_slots(slots)
    ready = ready_for_impl(slots)
    print(f"\npending (no content): {len(pending)}")
    print(f"ready for atom impl: {len(ready)}")

    for w in result.warnings:
        print(f"[WARN] {w}")
    for e in result.errors:
        print(f"[FAIL] {e}")

    if result.ok:
        print("\n[OK] mod registry schema valid")
        return 0
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
