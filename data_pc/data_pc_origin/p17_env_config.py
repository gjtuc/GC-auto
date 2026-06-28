# -*- coding: utf-8
"""P17 — origin pipeline 운영 env 기본값·effective config."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Dict, List, Mapping, Optional

from data_pc_origin.p13_imap_adapter import mask_email
from data_pc_origin.p14_runtime_bridge import ORIGIN_PIPELINE_ENV, origin_pipeline_enabled
from data_pc_origin.p16_watch_bridge import (
    LEGACY_WATCH_ENV,
    RUNTIME_WATCH_ENV,
    describe_watch_mode,
)

SKIP_ORIGIN_ENV = "DATA_PC_SKIP_ORIGIN"

ORIGIN_STACK_KEYS: List[str] = [
    ORIGIN_PIPELINE_ENV,
    LEGACY_WATCH_ENV,
    RUNTIME_WATCH_ENV,
    SKIP_ORIGIN_ENV,
    "DATA_PC_SKIP_WIFI_CHECK",
    "DATA_PC_BOOT_MAIL_CHECK",
    "DATA_PC_WATCH_INTERVAL_SEC",
    "DATA_PC_GDRIVE_RETRY_SEC",
]

ORIGIN_ENV_DEFAULTS: Dict[str, str] = {
    ORIGIN_PIPELINE_ENV: "1",
    LEGACY_WATCH_ENV: "0",
    RUNTIME_WATCH_ENV: "1",
    SKIP_ORIGIN_ENV: "0",
}

SECRET_KEY_TOKENS = ("password", "psk", "secret", "token", "credential")


def load_script_env(script_dir: str) -> bool:
    """`gc_automation.env` 로드 — 파일 있으면 True."""
    env_path = os.path.join(script_dir, "gc_automation.env")
    if not os.path.isfile(env_path):
        return False
    try:
        from dotenv import load_dotenv

        load_dotenv(env_path)
        return True
    except ImportError:
        return False


def is_secret_key(key: str) -> bool:
    lower = key.lower()
    return any(token in lower for token in SECRET_KEY_TOKENS)


def mask_env_value(key: str, value: str) -> str:
    if not value:
        return ""
    if is_secret_key(key):
        return "***"
    if "email" in key.lower() and "@" in value:
        return mask_email(value)
    return value


def read_env_file_keys(env_path: str) -> Dict[str, str]:
    """`.env` 파일에서 KEY=VALUE (주석·빈 줄 제외)."""
    out: Dict[str, str] = {}
    if not os.path.isfile(env_path):
        return out
    for line in Path(env_path).read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        if "=" not in stripped:
            continue
        key, _, val = stripped.partition("=")
        out[key.strip()] = val.strip()
    return out


def effective_origin_config(
    script_dir: str,
    *,
    environ: Optional[Mapping[str, str]] = None,
) -> Dict[str, Any]:
    """로드 후 origin stack effective 값 (마스킹)."""
    load_script_env(script_dir)
    env = dict(environ if environ is not None else os.environ)
    raw: Dict[str, str] = {}
    masked: Dict[str, str] = {}
    for key in ORIGIN_STACK_KEYS:
        val = env.get(key, "")
        raw[key] = val
        masked[key] = mask_env_value(key, val)

    skip_raw = env.get(SKIP_ORIGIN_ENV, "").strip().lower()
    skip_origin = skip_raw in ("1", "true", "yes", "on")

    return {
        "script_dir": script_dir,
        "env_file": os.path.join(script_dir, "gc_automation.env"),
        "env_file_exists": os.path.isfile(os.path.join(script_dir, "gc_automation.env")),
        "origin_pipeline": origin_pipeline_enabled(env),
        "watch_mode": describe_watch_mode(env),
        "skip_origin": skip_origin,
        "full_e2e_ready": origin_pipeline_enabled(env) and not skip_origin,
        "keys": masked,
        "defaults": dict(ORIGIN_ENV_DEFAULTS),
    }


def env_file_documents_origin_stack(env_path: str) -> bool:
    """예시/실 env 파일에 ORIGIN_PIPELINE 키·주석이 있는지."""
    if not os.path.isfile(env_path):
        return False
    text = Path(env_path).read_text(encoding="utf-8")
    return ORIGIN_PIPELINE_ENV in text


def missing_origin_defaults(env_path: str) -> List[str]:
    """파일에 없는 권장 origin stack 키."""
    present = read_env_file_keys(env_path)
    missing: List[str] = []
    for key in (ORIGIN_PIPELINE_ENV, LEGACY_WATCH_ENV):
        if key not in present:
            missing.append(key)
    return missing


def merge_origin_defaults_into_text(text: str) -> str:
    """예시 env 텍스트에 P17 블록이 없으면 append."""
    if ORIGIN_PIPELINE_ENV in text:
        return text
    block = (
        "\n# --- P층 origin pipeline (P14–P16) ---\n"
        f"{ORIGIN_PIPELINE_ENV}=1\n"
        f"# {LEGACY_WATCH_ENV}=1   # 긴급: 구 data_pc_watch 루프\n"
        f"# {SKIP_ORIGIN_ENV}=0     # Origin COM full E2E\n"
    )
    return text.rstrip() + block + "\n"
