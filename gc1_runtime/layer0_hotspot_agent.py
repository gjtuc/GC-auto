# -*- coding: utf-8 -*-
"""
GC1 iPhone 핫스팟 연결 edge → Cursor 새 에이전트에 개시 메시지 전달.

watch가 ``run_processing()`` 을 직접 호출하지 않고, 에이전트가 OCR·케이스스터디·런 closure까지
수행하도록 ``동작해`` 등 개시 문구를 Cursor SDK 로 보냅니다.

환경 변수:
  GC1_HOTSPOT_CURSOR_AGENT=1   — 기본 1 (GC1). 0 이면 watch 가 직접 파이프라인
  GC1_HOTSPOT_RECONNECT_MIN_SEC — 탐지·에이전트 재요청 쿨다운 (기본 1800 = 30분)
  CURSOR_API_KEY               — 없으면 enqueue 실패 → watch 가 직접 파이프라인 폴백
  GC1_HOTSPOT_CURSOR_MODEL     — 기본 composer-2.5
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import time
from datetime import datetime
from typing import Any

from gc_config import hotspot_reconnect_min_sec

HOTSPOT_AGENT_STATE = ".gc_hotspot_agent_state.json"
HOTSPOT_AGENT_PENDING = ".gc_hotspot_agent_pending.json"
HOTSPOT_AGENT_LOG = ".gc_hotspot_agent_run.log"

_IN_FLIGHT_STALE_SEC = 7200

_SUBPROCESS_FLAGS = 0
if sys.platform == "win32" and hasattr(subprocess, "CREATE_NO_WINDOW"):
    _SUBPROCESS_FLAGS = subprocess.CREATE_NO_WINDOW


def _env_bool(name: str, default: bool = True) -> bool:
    raw = os.getenv(name, "").strip().lower()
    if not raw:
        return default
    return raw in ("1", "true", "yes", "on")


def hotspot_cursor_agent_enabled() -> bool:
    """GC1 핫스팟 edge 시 Cursor 에이전트 개시 (기본 켜짐)."""
    return _env_bool("GC1_HOTSPOT_CURSOR_AGENT", True)


def _state_path(output_dir: str) -> str:
    return os.path.join(output_dir, HOTSPOT_AGENT_STATE)


def _pending_path(output_dir: str) -> str:
    return os.path.join(output_dir, HOTSPOT_AGENT_PENDING)


def _log_path(output_dir: str) -> str:
    return os.path.join(output_dir, HOTSPOT_AGENT_LOG)


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


def _append_log(output_dir: str, line: str) -> None:
    path = _log_path(output_dir)
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    stamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(path, "a", encoding="utf-8") as handle:
        handle.write(f"[{stamp}] {line}\n")


def build_hotspot_initiation_prompt(*, ssid: str, just_connected: bool) -> str:
    """사용자가 채팅에 치는 것과 동일한 개시 문구 — 에이전트 규칙이 force 파이프라인으로 이어짐."""
    _ = just_connected
    _ = ssid
    return "동작해"


def is_hotspot_agent_in_flight(output_dir: str) -> bool:
    state = _load_json(_state_path(output_dir))
    if not state.get("agent_in_flight"):
        return False
    since = float(state.get("in_flight_since") or 0)
    if since and (time.time() - since) > _IN_FLIGHT_STALE_SEC:
        return False
    return True


def _cooldown_remaining_sec(state: dict, cooldown_sec: int) -> float:
    last = float(state.get("last_trigger_at") or 0)
    if not last:
        return 0.0
    elapsed = time.time() - last
    return max(0.0, float(cooldown_sec) - elapsed)


def should_enqueue_hotspot_agent(
    output_dir: str,
    *,
    chemstation_mode: str = "gc1",
) -> tuple[bool, str]:
    """쿨다운·in-flight 검사. (ok, reason)."""
    if is_hotspot_agent_in_flight(output_dir):
        return False, "SKIP: Cursor 에이전트 실행 중"
    cooldown = hotspot_reconnect_min_sec(chemstation_mode)
    state = _load_json(_state_path(output_dir))
    remain = _cooldown_remaining_sec(state, cooldown)
    if remain > 0:
        mins = int(remain // 60)
        secs = int(remain % 60)
        return False, f"SKIP: 핫스팟 에이전트 쿨다운 {mins}분 {secs}초 남음"
    if not os.getenv("CURSOR_API_KEY", "").strip():
        return False, "CURSOR_API_KEY 없음"
    return True, "enqueue"


def enqueue_hotspot_cursor_agent(
    output_dir: str,
    base_script_dir: str,
    *,
    ssid: str,
    just_connected: bool,
    chemstation_mode: str = "gc1",
) -> tuple[bool, str]:
    """
    백그라운드에서 Cursor 에이전트 1회 기동.
    성공 시 watch 는 직접 pipeline 을 호출하지 않음.
    """
    if not hotspot_cursor_agent_enabled():
        return False, "GC1_HOTSPOT_CURSOR_AGENT=0"

    ok, reason = should_enqueue_hotspot_agent(output_dir, chemstation_mode=chemstation_mode)
    if not ok:
        return False, reason

    pending: dict[str, Any] = {
        "ssid": ssid,
        "just_connected": just_connected,
        "enqueued_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "prompt": build_hotspot_initiation_prompt(ssid=ssid, just_connected=just_connected),
        "base_script_dir": base_script_dir,
    }
    os.makedirs(output_dir, exist_ok=True)
    _save_json(_pending_path(output_dir), pending)

    state = _load_json(_state_path(output_dir))
    state["agent_in_flight"] = True
    state["in_flight_since"] = time.time()
    state["last_enqueue_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    state["last_ssid"] = ssid
    _save_json(_state_path(output_dir), state)

    handler_py = os.path.join(base_script_dir, "gc1_runtime", "layer0_hotspot_agent.py")
    cmd = [sys.executable, handler_py, "--trigger-once", "--output-dir", output_dir]
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
        state["agent_in_flight"] = False
        _save_json(_state_path(output_dir), state)
        return False, f"에이전트 프로세스 시작 실패: {exc}"

    _append_log(output_dir, f"ENQUEUE ssid={ssid!r} just_connected={just_connected}")
    return True, "Cursor 새 에이전트에 「동작해」 요청 — OCR·학습 루프로 처리"


def trigger_hotspot_cursor_agent_once(output_dir: str, base_script_dir: str) -> dict:
    """pending 1건 — Cursor SDK Agent.prompt."""
    pending_path = _pending_path(output_dir)
    pending = _load_json(pending_path)
    state_path = _state_path(output_dir)

    def _clear_in_flight() -> None:
        state = _load_json(state_path)
        state["agent_in_flight"] = False
        _save_json(state_path, state)

    if not pending:
        _clear_in_flight()
        return {"ok": False, "reason": "pending 없음"}

    prompt = str(pending.get("prompt") or "동작해")
    work_dir = str(pending.get("base_script_dir") or base_script_dir)
    _append_log(output_dir, f"START prompt={prompt!r}")

    from gc_error_handler import invoke_cursor_agent

    cursor_ok, cursor_msg = invoke_cursor_agent(prompt, work_dir)
    result: dict[str, Any] = {
        "ok": cursor_ok,
        "cursor_message": cursor_msg,
        "prompt": prompt,
    }

    state = _load_json(state_path)
    state["agent_in_flight"] = False
    state["last_finished_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    if cursor_ok:
        state["last_trigger_at"] = time.time()
        state["last_ok"] = True
    else:
        state["last_ok"] = False
    state["last_cursor_message"] = str(cursor_msg)[:500]
    _save_json(state_path, state)

    try:
        os.remove(pending_path)
    except OSError:
        pass

    _append_log(output_dir, f"DONE ok={cursor_ok}: {str(cursor_msg)[:200]}")
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description="GC1 핫스팟 → Cursor 에이전트 개시")
    parser.add_argument("--trigger-once", action="store_true", help="pending 1건 처리")
    parser.add_argument("--output-dir", default="", help="Desktop\\박은규 등 excel 출력 폴더")
    args = parser.parse_args()

    if not args.trigger_once:
        parser.print_help()
        return

    from gc_profiles import resolve_profile, script_dir

    base = script_dir()
    output_dir = args.output_dir.strip() or resolve_profile(base).excel_output_dir
    result = trigger_hotspot_cursor_agent_once(output_dir, base)
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
