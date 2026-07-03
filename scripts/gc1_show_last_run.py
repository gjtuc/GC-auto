# -*- coding: utf-8 -*-
"""
GC1 마지막 런·OCR 폴백·학습 가시화 — Cursor 꺼져 있어도 확인.

사용:
  python scripts/gc1_show_last_run.py
  python scripts/gc1_show_last_run.py --tail-log 30
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

from gc_profiles import bootstrap_env, resolve_profile


def _read_json(path: Path) -> dict:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return data if isinstance(data, dict) else {}
    except (OSError, json.JSONDecodeError):
        return {}


def _tail(path: Path, n: int) -> list[str]:
    if not path.is_file():
        return []
    try:
        lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
        return lines[-n:]
    except OSError:
        return []


def main() -> None:
    parser = argparse.ArgumentParser(description="GC1 마지막 런·OCR·핫스팟 로그 요약")
    parser.add_argument("--tail-log", type=int, default=15, help="핫스팟 로그 마지막 N줄")
    args = parser.parse_args()

    bootstrap_env(str(_REPO))
    profile = resolve_profile(str(_REPO))
    out_dir = Path(profile.excel_output_dir)
    learn_dir = Path(os.path.expanduser("~")) / ".cursor" / "gc-ocr-learnings"
    case_dir = Path(os.path.expanduser("~")) / ".cursor" / "gc-ocr-case-study"

    print("=" * 60)
    print("GC1 런 가시화 (Cursor 없이 파일로 확인)")
    print("=" * 60)
    print(f"출력 폴더     : {out_dir}")
    print(f"학습·저널     : {learn_dir}")
    print(f"케이스 스터디 : {case_dir}")
    print()

    # --- 핫스팟 / Cursor / OCR 폴백 ---
    state = _read_json(out_dir / ".gc_hotspot_agent_state.json")
    print("[핫스팟 에이전트]")
    if state:
        print(f"  마지막 모드   : {state.get('last_mode') or '-'}")
        print(f"  마지막 완료   : {state.get('last_finished_at') or '-'}")
        print(f"  성공 여부     : {state.get('last_ok')}")
        if state.get("last_cursor_message"):
            print(f"  Cursor 메시지 : {str(state.get('last_cursor_message'))[:120]}")
        if state.get("last_error"):
            print(f"  OCR 오류      : {state.get('last_error')}")
    else:
        print("  (아직 .gc_hotspot_agent_state.json 없음)")

    log_path = out_dir / ".gc_hotspot_agent_run.log"
    log_lines = _tail(log_path, args.tail_log)
    print(f"\n[핫스팟 로그 tail — {log_path.name}]")
    if log_lines:
        for line in log_lines:
            print(f"  {line}")
    else:
        print("  (로그 없음)")

    # --- 에이전트 저널 (런 closure) ---
    journal_path = learn_dir / "run_journal_latest.json"
    journal = _read_json(journal_path)
    print(f"\n[런 저널 — run_journal_latest.json]")
    if journal:
        print(f"  run_id        : {journal.get('run_id')}")
        print(f"  closed_at     : {journal.get('closed_at')}")
        print(f"  pipeline_ok   : {journal.get('pipeline_ok')}")
        print(f"  fail_reason   : {journal.get('fail_reason') or '-'}")
        print(f"  OCR 실패 건수 : {journal.get('ocr_fail_count', 0)}")
        patches = journal.get("ocr_applied_patches") or []
        print(f"  학습 반영     : {len(patches)}건")
        for p in patches[:5]:
            print(f"    · {p}")
        recs = journal.get("agent_recommendations") or []
        if recs:
            print("  권장 (다음 Cursor 세션):")
            for r in recs[:8]:
                print(f"    · {r}")
        phases = journal.get("phases") or []
        if phases:
            print("  파이프라인 단계:")
            for ph in phases[-8:]:
                mark = "OK" if ph.get("ok") else "FAIL"
                print(f"    [{mark}] {ph.get('phase')} — {str(ph.get('detail', ''))[:60]}")
    else:
        print("  (아직 런 종료 저널 없음 — OCR force 1회 돌리면 생김)")

    agent_log = learn_dir / "agent_run_log.txt"
    agent_lines = _tail(agent_log, 5)
    print(f"\n[agent_run_log.txt tail]")
    if agent_lines:
        for line in agent_lines:
            print(f"  {line}")
    else:
        print("  (없음)")

    # --- 케이스 스터디 ---
    fail_jsons = sorted(case_dir.glob("fail_*.json"), key=lambda p: p.stat().st_mtime, reverse=True)
    print(f"\n[케이스 스터디 최근 fail JSON: {len(fail_jsons)}개 전체]")
    for fp in fail_jsons[:3]:
        mtime = datetime.fromtimestamp(fp.stat().st_mtime).strftime("%Y-%m-%d %H:%M")
        rep = _read_json(fp)
        print(f"  {mtime}  {fp.name}")
        print(f"    step={rep.get('step_id')} kind={rep.get('kind')} reason={str(rep.get('reason', ''))[:50]}")

    overlay = learn_dir / "screen_regions.overlay.json"
    print(f"\n[overlay 학습 파일]")
    if overlay.is_file():
        mtime = datetime.fromtimestamp(overlay.stat().st_mtime).strftime("%Y-%m-%d %H:%M")
        ov = _read_json(overlay)
        regions = ov.get("regions") or {}
        print(f"  갱신: {mtime}  영역 수: {len(regions)}")
    else:
        print("  (아직 없음)")

    print()
    print("— 검증 팁 —")
    print("  1) 핫스팟 없이 OCR만: python gc1_runtime/layer0_hotspot_agent.py --ocr-fallback-once")
    print("  2) Cursor 실패 시뮬: env에 CURSOR_API_KEY=bad 잠깐 넣고 핫스팟 연결")
    print("  3) 위 명령 후 이 스크립트 다시 실행 → last_mode=ocr_direct, 저널·학습 확인")
    print("=" * 60)


if __name__ == "__main__":
    main()
