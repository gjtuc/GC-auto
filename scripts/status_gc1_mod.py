# -*- coding: utf-8 -*-
"""status_gc1_mod.py — MOD 슬롯·큐 요약 (T72)

Usage:
  python scripts/status_gc1_mod.py
  python scripts/status_gc1_mod.py --json deploy/gc1_mod_slots.json
"""
from __future__ import annotations

import argparse
import os
import sys

_REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _REPO not in sys.path:
    sys.path.insert(0, _REPO)

from gc1_runtime.mod_lifecycle import (  # noqa: E402
    all_user_mods_resolved,
    load_queue_summary,
)
from gc1_runtime.mod_registry import (  # noqa: E402
    DEFAULT_MOD_SLOTS_PATH,
    load_mod_slots,
    validate_mod_registry,
)


def main() -> int:
    parser = argparse.ArgumentParser(description="GC1 MOD slot queue status")
    parser.add_argument("--json", default=DEFAULT_MOD_SLOTS_PATH)
    args = parser.parse_args()

    path = os.path.abspath(args.json)
    if not os.path.isfile(path):
        print(f"[FAIL] not found: {path}", file=sys.stderr)
        return 1

    slots = load_mod_slots(path)
    validation = validate_mod_registry(slots)
    summary = load_queue_summary(path)

    print(f"=== MOD queue status: {os.path.basename(path)} ===\n")
    for slot in slots:
        extra = ""
        if slot.is_ready_for_impl and slot.status != "implemented":
            extra = " [content filled]"
        print(f"  {slot.mod_id}  {slot.status:11s}  task={slot.queue_task}{extra}")
        if slot.title:
            print(f"    title: {slot.title}")

    print(f"\ntotal={summary.total}  pending={summary.pending}  ready={summary.ready}")
    print(f"implemented={summary.implemented}  blocked={summary.blocked}")
    print(f"awaiting_user_text={summary.awaiting_user}")
    print(f"ready_for_atom_patch={summary.ready_for_atom_patch}")

    resolved = all_user_mods_resolved(slots)
    if resolved:
        print("\n[OK] all MOD slots resolved (implemented or blocked)")
    else:
        print("\n[WAIT] user MOD text or atom implementation still needed")

    if not validation.ok:
        for e in validation.errors:
            print(f"[FAIL] {e}")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
