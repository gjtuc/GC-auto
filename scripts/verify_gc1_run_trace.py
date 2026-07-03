# -*- coding: utf-8 -*-
"""
GC1 런 추적 — Cursor 꺼져 있어도 OCR 폴백·학습이 됐는지 확인.

사용 (GC1 장비 PC):
  python scripts/verify_gc1_run_trace.py
  python scripts/verify_gc1_run_trace.py --tail 30

핫스팟 없이 OCR 폴백만 시험:
  python gc1_runtime/layer0_hotspot_agent.py --ocr-fallback-once
  python scripts/verify_gc1_run_trace.py
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime
from pathlib import Path

_REPO = Path(__file__).resolve().parents[1]
if str(_REPO) not in sys.path:
    sys.path.insert(0, str(_REPO))


def _read_json(path: Path) -> dict:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return data if isinstance(data, dict) else {}
    except (OSError, json.JSONDecodeError):
        return {}


def _tail_lines(path: Path, n: int) -> list[str]:
    if not path.is_file():
        return []
    try:
        lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
        return lines[-n:]
    except OSError:
        return []


def _fmt_ts(iso: str) -> str:
    if not iso:
        return "-"
    try:
        return iso.replace("T", " ")[:19]
    except Exception:
        return iso


def main() -> None:
    parser = argparse.ArgumentParser(description="GC1 OCR 폴백·학습 런 추적")
    parser.add_argument("--tail", type=int, default=15, help="로그 tail 줄 수")
    args = parser.parse_args()

    from gc_profiles import bootstrap_env, paths_for_output_dir, resolve_profile
    from gc1_runtime.layer0_hotspot_agent import collect_hotspot_agent_status
    from gc1_runtime.layer3_ocr_learn import case_study_dir, learnings_dir, overlay_path

    bootstrap_env(str(_REPO))
    profile = resolve_profile(str(_REPO))
    paths = paths_for_output_dir(profile.excel_output_dir, gc_instance=profile.gc_instance)
    out = Path(paths["runtime_dir"])

    hotspot_log = out / ".gc_hotspot_agent_run.log"
    hotspot_state = out / ".gc_hotspot_agent_state.json"
    journal_latest = learnings_dir() / "run_journal_latest.json"
    agent_log = learnings_dir() / "agent_run_log.txt"
    overlay = overlay_path()
    case_dir = case_study_dir()

    status = collect_hotspot_agent_status(str(out))
    state = _read_json(hotspot_state)
    journal = _read_json(journal_latest)

    print("=" * 60)
    print("  GC1 런 추적 (Cursor 없이도 이 화면으로 확인)")
    print("=" * 60)
    print(f"데이터 폴더    : {paths['data_root']}")
    print(f"자동화 폴더    : {out}")
    print(f"시각          : {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()

    print("[1] 핫스팟 · Cursor / OCR 경로")
    print(f"  watch 처리 중 : {'예' if status.get('session_in_flight') else '아니오'}")
    print(f"  Cursor SDK    : {status.get('cursor_sdk_detail')}")
    last_mode = state.get("last_mode") or journal.get("mode") or "-"
    print(f"  마지막 모드   : {last_mode}")
    print("    · cursor_enqueued → SDK 에이전트 요청")
    print("    · ocr_direct / ocr_after_cursor_fail → Python OCR 폴백")
    print(f"  마지막 성공   : {state.get('last_ok')}")
    print(f"  마지막 완료   : {state.get('last_finished_at') or _fmt_ts(journal.get('closed_at', ''))}")
    if state.get("last_error"):
        print(f"  마지막 오류   : {str(state.get('last_error'))[:200]}")
    print()

    print("[2] 핫스팟 에이전트 로그 (tail)")
    if hotspot_log.is_file():
        for line in _tail_lines(hotspot_log, args.tail):
            print(f"  {line}")
    else:
        print("  (아직 없음 - 핫스팟 연결 또는 --ocr-fallback-once 후 생김)")
    print()

    print("[3] 런 종료 저널 (자가 피드백 - 에이전트/Cursor용)")
    if journal:
        print(f"  run_id        : {journal.get('run_id', '-')}")
        print(f"  pipeline_ok   : {journal.get('pipeline_ok')}")
        print(f"  ocr_fails     : {journal.get('ocr_fail_count', 0)}")
        patches = journal.get("ocr_applied_patches") or []
        print(f"  overlay 반영  : {len(patches)}건")
        for p in patches[:5]:
            print(f"    - {p}")
        recs = journal.get("agent_recommendations") or []
        if recs:
            print("  권장 (다음 Cursor 세션):")
            for r in recs[:8]:
                print(f"    · {r}")
        result = journal.get("result") or {}
        if result.get("output_path"):
            print(f"  산출물        : {result.get('output_path')}")
    else:
        print("  (아직 없음 - 파이프라인 1회 끝나면 run_journal_latest.json 생성)")
    print(f"  경로          : {journal_latest}")
    print()

    print("[4] agent_run_log.txt (런별 한 줄 요약 tail)")
    if agent_log.is_file():
        for line in _tail_lines(agent_log, args.tail):
            print(f"  {line.rstrip()}")
    else:
        print("  (아직 없음)")
    print()

    print("[5] OCR 케이스 스터디 (실패 시 빨간 박스·탐색 기록)")
    fails = sorted(case_dir.glob("fail_*.json"), key=lambda p: p.stat().st_mtime, reverse=True)
    print(f"  폴더          : {case_dir}")
    print(f"  fail JSON 수  : {len(fails)}")
    for fp in fails[:3]:
        rep = _read_json(fp)
        print(f"    · {fp.name} step={rep.get('step_id')} kind={rep.get('kind')}")
    print()

    print("[6] overlay 학습 (다음 런에 자동 반영 - Cursor 불필요)")
    if overlay.is_file():
        ov = _read_json(overlay)
        regions = ov.get("regions") or {}
        print(f"  경로          : {overlay}")
        print(f"  region 키 수  : {len(regions)}")
    else:
        print("  (아직 없음 - OCR 실패·학습 후 screen_regions.overlay.json 생성)")
    print()

    print("=" * 60)
    print("검증 방법 요약")
    print("=" * 60)
    print("A) 핫스팟 없이 OCR 폴백만 시험 (Autochro 켜 둔 상태):")
    print("     python gc1_runtime/layer0_hotspot_agent.py --ocr-fallback-once")
    print("     python scripts/verify_gc1_run_trace.py")
    print("B) Cursor 실패 → OCR 폴백: 로그에 FALLBACK OCR 또는 last_mode=ocr_after_cursor_fail")
    print("C) 자가 피드백: [3] patches 증가 + [6] overlay - Cursor 없이도 다음 런에 적용")
    print("D) Cursor 켜서 run_journal_latest.json 읽으면 코드 수정 루프 가능 (선택)")


if __name__ == "__main__":
    main()
