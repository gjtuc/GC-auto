# -*- coding: utf-8 -*-
"""validate_gc1_resume_policy.py — PART6 Resume 정책 검증 CLI (T93)

Usage (repo 루트):
  python scripts/validate_gc1_resume_policy.py

Exit: 0 = PASS, 1 = FAIL
"""
from __future__ import annotations

import argparse
import os
import sys

_REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _REPO not in sys.path:
    sys.path.insert(0, _REPO)

from gc1_runtime.layer0_resume import (  # noqa: E402
    DEFAULT_RESUME_POLICY_PATH,
    atoms_before_resume,
    load_resume_policy,
    validate_resume_policy,
)
from gc1_runtime.layer4_atoms_p8_p9 import P0_P9_ATOM_IDS  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description="GC1 PART6 resume policy validation")
    parser.add_argument("--json", default=DEFAULT_RESUME_POLICY_PATH)
    args = parser.parse_args()

    path = os.path.abspath(args.json)
    if not os.path.isfile(path):
        print(f"[FAIL] not found: {path}", file=sys.stderr)
        return 1

    doc = load_resume_policy(path)
    result = validate_resume_policy(doc, P0_P9_ATOM_IDS)

    print(f"=== PART6 resume policy: {os.path.basename(path)} ===")
    print(f"  schema_version : {doc.schema_version}")
    print(f"  rules          : {len(doc.rules)}")
    print(f"  P0_P9 atoms    : {len(P0_P9_ATOM_IDS)}\n")

    for rule in doc.rules:
        skipped = atoms_before_resume(rule.resume_from, P0_P9_ATOM_IDS)
        print(f"  {rule.resume_from}")
        print(f"    skip {len(skipped)} atoms - {rule.description}")

    if result.warnings:
        print("\n[WARN]")
        for w in result.warnings:
            print(f"  - {w}")

    if result.errors:
        print("\n[FAIL]")
        for e in result.errors:
            print(f"  - {e}")
        return 1

    print("\n[PASS] resume policy OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
