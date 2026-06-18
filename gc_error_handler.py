# -*- coding: utf-8 -*-
"""
gc_error_handler.py — GC 오류 로그 · watch 재시작 · Cursor SDK 복구

=============================================================================
[어느 PC — GC1 (은규) 에서 추가]
=============================================================================

  GC1 PC merge 시 추가. GC2 PC에도 코드는 있으나 env 로 비활성 가능.

  GitHub push 후 다른 PC: git pull. GC_ERROR_HANDLER_ENABLED=0 이면 GC2에서 무시.

흐름:
  1) watch/poll 이 error·stale heartbeat 감지 → enqueue_and_recover()
  2) 오류 JSONL + GC_오류_최근.txt 저장
  3) gc_stop_watch.bat → gc_start_watch.bat 재시작
  4) CURSOR_API_KEY 있으면 Cursor SDK Agent.prompt 로 수정·재시작 요청

환경 변수 (gc_automation.env):
  CURSOR_API_KEY              — Cursor SDK (없으면 재시작만)
  GC_ERROR_HANDLER_ENABLED=1  — 0 이면 비활성
  GC_ERROR_RESTART=1          — watch 재시작 (기본 1)
  GC_ERROR_CURSOR=1           — SDK 호출 (기본 1, API 키 필요)
  GC_ERROR_RECOVERY_COOLDOWN_SEC=300
  GC_ERROR_CURSOR_COOLDOWN_SEC=1800
  GC_ERROR_CURSOR_MAX_PER_DAY=8
  GC_ERROR_STALE_HEARTBEAT_SEC=180
  GC_ERROR_CURSOR_MODEL=composer-2.5
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import sys
import time
from datetime import datetime
from typing import Any, Optional

from gc_profiles import paths_for_output_dir, resolve_profile, script_dir
from gc_status import is_watch_alive

_SUBPROCESS_FLAGS = 0
if sys.platform == "win32" and hasattr(subprocess, "CREATE_NO_WINDOW"):
    _SUBPROCESS_FLAGS = subprocess.CREATE_NO_WINDOW

ERROR_LOG_JSONL = ".gc_error_log.jsonl"
ERROR_LATEST_TXT = "GC_오류_최근.txt"
ERROR_PENDING_JSON = ".gc_error_pending.json"
ERROR_HANDLER_STATE = ".gc_error_handler_state.json"
ERROR_HANDLER_RUN_LOG = ".gc_error_handler_run.log"


def _env_bool(name: str, default: bool = True) -> bool:
    raw = os.getenv(name, "").strip().lower()
    if not raw:
        return default
    return raw in ("1", "true", "yes", "on")


def _env_int(name: str, default: int) -> int:
    raw = os.getenv(name, "").strip()
    if not raw:
        return default
    try:
        return max(0, int(raw))
    except ValueError:
        return default


def _paths(output_dir: str) -> dict[str, str]:
    base = paths_for_output_dir(output_dir)
    return {
        **base,
        "error_log": os.path.join(output_dir, ERROR_LOG_JSONL),
        "error_latest": os.path.join(output_dir, ERROR_LATEST_TXT),
        "error_pending": os.path.join(output_dir, ERROR_PENDING_JSON),
        "handler_state": os.path.join(output_dir, ERROR_HANDLER_STATE),
        "handler_run_log": os.path.join(output_dir, ERROR_HANDLER_RUN_LOG),
    }


def _load_json(path: str) -> dict:
    try:
        with open(path, encoding="utf-8") as handle:
            data = json.load(handle)
        return data if isinstance(data, dict) else {}
    except (OSError, json.JSONDecodeError):
        return {}


def _save_json(path: str, data: dict) -> None:
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(data, handle, ensure_ascii=False, indent=2)


def _append_run_log(path: str, line: str) -> None:
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    stamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(path, "a", encoding="utf-8") as handle:
        handle.write(f"[{stamp}] {line}\n")


def error_signature(entry: dict) -> str:
    raw = "|".join(
        str(entry.get(key, ""))
        for key in ("source", "status_code", "message", "issue_type")
    )
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:16]


def record_error(output_dir: str, entry: dict) -> dict:
    """오류 1건 기록 — JSONL + GC_오류_최근.txt."""
    paths = _paths(output_dir)
    entry = {
        **entry,
        "recorded_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "signature": error_signature(entry),
    }
    os.makedirs(output_dir, exist_ok=True)
    with open(paths["error_log"], "a", encoding="utf-8") as handle:
        handle.write(json.dumps(entry, ensure_ascii=False) + "\n")

    lines = [
        "========================================",
        "  GC 오류 기록",
        "========================================",
        f"시각: {entry['recorded_at']}",
        f"출처: {entry.get('source', '?')}",
        f"코드: {entry.get('status_code', entry.get('issue_type', '?'))}",
        f"내용: {entry.get('message', '')}",
    ]
    if entry.get("sequence_folder"):
        lines.append(f"경로: {entry['sequence_folder']}")
    if entry.get("watch_status"):
        ws = entry["watch_status"]
        lines.append(f"Watch PID: {ws.get('pid')}")
        lines.append(f"Watch heartbeat: {ws.get('last_heartbeat')}")
    lines.append("========================================")
    with open(paths["error_latest"], "w", encoding="utf-8") as handle:
        handle.write("\n".join(lines) + "\n")
    return entry


def _read_watch_status(path: str) -> dict:
    return _load_json(path)


def _should_recover(state: dict, signature: str, *, cursor: bool) -> tuple[bool, str]:
    now = time.time()
    cooldown = _env_int("GC_ERROR_RECOVERY_COOLDOWN_SEC", 300)
    last = state.get("last_recovery_by_signature", {})
    if isinstance(last, dict):
        prev = last.get(signature)
        if prev and now - float(prev) < cooldown:
            return False, f"동일 오류 {cooldown}초 쿨다운 중"


    if cursor:
        cursor_cooldown = _env_int("GC_ERROR_CURSOR_COOLDOWN_SEC", 1800)
        cursor_last = state.get("last_cursor_by_signature", {})
        if isinstance(cursor_last, dict):
            prev_c = cursor_last.get(signature)
            if prev_c and now - float(prev_c) < cursor_cooldown:
                return True, "재시작만 (Cursor 쿨다운)"

        today = datetime.now().strftime("%Y%m%d")
        day_counts = state.get("cursor_calls_by_day", {})
        if not isinstance(day_counts, dict):
            day_counts = {}
        max_day = _env_int("GC_ERROR_CURSOR_MAX_PER_DAY", 8)
        if int(day_counts.get(today, 0)) >= max_day:
            return True, "재시작만 (일일 Cursor 한도)"

    return True, "재시작 + Cursor"


def _update_recovery_state(
    path: str,
    signature: str,
    *,
    cursor_called: bool,
) -> None:
    state = _load_json(path)
    now = time.time()
    by_sig = state.get("last_recovery_by_signature")
    if not isinstance(by_sig, dict):
        by_sig = {}
    by_sig[signature] = now
    state["last_recovery_by_signature"] = by_sig

    if cursor_called:
        cursor_by = state.get("last_cursor_by_signature")
        if not isinstance(cursor_by, dict):
            cursor_by = {}
        cursor_by[signature] = now
        state["last_cursor_by_signature"] = cursor_by
        today = datetime.now().strftime("%Y%m%d")
        day_counts = state.get("cursor_calls_by_day")
        if not isinstance(day_counts, dict):
            day_counts = {}
        day_counts[today] = int(day_counts.get(today, 0)) + 1
        state["cursor_calls_by_day"] = day_counts

    state["last_recovery_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    _save_json(path, state)


def stop_watch_processes(base_script_dir: str) -> int:
    """실행 중 --watch python 프로세스 종료 (gc_stop_watch.bat)."""
    stop_bat = os.path.join(base_script_dir, "gc_stop_watch.bat")
    if not os.path.isfile(stop_bat):
        return 0
    subprocess.run(
        ["cmd", "/c", stop_bat],
        cwd=base_script_dir,
        creationflags=_SUBPROCESS_FLAGS,
        timeout=30,
    )
    return 1


def restart_watch(base_script_dir: str) -> bool:
    """watch 중지 후 gc_start_watch.bat 실행."""
    stop_watch_processes(base_script_dir)
    time.sleep(2)
    start_bat = os.path.join(base_script_dir, "gc_start_watch.bat")
    if not os.path.isfile(start_bat):
        print(f"[오류] {start_bat} 없음")
        return False
    subprocess.Popen(
        ["cmd", "/c", start_bat],
        cwd=base_script_dir,
        creationflags=_SUBPROCESS_FLAGS,
    )
    return True


def build_cursor_prompt(entry: dict, output_dir: str, base_script_dir: str) -> str:
    latest_txt = os.path.join(output_dir, ERROR_LATEST_TXT)
    log_tail = ""
    log_path = os.path.join(output_dir, ERROR_LOG_JSONL)
    if os.path.isfile(log_path):
        try:
            with open(log_path, encoding="utf-8") as handle:
                lines = handle.readlines()
            log_tail = "".join(lines[-5:])
        except OSError:
            pass

    return (
        "GC chemstation-gc-automation 오류가 발생했습니다. 아래 로그를 보고 원인을 수정한 뒤 "
        "watch를 재시작하고 파이프라인이 정상 동작하는지 확인해 주세요.\n\n"
        f"repo: {base_script_dir}\n"
        f"출력 폴더: {output_dir}\n"
        f"오류 시각: {entry.get('recorded_at')}\n"
        f"status_code: {entry.get('status_code', entry.get('issue_type'))}\n"
        f"message: {entry.get('message')}\n"
        f"sequence: {entry.get('sequence_folder', '(없음)')}\n\n"
        f"GC_오류_최근.txt:\n"
        f"{open(latest_txt, encoding='utf-8').read() if os.path.isfile(latest_txt) else '(없음)'}\n\n"
        f"최근 JSONL:\n{log_tail or '(없음)'}\n\n"
        "작업:\n"
        "1) 로그·gc_watch.py·관련 모듈 확인 후 버그/설정 문제 수정\n"
        "2) gc_stop_watch.bat → gc_start_watch.bat 로 watch 재시작\n"
        "3) 필요 시 python gc_automation.py --force 로 1회 검증\n"
        "Autochro 창이 필요하면 사용자에게 안내 문구만 남기세요."
    )


def invoke_cursor_agent(prompt: str, base_script_dir: str) -> tuple[bool, str]:
    """Cursor SDK Agent.prompt — API 키 없거나 패키지 없으면 skip."""
    if not _env_bool("GC_ERROR_CURSOR", True):
        return False, "GC_ERROR_CURSOR=0"
    api_key = os.getenv("CURSOR_API_KEY", "").strip()
    if not api_key:
        return False, "CURSOR_API_KEY 없음"

    try:
        from cursor_sdk import Agent, AgentOptions, CursorAgentError, LocalAgentOptions
    except ImportError:
        return False, "cursor-sdk 미설치 — pip install cursor-sdk"

    model = os.getenv("GC_ERROR_CURSOR_MODEL", "composer-2.5").strip() or "composer-2.5"
    try:
        result = Agent.prompt(
            prompt,
            AgentOptions(
                api_key=api_key,
                model=model,
                local=LocalAgentOptions(cwd=base_script_dir),
            ),
        )
    except CursorAgentError as exc:
        return False, f"Cursor SDK 시작 실패: {exc.message}"
    except Exception as exc:
        return False, f"Cursor SDK 오류: {exc}"

    if getattr(result, "status", "") == "error":
        return False, f"Cursor run 실패: {getattr(result, 'id', '?')}"
    summary = getattr(result, "result", None) or getattr(result, "text", "") or "완료"
    return True, str(summary)[:500]


def run_recovery(output_dir: str, base_script_dir: str, entry: dict) -> dict:
    """오류 1건에 대해 재시작 + (옵션) Cursor SDK."""
    paths = _paths(output_dir)
    signature = entry.get("signature") or error_signature(entry)
    cursor_wanted = _env_bool("GC_ERROR_CURSOR", True) and bool(os.getenv("CURSOR_API_KEY", "").strip())
    ok_recover, plan = _should_recover(_load_json(paths["handler_state"]), signature, cursor=cursor_wanted)
    if not ok_recover:
        msg = plan
        _append_run_log(paths["handler_run_log"], f"SKIP {signature}: {msg}")
        return {"ok": False, "skipped": True, "reason": msg}

    result: dict[str, Any] = {"ok": True, "plan": plan, "signature": signature}
    _append_run_log(paths["handler_run_log"], f"START {signature}: {plan} — {entry.get('message', '')[:120]}")

    if _env_bool("GC_ERROR_RESTART", True):
        restarted = restart_watch(base_script_dir)
        result["watch_restarted"] = restarted
        _append_run_log(paths["handler_run_log"], f"RESTART watch: {restarted}")
    else:
        result["watch_restarted"] = False

    cursor_called = False
    if cursor_wanted and "Cursor 쿨다운" not in plan and "일일 Cursor 한도" not in plan:
        prompt = build_cursor_prompt(entry, output_dir, base_script_dir)
        cursor_ok, cursor_msg = invoke_cursor_agent(prompt, base_script_dir)
        cursor_called = cursor_ok
        result["cursor_ok"] = cursor_ok
        result["cursor_message"] = cursor_msg
        _append_run_log(paths["handler_run_log"], f"CURSOR ok={cursor_ok}: {cursor_msg[:200]}")

    _update_recovery_state(paths["handler_state"], signature, cursor_called=cursor_called)
    return result


def enqueue_and_recover(
    output_dir: str,
    base_script_dir: str,
    *,
    status_code: str,
    message: str,
    source: str = "watch",
    sequence_folder: Optional[str] = None,
    watch_status_path: Optional[str] = None,
) -> None:
    """오류 기록 후 백그라운드 recover-once 실행."""
    if not _env_bool("GC_ERROR_HANDLER_ENABLED", True):
        return

    watch_status = _read_watch_status(watch_status_path) if watch_status_path else {}
    entry = record_error(
        output_dir,
        {
            "source": source,
            "status_code": status_code,
            "message": message,
            "sequence_folder": sequence_folder,
            "watch_status": watch_status,
        },
    )
    paths = _paths(output_dir)
    signature = entry["signature"]
    cursor_wanted = _env_bool("GC_ERROR_CURSOR", True) and bool(os.getenv("CURSOR_API_KEY", "").strip())
    ok_recover, plan = _should_recover(_load_json(paths["handler_state"]), signature, cursor=cursor_wanted)
    if not ok_recover:
        _append_run_log(paths["handler_run_log"], f"ENQUEUE SKIP {signature}: {plan}")
        return

    _save_json(paths["error_pending"], entry)
    _append_run_log(paths["handler_run_log"], f"ENQUEUE {signature}: {plan}")

    handler_py = os.path.join(base_script_dir, "gc_error_handler.py")
    cmd = [sys.executable, handler_py, "--recover-once"]
    flags = _SUBPROCESS_FLAGS
    if sys.platform == "win32":
        flags |= subprocess.DETACHED_PROCESS | subprocess.CREATE_NEW_PROCESS_GROUP
    try:
        subprocess.Popen(
            cmd,
            cwd=base_script_dir,
            creationflags=flags,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            close_fds=True,
        )
    except OSError as exc:
        print(f"[경고] 오류 복구 프로세스 시작 실패: {exc}")


def recover_pending_once(output_dir: str, base_script_dir: str) -> dict:
    paths = _paths(output_dir)
    pending = _load_json(paths["error_pending"])
    if not pending:
        return {"ok": False, "reason": "pending 없음"}
    result = run_recovery(output_dir, base_script_dir, pending)
    try:
        os.remove(paths["error_pending"])
    except OSError:
        pass
    return result


def poll_issues(output_dir: str, watch_status_path: str) -> list[dict]:
    """watch JSON 에서 error·stale heartbeat 감지."""
    issues: list[dict] = []
    if not os.path.isfile(watch_status_path):
        return issues
    data = _read_watch_status(watch_status_path)
    if not data:
        return issues

    stale_sec = _env_int("GC_ERROR_STALE_HEARTBEAT_SEC", 180)
    if data.get("alive") and not is_watch_alive(watch_status_path, max_stale_sec=stale_sec):
        issues.append(
            {
                "source": "poll",
                "issue_type": "stale_heartbeat",
                "status_code": "stale_heartbeat",
                "message": (
                    f"watch heartbeat {stale_sec}초 초과 — Autochro 등에서 멈춘 것으로 보임"
                ),
                "watch_status": data,
            }
        )

    if data.get("status_code") == "error":
        issues.append(
            {
                "source": "poll",
                "issue_type": "watch_error",
                "status_code": "error",
                "message": data.get("message") or "watch error 상태",
                "sequence_folder": data.get("sequence_folder"),
                "watch_status": data,
            }
        )
    return issues


def poll_and_recover(output_dir: str, base_script_dir: str, watch_status_path: str) -> list[dict]:
    results = []
    for issue in poll_issues(output_dir, watch_status_path):
        entry = record_error(output_dir, issue)
        paths = _paths(output_dir)
        _save_json(paths["error_pending"], entry)
        results.append(recover_pending_once(output_dir, base_script_dir))
    return results


def main() -> None:
    parser = argparse.ArgumentParser(description="GC 오류 로그 · watch 재시작 · Cursor SDK")
    parser.add_argument("--recover-once", action="store_true", help="pending 오류 1건 복구")
    parser.add_argument("--poll", action="store_true", help="error/stale 감지 후 복구")
    parser.add_argument("--record-test", action="store_true", help="테스트 오류 기록만")
    args = parser.parse_args()

    base = script_dir()
    profile = resolve_profile(base)
    output_dir = profile.excel_output_dir
    runtime = paths_for_output_dir(output_dir)
    watch_status = runtime["watch_status_json"]

    if args.record_test:
        record_error(
            output_dir,
            {
                "source": "test",
                "status_code": "error",
                "message": "gc_error_handler 테스트 기록",
            },
        )
        print(f"[OK] 기록: {os.path.join(output_dir, ERROR_LATEST_TXT)}")
        return

    if args.recover_once:
        result = recover_pending_once(output_dir, base)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return

    if args.poll:
        results = poll_and_recover(output_dir, base, watch_status)
        print(json.dumps(results, ensure_ascii=False, indent=2))
        return

    parser.print_help()


if __name__ == "__main__":
    main()
