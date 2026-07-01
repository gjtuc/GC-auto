# -*- coding: utf-8 -*-
"""validate_gc1_blocked_policy.py — PART6 BLOCKED 정책 검증 CLI (T96)

Usage (repo 루트):
  python scripts/validate_gc1_blocked_policy.py

Exit: 0 = PASS, 1 = FAIL
"""
from __future__ import annotations

import argparse
import os
import sys

_REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _REPO not in sys.path:
    sys.path.insert(0, _REPO)

from gc1_runtime.layer0_blocked import (  # noqa: E402
    DEFAULT_BLOCKED_POLICY_PATH,
    load_blocked_policy,
    validate_blocked_policy,
)


def main() -> int:
    parser = argparse.ArgumentParser(description="GC1 PART6 blocked policy validation")
    parser.add_argument("--json", default=DEFAULT_BLOCKED_POLICY_PATH)
    args = parser.parse_args()

    path = os.path.abspath(args.json)
    if not os.path.isfile(path):
        print(f"[FAIL] not found: {path}", file=sys.stderr)
        return 1

    doc = load_blocked_policy(path)
    result = validate_blocked_policy(doc)

    print(f"=== PART6 blocked policy: {os.path.basename(path)} ===")
    print(f"  schema_version : {doc.schema_version}")
    print(f"  hook_status    : {doc.hook_status}")
    print(f"  rules          : {len(doc.rules)}\n")

    for rule in doc.rules:
        print(f"  {rule.code}")
        print(f"    {rule.description}")
        if rule.step_ref:
            print(f"    step_ref: {rule.step_ref}")

    if result.warnings:
        print("\n[WARN]")
        for w in result.warnings:
            print(f"  - {w}")

    if result.errors:
        print("\n[FAIL]")
        for e in result.errors:
            print(f"  - {e}")
        return 1

    print("\n[PASS] blocked policy OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
