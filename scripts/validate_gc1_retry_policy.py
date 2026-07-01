# -*- coding: utf-8 -*-
"""validate_gc1_retry_policy.py — PART6 retry 정책 ↔ L4 코드 대조 CLI (T90)

정적: JSON 로드
실행: merge_l4_atom_specs() 와 on_fail 필드 대조

Usage (repo 루트):
  python scripts/validate_gc1_retry_policy.py
  python scripts/validate_gc1_retry_policy.py --json deploy/gc1_atom_retry_policy.json

Exit: 0 = PASS, 1 = FAIL
"""
from __future__ import annotations

import argparse
import os
import sys

_REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _REPO not in sys.path:
    sys.path.insert(0, _REPO)

from gc1_runtime.layer0_retry import (  # noqa: E402
    DEFAULT_RETRY_POLICY_PATH,
    atoms_with_runtime_retry,
    load_retry_policy,
    merge_l4_atom_specs,
    validate_retry_policy,
)


def main() -> int:
    parser = argparse.ArgumentParser(description="GC1 PART6 retry policy validation")
    parser.add_argument("--json", default=DEFAULT_RETRY_POLICY_PATH, help="gc1_atom_retry_policy.json")
    args = parser.parse_args()

    path = os.path.abspath(args.json)
    if not os.path.isfile(path):
        print(f"[FAIL] not found: {path}", file=sys.stderr)
        return 1

    doc = load_retry_policy(path)
    specs = merge_l4_atom_specs()
    result = validate_retry_policy(doc, specs)

    print(f"=== PART6 retry policy: {os.path.basename(path)} ===")
    print(f"  schema_version : {doc.schema_version}")
    print(f"  policies       : {len(doc.policies)}")
    print(f"  g_post_retry   : {len(doc.g_post_retry)}")
    print(f"  externals      : {len(doc.externals)} (documented only)")
    print(f"  L4 specs total : {len(specs)}")
    print(f"  code retry atoms: {', '.join(atoms_with_runtime_retry(specs)) or '(none)'}\n")

    for entry in doc.policies:
        delay = entry.retry_delay_ms if entry.retry_delay_ms is not None else "-"
        kind = f" [{entry.delay_kind}]" if entry.delay_kind != "sleep" else ""
        print(f"  {entry.atom_id}  attempt={entry.max_attempt}  delay={delay}{kind}  code={entry.fail_code}")

    if result.warnings:
        print("\n[WARN]")
        for w in result.warnings:
            print(f"  - {w}")

    if result.errors:
        print("\n[FAIL]")
        for e in result.errors:
            print(f"  - {e}")
        print(f"\nchecked={result.checked} errors={len(result.errors)}")
        return 1

    print(f"\n[PASS] checked={result.checked} policies match L4 on_fail")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
