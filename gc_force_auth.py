# -*- coding: utf-8 -*-
"""force / --request 실행 시 선택적 GC_FORCE_TOKEN 검증."""
from __future__ import annotations

import os
import secrets
import sys


def configured_force_token() -> str:
    return os.getenv("GC_FORCE_TOKEN", "").strip()


def force_authorized(provided: str | None = None) -> bool:
    expected = configured_force_token()
    if not expected:
        return True
    candidate = (provided or os.getenv("GC_FORCE_INVOKE", "")).strip()
    if not candidate:
        return False
    return secrets.compare_digest(candidate, expected)


def require_force_auth(provided: str | None = None) -> None:
    if force_authorized(provided):
        return
    print(
        "[오류] force 실행 거부 - GC_FORCE_TOKEN 이 설정되어 있습니다.\n"
        "       gc_동작해줘.bat / gc_run_force.bat 사용, 또는\n"
        "       --force-token <토큰> (gc_automation.env 의 GC_FORCE_TOKEN)"
    )
    raise SystemExit(3)


def print_invoke_token_for_bat() -> None:
    """bat for /f — gc_automation.env 의 GC_FORCE_TOKEN 출력."""
    from gc_profiles import bootstrap_env

    script_dir = os.path.dirname(os.path.abspath(__file__))
    bootstrap_env(script_dir)
    sys.stdout.write(configured_force_token())


if __name__ == "__main__":
    print_invoke_token_for_bat()
