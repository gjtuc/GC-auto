# -*- coding: utf-8 -*-
"""close_gc1_mod.py — atom 패치 완료 후 MOD status=implemented (T72)

Usage:
  python scripts/close_gc1_mod.py --mod MOD-3
  python scripts/close_gc1_mod.py --mod MOD-3 --json path/to/gc1_mod_slots.json
"""
from __future__ import annotations

import argparse
import os
import sys

_REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _REPO not in sys.path:
    sys.path.insert(0, _REPO)

from gc1_runtime.mod_lifecycle import mark_implemented  # noqa: E402
from gc1_runtime.mod_registry import DEFAULT_MOD_SLOTS_PATH  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Mark MOD slot implemented after atom patch",
    )
    parser.add_argument("--mod", required=True, help="MOD-ID e.g. MOD-3")
    parser.add_argument("--json", default=DEFAULT_MOD_SLOTS_PATH)
    args = parser.parse_args()

    path = os.path.abspath(args.json)
    if not os.path.isfile(path):
        print(f"[FAIL] not found: {path}", file=sys.stderr)
        return 1

    result = mark_implemented(args.mod, path)
    if result.ok:
        print(f"[OK] {result.mod_id}: {result.old_status} -> {result.new_status}")
        return 0
    print(f"[FAIL] {result.mod_id}: {result.message}", file=sys.stderr)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
