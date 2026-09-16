# -*- coding: utf-8 -*-
"""데이터 PC 실행 증거 — 콘솔이 닫혀도 남는 기록.

한 줄 = JSON. 경로:
  %USERPROFILE%\\.cursor\\gc-runtime-temp\\data_pc_run_evidence.jsonl
  %USERPROFILE%\\.cursor\\gc-runtime-temp\\data_pc_run_latest.txt

메일 비밀번호·토큰은 기록하지 않는다.
"""

from __future__ import annotations

import json
import os
import traceback
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

_RUN_ID: Optional[str] = None
_WARN_COUNT = 0
_FAIL_COUNT = 0


def evidence_dir() -> Path:
    override = os.environ.get("DATA_PC_EVIDENCE_DIR", "").strip()
    path = Path(override) if override else Path.home() / ".cursor" / "gc-runtime-temp"
    path.mkdir(parents=True, exist_ok=True)
    return path


def jsonl_path() -> Path:
    return evidence_dir() / "data_pc_run_evidence.jsonl"


def latest_path() -> Path:
    return evidence_dir() / "data_pc_run_latest.txt"


def current_run_id() -> Optional[str]:
    return _RUN_ID


def _now() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def _redact(text: str) -> str:
    raw = str(text or "")
    lowered = raw.lower()
    markers = (
        "password",
        "app_password",
        "secret",
        "api_key",
        "credentials",
    )
    if any(m in lowered for m in markers):
        return "[redacted]"
    return raw[:8000]


def _append(event: dict[str, Any]) -> None:
    line = json.dumps(event, ensure_ascii=False)
    try:
        with jsonl_path().open("a", encoding="utf-8") as fh:
            fh.write(line + "\n")
    except OSError:
        return
    try:
        latest_path().write_text(
            f"{event.get('ts')} {event.get('event')} stage={event.get('stage', '')} "
            f"ok={event.get('ok', '')} sample={event.get('sample', '')}\n"
            f"{event.get('detail') or event.get('exc') or ''}\n",
            encoding="utf-8",
        )
    except OSError:
        pass


def begin_run(trigger: str) -> str:
    """실행 시작. 이미 열린 run 이 있으면 그 id 를 재사용."""
    global _RUN_ID, _WARN_COUNT, _FAIL_COUNT
    if _RUN_ID:
        return _RUN_ID
    _WARN_COUNT = 0
    _FAIL_COUNT = 0
    _RUN_ID = datetime.now().strftime("%Y%m%d-%H%M%S") + "-" + uuid.uuid4().hex[:6]
    _append(
        {
            "ts": _now(),
            "run_id": _RUN_ID,
            "event": "run_start",
            "stage": "run",
            "ok": True,
            "trigger": _redact(trigger),
            "computer": os.environ.get("COMPUTERNAME", ""),
        }
    )
    return _RUN_ID


def record(
    stage: str,
    ok: bool,
    *,
    sample: str = "",
    mail_id: str = "",
    detail: str = "",
    exc: BaseException | None = None,
) -> None:
    """단계 성공/실패. 예외가 있으면 traceback 까지 남긴다."""
    global _FAIL_COUNT
    if not ok:
        _FAIL_COUNT += 1
    begin_run("implicit")
    event: dict[str, Any] = {
        "ts": _now(),
        "run_id": _RUN_ID,
        "event": "stage",
        "stage": stage,
        "ok": bool(ok),
        "sample": _redact(sample)[:300],
        "mail_id": _redact(mail_id)[:200],
        "detail": _redact(detail),
    }
    if exc is not None:
        event["exc_type"] = type(exc).__name__
        event["exc"] = _redact(str(exc))
        event["traceback"] = _redact(traceback.format_exc())
    _append(event)


def warn(code: str, message: str, *, sample: str = "") -> None:
    """계산 경고·교차검증처럼 실패는 아닌 이상."""
    global _WARN_COUNT
    _WARN_COUNT += 1
    begin_run("implicit")
    _append(
        {
            "ts": _now(),
            "run_id": _RUN_ID,
            "event": "warn",
            "stage": "calc",
            "ok": True,
            "code": _redact(code)[:80],
            "sample": _redact(sample)[:300],
            "detail": _redact(message),
        }
    )


def note_swallowed(where: str, exc: BaseException) -> None:
    """except pass 로 삼킨 예외를 한 줄이라도 남긴다. 끝난 run 을 다시 열지 않는다."""
    _append(
        {
            "ts": _now(),
            "run_id": _RUN_ID or "none",
            "event": "swallowed",
            "stage": where,
            "ok": False,
            "exc_type": type(exc).__name__,
            "exc": _redact(str(exc)),
            "traceback": _redact(traceback.format_exc()),
        }
    )


def emit_calc(sample: str, warnings, *, ok: bool = True, detail: str = "") -> None:
    """계산 경고와 실패를 같은 실행 기록에 남긴다."""
    for message in warnings or []:
        warn("calc", str(message), sample=sample)
    if not ok:
        record("calc", False, sample=sample, detail=detail or "계산 실패")


def close_run(ok: bool, *, detail: str = "") -> None:
    global _RUN_ID
    if not _RUN_ID:
        return
    run_id = _RUN_ID
    _append(
        {
            "ts": _now(),
            "run_id": run_id,
            "event": "run_end",
            "stage": "run",
            "ok": bool(ok) and _FAIL_COUNT == 0,
            "warn_count": _WARN_COUNT,
            "fail_count": _FAIL_COUNT,
            "detail": _redact(detail),
            "log": str(jsonl_path()),
        }
    )
    print(f"[증거] {jsonl_path()}")
    _RUN_ID = None
