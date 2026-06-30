# -*- coding: utf-8 -*-
"""run_gc1_step8_live.py — Step 8.3a/8.3b 실장비 E2E 래퍼 (T97)

8.3d (``run_gc1_runtime_e2e.py``) 와 다름 — **실 Autochro UI** + optional SMTP.

Usage (repo 루트, GC1 장비 PC):
  python scripts/run_gc1_step8_live.py --preflight
  python scripts/run_gc1_step8_live.py --plan --mode excel
  python scripts/run_gc1_step8_live.py --run --mode excel
  python scripts/run_gc1_step8_live.py --run --mode mail --use-runtime

기본: **--run 없으면** gc_automation 호출 안 함 (계획·preflight 만).

Exit:
  0 = preflight/plan/run 성공
  1 = preflight 실패 또는 gc_automation 비정상 종료
  2 = IDENT 진단용 (ok_for_gc1_autochro False, --preflight)
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys

_REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _REPO not in sys.path:
    sys.path.insert(0, _REPO)

from gc1_runtime.layer0_ident import read_ident_snapshot  # noqa: E402
from gc1_runtime.layer0_live_e2e import (  # noqa: E402
    Step83Mode,
    build_live_e2e_plan,
    contrast_with_83d,
    evaluate_live_preflight,
)


def _parse_mode(raw: str) -> Step83Mode:
    key = (raw or "").strip().lower()
    if key in ("excel", "8.3a", "a"):
        return Step83Mode.EXCEL_ONLY
    if key in ("mail", "8.3b", "b"):
        return Step83Mode.MAIL
    raise SystemExit(f"[FAIL] unknown --mode {raw!r} (excel|mail)")


def main() -> int:
    parser = argparse.ArgumentParser(description="GC1 Step 8.3 live E2E wrapper")
    parser.add_argument(
        "--mode",
        default="excel",
        help="excel=8.3a (--no-email), mail=8.3b (default excel: safer during reduction)",
    )
    parser.add_argument("--use-runtime", action="store_true", help="GC1_USE_RUNTIME=1")
    parser.add_argument("--preflight", action="store_true", help="IDENT + plan checks only")
    parser.add_argument("--plan", action="store_true", help="print JSON plan (implies preflight)")
    parser.add_argument("--run", action="store_true", help="execute gc_automation.py subprocess")
    parser.add_argument("--pretty", action="store_true", help="indented JSON for --plan")
    args = parser.parse_args()

    mode = _parse_mode(args.mode)
    plan = build_live_e2e_plan(_REPO, mode, use_runtime=args.use_runtime)
    ident = read_ident_snapshot()
    pre = evaluate_live_preflight(ident.to_dict(), plan)

    payload: dict = {
        "ident": ident.to_dict(),
        "plan": plan.to_dict(),
        "preflight": pre.to_dict(),
        "contrast_83d": contrast_with_83d(plan),
    }

    if args.plan or args.preflight or not args.run:
        indent = 2 if args.pretty else None
        print(json.dumps(payload, ensure_ascii=False, indent=indent))

    if not pre.ok:
        print("[FAIL] preflight:", "; ".join(pre.errors), file=sys.stderr)
        for w in pre.warnings:
            print(f"[WARN] {w}", file=sys.stderr)
        return 1

    for w in pre.warnings:
        print(f"[WARN] {w}", file=sys.stderr)

    if not ident.ok_for_gc1_autochro and args.preflight and not args.run:
        return 2

    if not args.run:
        if args.preflight or args.plan:
            print("[OK] preflight passed (no --run)", file=sys.stderr)
            return 0
        print("[FAIL] specify --preflight, --plan, or --run", file=sys.stderr)
        return 1

    # 실행 검증 — 실장비 subprocess
    env = os.environ.copy()
    env.update(plan.env)
    cmd = [sys.executable, *plan.argv]
    print(f"[RUN] env AUTOCHRO_DRY_RUN={env.get('AUTOCHRO_DRY_RUN')} "
          f"GC1_USE_RUNTIME={env.get('GC1_USE_RUNTIME')}", file=sys.stderr)
    print(f"[RUN] {' '.join(cmd)}", file=sys.stderr)
    result = subprocess.run(cmd, cwd=_REPO, env=env)
    if result.returncode != 0:
        print(f"[FAIL] gc_automation exit={result.returncode}", file=sys.stderr)
        return 1
    print("[OK] gc_automation completed", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
