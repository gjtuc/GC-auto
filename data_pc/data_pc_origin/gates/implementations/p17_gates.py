# -*- coding: utf-8
"""P17 L4 gate bodies — origin env defaults."""

from __future__ import annotations

import json
from pathlib import Path

from data_pc_origin.gates.registry import P17_DEPS, register_gate
from data_pc_origin.live_env import ARTIFACT_NAME, run_live_env
from data_pc_origin.p14_runtime_bridge import ORIGIN_PIPELINE_ENV
from data_pc_origin.p17_env_config import (
    ORIGIN_ENV_DEFAULTS,
    ORIGIN_STACK_KEYS,
    effective_origin_config,
    env_file_documents_origin_stack,
    is_secret_key,
    mask_env_value,
    merge_origin_defaults_into_text,
    missing_origin_defaults,
)


def _assert(condition: bool, msg: str = "") -> None:
    if not condition:
        raise AssertionError(msg or "assertion failed")


def _script_dir() -> str:
    return str(Path(__file__).resolve().parents[2].parent)


def _chaheon_example() -> Path:
    return Path(_script_dir()) / "GC-auto-push" / "deploy" / "gc_automation.env.chaheon.example"


def _gate_p17_e_01_a_1() -> None:
    _assert(ORIGIN_PIPELINE_ENV in ORIGIN_ENV_DEFAULTS)
    _assert(ORIGIN_ENV_DEFAULTS[ORIGIN_PIPELINE_ENV] == "1")
    _assert(len(ORIGIN_STACK_KEYS) >= 4)


def _gate_p17_e_02_a_1() -> None:
    cfg = effective_origin_config(
        _script_dir(),
        environ={ORIGIN_PIPELINE_ENV: "1", "DATA_PC_SKIP_ORIGIN": "1"},
    )
    _assert(cfg["origin_pipeline"] is True)
    _assert(cfg["watch_mode"] == "runtime_origin")


def _gate_p17_e_03_a_1() -> None:
    cfg = effective_origin_config(
        _script_dir(),
        environ={ORIGIN_PIPELINE_ENV: "1", "DATA_PC_SKIP_ORIGIN": "0"},
    )
    _assert(cfg["full_e2e_ready"] is True)


def _gate_p17_e_04_a_1() -> None:
    masked = mask_env_value("NAVER_APP_PASSWORD", "abcdefghijklmnop")
    _assert(masked == "***")
    _assert(is_secret_key("IPTIME_WIFI_PSK"))


def _gate_p17_h_01_a_1() -> None:
    root = Path(__file__).resolve().parents[2]
    out = run_live_env(artifact_dir=root, script_dir=_script_dir())
    _assert(out["status"] == "ok")
    _assert(out["mode"] == "effective_config")


def _gate_p17_h_02_a_1() -> None:
    root = Path(__file__).resolve().parents[2]
    _assert((root / ARTIFACT_NAME).is_file())


def _gate_p17_h_03_a_1() -> None:
    example = _chaheon_example()
    _assert(example.is_file())
    _assert(env_file_documents_origin_stack(str(example)))


def _gate_p17_h_04_a_1() -> None:
    env_path = str(Path(_script_dir()) / "gc_automation.env")
    _assert(env_file_documents_origin_stack(env_path))
    missing = missing_origin_defaults(env_path)
    _assert(ORIGIN_PIPELINE_ENV not in missing)
    merged = merge_origin_defaults_into_text("# test\nFOO=1\n")
    _assert(ORIGIN_PIPELINE_ENV in merged)


_P17_GATES: list[tuple[str, object]] = [
    ("P17-E-01-a-1", _gate_p17_e_01_a_1),
    ("P17-E-02-a-1", _gate_p17_e_02_a_1),
    ("P17-E-03-a-1", _gate_p17_e_03_a_1),
    ("P17-E-04-a-1", _gate_p17_e_04_a_1),
    ("P17-H-01-a-1", _gate_p17_h_01_a_1),
    ("P17-H-02-a-1", _gate_p17_h_02_a_1),
    ("P17-H-03-a-1", _gate_p17_h_03_a_1),
    ("P17-H-04-a-1", _gate_p17_h_04_a_1),
]


def register_p17_gates() -> None:
    for gate_id, fn in _P17_GATES:
        register_gate(gate_id, fn, depends=P17_DEPS[gate_id], layer="P17")  # type: ignore[arg-type]
