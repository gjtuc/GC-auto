# -*- coding: utf-8 -*-
"""
GC1 스터디·성숙도·정책 한 화면 요약.

  python scripts/gc1_study_review.py
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

_REPO = Path(__file__).resolve().parents[1]
if str(_REPO) not in sys.path:
    sys.path.insert(0, str(_REPO))

from gc1_runtime.layer3_ocr_maturity import load_maturity, load_policy
from gc1_runtime.layer3_ocr_study import review_prior_learning
from gc1_runtime.layer3_ocr_learn import learnings_dir


def _read_json(path: Path) -> dict:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}


def main() -> int:
    learn = learnings_dir()
    print("=" * 60)
    print("  GC1 OCR 스터디·성숙도 요약")
    print("=" * 60)
    print(f"학습 폴더: {learn}\n")

    review_prior_learning(log_fn=print)

    mat = load_maturity()
    skills = mat.get("skills") or {}
    mature = [(k, v) for k, v in skills.items() if v.get("mature")]
    learning = [(k, v) for k, v in skills.items() if not v.get("mature") and v.get("attempts")]

    print(f"\n[성숙도] threshold={mat.get('threshold')} min_n={mat.get('min_attempts')}")
    print(f"  성숙(학습 중단): {len(mature)}")
    for k, v in sorted(mature, key=lambda x: -float(x[1].get("rate") or 0))[:12]:
        print(f"    {k}  rate={v.get('rate')} n={v.get('attempts')}")

    print(f"  학습 중: {len(learning)}")
    for k, v in sorted(learning, key=lambda x: -float(x[1].get('rate') or 0))[:12]:
        print(f"    {k}  rate={v.get('rate')} n={v.get('attempts')}")

    pol = load_policy()
    print(f"\n[정책] preferred_method (다음 런 우선)")
    for k, v in list((pol.get("skills") or {}).items())[:15]:
        print(f"    {k} -> {v.get('preferred_method')} ({v.get('best_rate')})")

    study = _read_json(learn / "study_journal_latest.json")
    if study:
        r = study.get("result") or {}
        print(f"\n[직전 스터디] run={study.get('run_id')} obs={r.get('observation_count')} patches={len(r.get('applied_patches') or [])}")

    log = learn / "study_session_log.txt"
    if log.is_file():
        lines = log.read_text(encoding="utf-8", errors="replace").splitlines()
        print("\n[스터디 로그 tail]")
        for line in lines[-8:]:
            print(f"  {line}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
