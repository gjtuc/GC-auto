# -*- coding: utf-8 -*-
"""probe_gc1_ident.py — Ω.A.B.IDENT 스냅샷 CLI (T89)

정적 import + **실행 검증**: 이 PC에서 IDENT leaf 를 읽어 JSON 출력.

Usage (repo 루트):
  python scripts/probe_gc1_ident.py
  python scripts/probe_gc1_ident.py --pretty

Exit: 0 = ok_for_gc1_autochro True, 2 = False (진단용, 오류 아님)
"""
from __future__ import annotations

import argparse
import json
import os
import sys

_REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _REPO not in sys.path:
    sys.path.insert(0, _REPO)

from gc1_runtime.layer0_ident import read_ident_snapshot  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description="GC1 IDENT probe (B-layer)")
    parser.add_argument("--pretty", action="store_true", help="indented JSON")
    args = parser.parse_args()

    snap = read_ident_snapshot()
    payload = snap.to_dict()
    if args.pretty:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        print(json.dumps(payload, ensure_ascii=False))

    return 0 if snap.ok_for_gc1_autochro else 2


if __name__ == "__main__":
    raise SystemExit(main())
