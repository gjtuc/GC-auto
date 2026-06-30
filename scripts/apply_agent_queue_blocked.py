# -*- coding: utf-8 -*-
"""apply_agent_queue_blocked.py — agent_queue_state blocked 설정 CLI (T96)

실장비·Origin·G: 등 사람 개입 필요 시 Hook followup 중단.

Usage (repo 루트):
  python scripts/apply_agent_queue_blocked.py --code autochro_live_ui --task T96
  python scripts/apply_agent_queue_blocked.py --code origin_gui --dry-run

Exit: 0 = ok, 1 = unknown code / policy error
"""
from __future__ import annotations

import argparse
import json
import os
import sys

_REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _REPO not in sys.path:
    sys.path.insert(0, _REPO)

from gc1_runtime.layer0_blocked import (  # noqa: E402
    DEFAULT_AGENT_QUEUE_STATE_PATH,
    DEFAULT_BLOCKED_POLICY_PATH,
    apply_agent_queue_blocked,
    infer_blocked_code_from_text,
    load_blocked_policy,
)


def main() -> int:
    parser = argparse.ArgumentParser(description="Set agent_queue_state to blocked")
    parser.add_argument("--code", help="blocked code (see validate_gc1_blocked_policy.py)")
    parser.add_argument("--infer-from", help="infer code from message text")
    parser.add_argument("--task", default="", help="last_task label e.g. T96")
    parser.add_argument("--policy", default=DEFAULT_BLOCKED_POLICY_PATH)
    parser.add_argument("--state", default=DEFAULT_AGENT_QUEUE_STATE_PATH)
    parser.add_argument("--dry-run", action="store_true", help="do not write state file")
    parser.add_argument("--pretty", action="store_true", help="indented JSON stdout")
    args = parser.parse_args()

    code = (args.code or "").strip()
    if not code and args.infer_from:
        code = infer_blocked_code_from_text(args.infer_from) or ""
    if not code:
        doc = load_blocked_policy(args.policy)
        known = ", ".join(r.code for r in doc.rules)
        print(f"[FAIL] --code or --infer-from required (known: {known})", file=sys.stderr)
        return 1

    result = apply_agent_queue_blocked(
        code,
        policy_path=args.policy,
        state_path=args.state,
        last_task=args.task,
        dry_run=args.dry_run,
    )
    if not result.ok:
        print(f"[FAIL] {result.message}", file=sys.stderr)
        return 1

    indent = 2 if args.pretty else None
    print(json.dumps(result.state, ensure_ascii=False, indent=indent))
    if args.dry_run:
        print("[OK] dry-run - state not written", file=sys.stderr)
    else:
        print(f"[OK] blocked={result.code} -> {result.state_path}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
