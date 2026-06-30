# -*- coding: utf-8 -*-
"""
GC1 iPhone 핫스팟 연결 edge → Cursor 새 에이전트에 개시 메시지 전달.

우선순위:
  1) Cursor SDK 가능 → Agent.prompt("동작해") — IDE 꺼져 있어도 SDK·API 키만 있으면 동작
  2) Cursor 불가 → Python OCR force 파이프라인 (Tesseract·Autochro eye·케이스스터디)

환경 변수:
  GC1_HOTSPOT_CURSOR_AGENT=1   — 기본 1. 0 이면 watch 가 직접 pipeline (레거시)
  GC1_HOTSPOT_RECONNECT_MIN_SEC — 탐지·재요청 쿨다운 (기본 1800 = 30분)
  CURSOR_API_KEY               — 없으면 자동으로 OCR 직접 실행
  GC1_HOTSPOT_CURSOR_MODEL     — 기본 composer-2.5
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import time
from dataclasses import replace
from datetime import datetime
from typing import Any, Literal

_REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _REPO_ROOT not in sys.path:
    sys.path.insert(0, _REPO_ROOT)

from gc_config import AppConfig, hotspot_reconnect_min_sec

HOTSPOT_AGENT_STATE = ".gc_hotspot_agent_state.json"
HOTSPOT_AGENT_PENDING = ".gc_hotspot_agent_pending.json"
HOTSPOT_AGENT_LOG = ".gc_hotspot_agent_run.log"

_IN_FLIGHT_STALE_SEC = 7200

# Cursor 없을 때도 핫스팟 세션에서 켜 둘 OCR 기본값 (env에 없을 때만)
_GC1_OCR_ENV_DEFAULTS: dict[str, str] = {
    "GC1_AUTOCHRO_EYE": "1",
    "GC1_AUTOCHRO_EYE_ADAPT": "1",
    "GC1_AUTOCHRO_EYE_STRICT": "0",
    "GC1_OCR_CASE_STUDY": "1",
    "GC1_OCR_LEARN": "1",
    "GC1_OCR_EXPLORE": "1",
}

DispatchAction = Literal[
    "cursor_enqueued",
    "ocr_started",
    "skip",
    "continue_legacy",
    "in_flight",
]

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


def ensure_gc1_ocr_env() -> dict[str, str]:
    """Cursor 없이 돌릴 때 OCR·학습 env 기본값 보장. 적용한 키만 반환."""
    applied: dict[str, str] = {}
    for key, value in _GC1_OCR_ENV_DEFAULTS.items():
        if not os.getenv(key, "").strip():
            os.environ[key] = value
            applied[key] = value
    return applied


def cursor_sdk_ready() -> tuple[bool, str]:
    """Cursor IDE 창 여부와 무관 — API 키 + cursor-sdk 패키지만 확인."""
    if not os.getenv("CURSOR_API_KEY", "").strip():
        return False, "CURSOR_API_KEY 없음"
    try:
        import cursor_sdk  # noqa: F401
    except ImportError:
        return False, "cursor-sdk 미설치 (pip install cursor-sdk)"
    return True, "준비됨"


def is_ocr_fallback_in_flight(output_dir: str) -> bool:
    state = _load_json(_state_path(output_dir))
    if not state.get("ocr_in_flight"):
        return False
    since = float(state.get("ocr_in_flight_since") or 0)
    if since and (time.time() - since) > _IN_FLIGHT_STALE_SEC:
        return False
    return True


def is_hotspot_agent_in_flight(output_dir: str) -> bool:
    state = _load_json(_state_path(output_dir))
    if not state.get("agent_in_flight"):
        return False
    since = float(state.get("in_flight_since") or 0)
    if since and (time.time() - since) > _IN_FLIGHT_STALE_SEC:
        return False
    return True


def is_hotspot_session_in_flight(output_dir: str) -> bool:
    return is_hotspot_agent_in_flight(output_dir) or is_ocr_fallback_in_flight(output_dir)


def _cooldown_remaining_sec(state: dict, cooldown_sec: int) -> float:
    last = float(state.get("last_trigger_at") or 0)
    if not last:
        return 0.0
    elapsed = time.time() - last
    return max(0.0, float(cooldown_sec) - elapsed)


def should_run_hotspot_session(
    output_dir: str,
    *,
    chemstation_mode: str = "gc1",
) -> tuple[bool, str]:
    """쿨다운·실행 중 검사 — Cursor/OCR 공통."""
    if is_hotspot_session_in_flight(output_dir):
        return False, "SKIP: 핫스팟 처리 실행 중"
    cooldown = hotspot_reconnect_min_sec(chemstation_mode)
    state = _load_json(_state_path(output_dir))
    remain = _cooldown_remaining_sec(state, cooldown)
    if remain > 0:
        mins = int(remain // 60)
        secs = int(remain % 60)
        return False, f"SKIP: 핫스팟 쿨다운 {mins}분 {secs}초 남음"
    return True, "ok"


def should_enqueue_hotspot_agent(
    output_dir: str,
    *,
    chemstation_mode: str = "gc1",
) -> tuple[bool, str]:
    """Cursor SDK enqueue 가능 여부."""
    ok, reason = should_run_hotspot_session(output_dir, chemstation_mode=chemstation_mode)
    if not ok:
        return False, reason
    sdk_ok, sdk_reason = cursor_sdk_ready()
    if not sdk_ok:
        return False, sdk_reason
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

    if not cursor_ok:
        _append_log(output_dir, f"FALLBACK OCR — Cursor 실패: {str(cursor_msg)[:120]}")
        fb = run_hotspot_ocr_fallback_once(output_dir, work_dir)
        result["fallback"] = fb
        result["ok"] = bool(fb.get("ok"))
        if fb.get("ok"):
            state = _load_json(state_path)
            state["last_trigger_at"] = time.time()
            state["last_ok"] = True
            state["last_mode"] = "ocr_after_cursor_fail"
            _save_json(state_path, state)

    return result


def _build_gc1_force_config(base_script_dir: str) -> AppConfig:
    from gc_automation import apply_env_overrides, config_from_args, force_config_from
    from gc_profiles import paths_for_output_dir, resolve_profile

    profile = resolve_profile(base_script_dir)
    runtime_paths = paths_for_output_dir(profile.excel_output_dir)
    args = argparse.Namespace(
        chemstation_mode=profile.chemstation_mode,
        data_path=None,
        no_email=False,
        sample_name=None,
        sequence_date=None,
        sequence_folder=None,
        detector="TCD",
        required_ssid=profile.required_ssid,
        no_wifi_check=False,
        force=True,
        watch=False,
        send_state_file=runtime_paths["send_state"],
    )
    config = config_from_args(args, base_script_dir)
    config = apply_env_overrides(config, base_script_dir, chemstation_mode_cli=profile.chemstation_mode)
    return force_config_from(config)


def _mark_ocr_in_flight(output_dir: str, *, on: bool) -> None:
    state = _load_json(_state_path(output_dir))
    if on:
        state["ocr_in_flight"] = True
        state["ocr_in_flight_since"] = time.time()
    else:
        state["ocr_in_flight"] = False
    _save_json(_state_path(output_dir), state)


def run_hotspot_ocr_fallback_once(output_dir: str, base_script_dir: str) -> dict:
    """
    Cursor 없이 Python OCR force 1회 — Autochro eye·케이스스터디·closure 포함.
    gc_automation.run_force_once 와 동일 경로.
    """
    applied = ensure_gc1_ocr_env()
    _mark_ocr_in_flight(output_dir, on=True)
    state_path = _state_path(output_dir)
    result: dict[str, Any] = {"ok": False, "mode": "ocr_direct", "ocr_env_applied": applied}
    _append_log(output_dir, "OCR_FALLBACK START")

    try:
        from gc_automation import run_force_once

        config = _build_gc1_force_config(base_script_dir)
        if output_dir:
            config = replace(config, excel_output_dir=os.path.normpath(output_dir))
        run_force_once(config, base_script_dir)
        result["ok"] = True
        state = _load_json(state_path)
        state["last_trigger_at"] = time.time()
        state["last_ok"] = True
        state["last_mode"] = "ocr_direct"
        state["last_finished_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        _save_json(state_path, state)
        _append_log(output_dir, "OCR_FALLBACK OK")
    except Exception as exc:
        result["error"] = str(exc)
        state = _load_json(state_path)
        state["last_ok"] = False
        state["last_mode"] = "ocr_direct_fail"
        state["last_error"] = str(exc)[:300]
        _save_json(state_path, state)
        _append_log(output_dir, f"OCR_FALLBACK FAIL: {exc}")
    finally:
        _mark_ocr_in_flight(output_dir, on=False)

    return result


def start_hotspot_ocr_fallback_subprocess(output_dir: str, base_script_dir: str) -> tuple[bool, str]:
    """watch 에서 Cursor 불가 시 백그라운드 OCR force."""
    ok, reason = should_run_hotspot_session(output_dir)
    if not ok:
        return False, reason

    _mark_ocr_in_flight(output_dir, on=True)
    handler_py = os.path.join(base_script_dir, "gc1_runtime", "layer0_hotspot_agent.py")
    cmd = [sys.executable, handler_py, "--ocr-fallback-once", "--output-dir", output_dir]
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
        _mark_ocr_in_flight(output_dir, on=False)
        return False, f"OCR 폴백 프로세스 시작 실패: {exc}"

    _append_log(output_dir, "ENQUEUE ocr_direct_fallback")
    return True, "Cursor 없음 — Python OCR force 파이프라인 시작 (Autochro eye)"


def dispatch_gc1_hotspot_session(
    output_dir: str,
    base_script_dir: str,
    *,
    ssid: str,
    just_connected: bool,
    chemstation_mode: str = "gc1",
) -> tuple[DispatchAction, str]:
    """
    GC1 핫스팟 edge 디스패치.
    cursor_enqueued | ocr_started | skip | continue_legacy | in_flight
    """
    if not hotspot_cursor_agent_enabled():
        return "continue_legacy", ""

    if is_hotspot_session_in_flight(output_dir):
        return "in_flight", "핫스팟 처리 실행 중"

    ok_session, session_reason = should_run_hotspot_session(
        output_dir, chemstation_mode=chemstation_mode
    )
    if not ok_session:
        return "skip", session_reason

    sdk_ok, sdk_reason = cursor_sdk_ready()
    if sdk_ok:
        triggered, agent_msg = enqueue_hotspot_cursor_agent(
            output_dir,
            base_script_dir,
            ssid=ssid,
            just_connected=just_connected,
            chemstation_mode=chemstation_mode,
        )
        if triggered:
            return "cursor_enqueued", agent_msg

    started, ocr_msg = start_hotspot_ocr_fallback_subprocess(output_dir, base_script_dir)
    if started:
        detail = f"{ocr_msg} ({sdk_reason})" if not sdk_ok else ocr_msg
        return "ocr_started", detail
    return "skip", ocr_msg


def collect_hotspot_agent_status(output_dir: str, *, ssid: str | None = None) -> dict[str, Any]:
    """확인용 — ``--status`` / watch 점검."""
    from gc_wifi import get_connected_wifi_ssid, is_required_hotspot_connected

    state = _load_json(_state_path(output_dir))
    cooldown = hotspot_reconnect_min_sec("gc1")
    remain = _cooldown_remaining_sec(state, cooldown)
    sdk_ok, sdk_reason = cursor_sdk_ready()
    required = os.getenv("REQUIRED_HOTSPOT", "iPhone").strip() or "iPhone"
    connected = is_required_hotspot_connected(required, skip_wifi_check=False)
    current_ssid = ssid or get_connected_wifi_ssid()

    ocr_env = {k: os.getenv(k, "(미설정)") for k in _GC1_OCR_ENV_DEFAULTS}

    return {
        "hotspot_cursor_agent": hotspot_cursor_agent_enabled(),
        "wifi_required_ssid": required,
        "wifi_connected": connected,
        "wifi_current_ssid": current_ssid,
        "cursor_sdk_ready": sdk_ok,
        "cursor_sdk_detail": sdk_reason,
        "cooldown_sec": cooldown,
        "cooldown_remaining_sec": int(remain),
        "session_in_flight": is_hotspot_session_in_flight(output_dir),
        "agent_in_flight": is_hotspot_agent_in_flight(output_dir),
        "ocr_in_flight": is_ocr_fallback_in_flight(output_dir),
        "last_mode": state.get("last_mode"),
        "last_finished_at": state.get("last_finished_at"),
        "last_ok": state.get("last_ok"),
        "ocr_env": ocr_env,
        "log_file": _log_path(output_dir),
        "state_file": _state_path(output_dir),
    }


def print_hotspot_agent_status(output_dir: str) -> None:
    status = collect_hotspot_agent_status(output_dir)
    mins, secs = divmod(status["cooldown_remaining_sec"], 60)
    print("=== GC1 핫스팟 → Cursor / OCR 상태 ===")
    print(f"Wi-Fi 필요 SSID     : {status['wifi_required_ssid']}")
    print(f"Wi-Fi 현재 SSID     : {status['wifi_current_ssid'] or '(없음)'}")
    print(f"Wi-Fi 연결 OK       : {'예' if status['wifi_connected'] else '아니오'}")
    print(f"에이전트 모드       : {'켜짐' if status['hotspot_cursor_agent'] else '꺼짐(레거시 pipeline)'}")
    print(f"Cursor SDK          : {status['cursor_sdk_detail']}")
    print(f"쿨다운              : {status['cooldown_sec']}초 (남음 {mins}분 {secs}초)")
    print(f"실행 중             : {'예' if status['session_in_flight'] else '아니오'}")
    print(f"마지막 모드         : {status.get('last_mode') or '-'}")
    print(f"마지막 완료         : {status.get('last_finished_at') or '-'}")
    print(f"마지막 성공         : {status.get('last_ok')}")
    print("OCR env:")
    for key, val in status["ocr_env"].items():
        print(f"  {key}={val}")
    print(f"상태 파일           : {status['state_file']}")
    print(f"로그 파일           : {status['log_file']}")
    if status["cursor_sdk_ready"]:
        print("다음 핫스팟 연결 시: Cursor 에이전트「동작해」요청")
    else:
        print("다음 핫스팟 연결 시: Cursor 없이 Python OCR force 자동 실행")


def main() -> None:
    parser = argparse.ArgumentParser(description="GC1 핫스팟 → Cursor 에이전트 / OCR 폴백")
    parser.add_argument("--trigger-once", action="store_true", help="pending Cursor 1건 처리")
    parser.add_argument("--ocr-fallback-once", action="store_true", help="OCR force 1회 (Cursor 없을 때)")
    parser.add_argument("--status", action="store_true", help="핫스팟·SDK·OCR·쿨다운 상태 출력")
    parser.add_argument("--output-dir", default="", help="Desktop\\박은규 등 excel 출력 폴더")
    args = parser.parse_args()

    from gc_profiles import paths_for_output_dir, resolve_profile, script_dir

    base = script_dir()
    profile = resolve_profile(base)
    paths = paths_for_output_dir(profile.excel_output_dir, gc_instance=profile.gc_instance)
    output_dir = args.output_dir.strip() or paths["runtime_dir"]

    if args.status:
        print_hotspot_agent_status(output_dir)
        return

    if args.ocr_fallback_once:
        result = run_hotspot_ocr_fallback_once(output_dir, base)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return

    if args.trigger_once:
        result = trigger_hotspot_cursor_agent_once(output_dir, base)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return

    parser.print_help()


if __name__ == "__main__":
    main()
