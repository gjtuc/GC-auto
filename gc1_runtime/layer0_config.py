# -*- coding: utf-8 -*-
"""
B-CFG 프로브 (Ω.A.B.CFG.*) — env 키마다 READ→TRIM→DEFAULT→VALID 4 leaf.

설계: ``deploy/GC1_RUNTIME_DESIGN.md`` §B-CFG (19키 × 4 = 76 leaf).
``gc_autochro`` 와 동일한 bool 파싱(1/true/yes/on). invalid 시 **default fallback**.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Callable, Mapping

# 타입 별칭 — 테스트 시 dict 주입
EnvMap = Mapping[str, str]

_TRUE_TOKENS = frozenset({"1", "true", "yes", "on"})
_FALSE_TOKENS = frozenset({"0", "false", "no", "off", ""})


def _default_desktop_dir() -> str:
    """Ω.A.B.CFG.07c — 분석방법 MTD 기본 폴더 (바탕화면)."""
    return os.path.normpath(os.path.expanduser("~/Desktop"))


def leaf_read(env: EnvMap | None, key: str) -> str | None:
    """Ω.A.B.CFG.*a — READ (os.getenv 또는 주입 env)."""
    if env is not None:
        if key in env:
            return env[key]
        return None
    return os.getenv(key)


def leaf_trim(raw: str | None) -> str:
    """Ω.A.B.CFG.*b — TRIM."""
    return (raw or "").strip()


def parse_bool(trimmed: str, default: bool) -> bool:
    """Ω.A.B.CFG.*d bool — invalid·빈 값이면 default."""
    low = trimmed.lower()
    if not low:
        return default
    if low in _TRUE_TOKENS:
        return True
    if low in _FALSE_TOKENS:
        return False
    return default


def parse_int_nonneg(trimmed: str, default: int) -> int:
    """Ω.A.B.CFG.*d int≥0 — 음수·비숫자면 default."""
    if not trimmed:
        return default
    try:
        value = int(trimmed)
    except ValueError:
        return default
    return value if value >= 0 else default


def parse_int(trimmed: str, default: int) -> int:
    """Ω.A.B.CFG.04d/05d — 일반 int (음수 허용, 창 좌표용)."""
    if not trimmed:
        return default
    try:
        return int(trimmed)
    except ValueError:
        return default


def parse_frac(trimmed: str, default: float) -> float:
    """Ω.A.B.CFG.06d — 0 < f < 1, 아니면 default."""
    if not trimmed:
        return default
    try:
        value = float(trimmed)
    except ValueError:
        return default
    if value <= 0.0 or value >= 1.0:
        return default
    return value


def parse_nonempty_str(trimmed: str, default: str) -> str:
    """Ω.A.B.CFG.02d — 빈 문자열이면 default."""
    return trimmed if trimmed else default


def parse_optional_str(trimmed: str) -> str:
    """Ω.A.B.CFG.14d — 빈 값 허용 (UI fallback 경로)."""
    return trimmed


def parse_optional_file(trimmed: str) -> str:
    """Ω.A.B.CFG.13d — 파일이 없으면 빈 문자열 (optional)."""
    if not trimmed:
        return ""
    path = os.path.normpath(os.path.expanduser(trimmed))
    return path if os.path.isfile(path) else ""


def parse_isdir_path(trimmed: str, default: str) -> str:
    """Ω.A.B.CFG.07d — 디렉터리 아니면 default."""
    if not trimmed:
        candidate = default
    else:
        candidate = os.path.normpath(os.path.expanduser(trimmed))
    if os.path.isdir(candidate):
        return candidate
    if os.path.isdir(default):
        return default
    return candidate


def parse_hotspot_csv(trimmed: str, default: str) -> tuple[str, ...]:
    """Ω.A.B.CFG.18d — 쉼표 구분 SSID 목록."""
    raw = trimmed if trimmed else default
    return tuple(part.strip() for part in raw.split(",") if part.strip())


def _read_key(
    env: EnvMap | None,
    key: str,
    *,
    default_str: str,
    parser: Callable[[str], object],
) -> object:
    """4-leaf 파이프라인 공통."""
    trimmed = leaf_trim(leaf_read(env, key))
    if not trimmed:
        trimmed = default_str
    return parser(trimmed)


# --- 키별 read_* (Ω.A.B.CFG.01~19) ---


def read_autochro_enabled(env: EnvMap | None = None) -> bool:
    return bool(
        _read_key(
            env,
            "AUTOCHRO_ENABLED",
            default_str="0",
            parser=lambda s: parse_bool(s, False),
        )
    )


def read_window_title_pattern(env: EnvMap | None = None) -> str:
    return str(
        _read_key(
            env,
            "AUTOCHRO_WINDOW_TITLE_PATTERN",
            default_str="Autochro",
            parser=lambda s: parse_nonempty_str(s, "Autochro"),
        )
    )


def read_auto_position(env: EnvMap | None = None) -> bool:
    return bool(
        _read_key(
            env,
            "AUTOCHRO_AUTO_POSITION",
            default_str="1",
            parser=lambda s: parse_bool(s, True),
        )
    )


def read_window_x(env: EnvMap | None = None) -> int:
    return int(
        _read_key(
            env,
            "AUTOCHRO_WINDOW_X",
            default_str="40",
            parser=lambda s: parse_int(s, 40),
        )
    )


def read_window_y(env: EnvMap | None = None) -> int:
    return int(
        _read_key(
            env,
            "AUTOCHRO_WINDOW_Y",
            default_str="40",
            parser=lambda s: parse_int(s, 40),
        )
    )


def read_list_neutral_x_frac(env: EnvMap | None = None) -> float:
    return float(
        _read_key(
            env,
            "AUTOCHRO_LIST_NEUTRAL_X_FRAC",
            default_str="0.78",
            parser=lambda s: parse_frac(s, 0.78),
        )
    )


def read_analysis_method_dir(env: EnvMap | None = None) -> str:
    desktop = _default_desktop_dir()
    trimmed = leaf_trim(leaf_read(env, "AUTOCHRO_ANALYSIS_METHOD_DIR"))
    return parse_isdir_path(trimmed, desktop)


def read_gc1_autochro_prep_steps(env: EnvMap | None = None) -> bool:
    return bool(
        _read_key(
            env,
            "GC1_AUTOCHRO_PREP_STEPS",
            default_str="1",
            parser=lambda s: parse_bool(s, True),
        )
    )


def read_hancom_wait_sec(env: EnvMap | None = None) -> int:
    return int(
        _read_key(
            env,
            "AUTOCHRO_HANCOM_WAIT_SEC",
            default_str="120",
            parser=lambda s: parse_int_nonneg(s, 120),
        )
    )


def read_quantify_wait_sec(env: EnvMap | None = None) -> int:
    return int(
        _read_key(
            env,
            "AUTOCHRO_QUANTIFY_WAIT_SEC",
            default_str="60",
            parser=lambda s: parse_int_nonneg(s, 60),
        )
    )


def read_dialog_wait_sec(env: EnvMap | None = None) -> int:
    return int(
        _read_key(
            env,
            "AUTOCHRO_DIALOG_WAIT_SEC",
            default_str="30",
            parser=lambda s: parse_int_nonneg(s, 30),
        )
    )


def read_pdf_ready_wait_sec(env: EnvMap | None = None) -> int:
    return int(
        _read_key(
            env,
            "GC1_PDF_READY_WAIT_SEC",
            default_str="90",
            parser=lambda s: parse_int_nonneg(s, 90),
        )
    )


def read_crm_path(env: EnvMap | None = None) -> str:
    trimmed = leaf_trim(leaf_read(env, "AUTOCHRO_CRM_PATH"))
    return parse_optional_file(trimmed)


def read_data_name(env: EnvMap | None = None) -> str:
    trimmed = leaf_trim(leaf_read(env, "AUTOCHRO_DATA_NAME"))
    return parse_optional_str(trimmed)


def read_gc1_use_runtime(env: EnvMap | None = None) -> bool:
    return bool(
        _read_key(
            env,
            "GC1_USE_RUNTIME",
            default_str="0",
            parser=lambda s: parse_bool(s, False),
        )
    )


def read_gc1_runtime_verify_eye(env: EnvMap | None = None) -> bool:
    return bool(
        _read_key(
            env,
            "GC1_RUNTIME_VERIFY_EYE",
            default_str="0",
            parser=lambda s: parse_bool(s, False),
        )
    )


def read_gc1_skip_autochro_export(env: EnvMap | None = None) -> bool:
    return bool(
        _read_key(
            env,
            "GC1_SKIP_AUTOCHRO_EXPORT",
            default_str="0",
            parser=lambda s: parse_bool(s, False),
        )
    )


def read_required_hotspot(env: EnvMap | None = None) -> tuple[str, ...]:
    trimmed = leaf_trim(leaf_read(env, "REQUIRED_HOTSPOT"))
    return parse_hotspot_csv(trimmed, "iPhone")


def read_hotspot_reconnect_min_sec(env: EnvMap | None = None) -> int:
    return int(
        _read_key(
            env,
            "GC1_HOTSPOT_RECONNECT_MIN_SEC",
            default_str="90",
            parser=lambda s: parse_int_nonneg(s, 90),
        )
    )


@dataclass(frozen=True)
class Gc1RuntimeConfig:
    """19개 B-CFG 키를 한 번에 로드한 스냅샷."""

    autochro_enabled: bool
    window_title_pattern: str
    auto_position: bool
    window_x: int
    window_y: int
    list_neutral_x_frac: float
    analysis_method_dir: str
    gc1_autochro_prep_steps: bool
    hancom_wait_sec: int
    quantify_wait_sec: int
    dialog_wait_sec: int
    pdf_ready_wait_sec: int
    crm_path: str
    data_name: str
    gc1_use_runtime: bool
    gc1_runtime_verify_eye: bool
    gc1_skip_autochro_export: bool
    required_hotspot: tuple[str, ...]
    hotspot_reconnect_min_sec: int


class ConfigReader:
    """B-CFG 로더 — ``env`` dict 주입으로 단위 테스트 격리."""

    def load(self, env: EnvMap | None = None) -> Gc1RuntimeConfig:
        return Gc1RuntimeConfig(
            autochro_enabled=read_autochro_enabled(env),
            window_title_pattern=read_window_title_pattern(env),
            auto_position=read_auto_position(env),
            window_x=read_window_x(env),
            window_y=read_window_y(env),
            list_neutral_x_frac=read_list_neutral_x_frac(env),
            analysis_method_dir=read_analysis_method_dir(env),
            gc1_autochro_prep_steps=read_gc1_autochro_prep_steps(env),
            hancom_wait_sec=read_hancom_wait_sec(env),
            quantify_wait_sec=read_quantify_wait_sec(env),
            dialog_wait_sec=read_dialog_wait_sec(env),
            pdf_ready_wait_sec=read_pdf_ready_wait_sec(env),
            crm_path=read_crm_path(env),
            data_name=read_data_name(env),
            gc1_use_runtime=read_gc1_use_runtime(env),
            gc1_runtime_verify_eye=read_gc1_runtime_verify_eye(env),
            gc1_skip_autochro_export=read_gc1_skip_autochro_export(env),
            required_hotspot=read_required_hotspot(env),
            hotspot_reconnect_min_sec=read_hotspot_reconnect_min_sec(env),
        )


def load_gc1_runtime_config(env: EnvMap | None = None) -> Gc1RuntimeConfig:
    """편의 함수 — ConfigReader().load() 와 동일."""
    return ConfigReader().load(env)
