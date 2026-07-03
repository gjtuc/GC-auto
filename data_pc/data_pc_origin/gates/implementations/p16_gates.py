# -*- coding: utf-8
"""P16 L4 gate bodies — watch → runtime supervisor."""

from __future__ import annotations

import os
from pathlib import Path
from unittest.mock import patch

from data_pc_origin.gates.registry import P16_DEPS, register_gate
from data_pc_origin.live_watch import ARTIFACT_NAME, run_live_watch
from data_pc_origin.p16_watch_bridge import (
    LEGACY_WATCH_ENV,
    ORIGIN_PIPELINE_ENV,
    describe_watch_mode,
    run_watch_via_runtime,
    should_use_runtime_watch,
)


def _assert(condition: bool, msg: str = "") -> None:
    if not condition:
        raise AssertionError(msg or "assertion failed")


def _script_dir() -> str:
    return str(Path(__file__).resolve().parents[2].parent)


def _gate_p16_w_01_a_1() -> None:
    _assert(should_use_runtime_watch({LEGACY_WATCH_ENV: "0"}))


def _gate_p16_w_02_a_1() -> None:
    _assert(not should_use_runtime_watch({LEGACY_WATCH_ENV: "1"}))
    _assert(describe_watch_mode({LEGACY_WATCH_ENV: "1"}) == "legacy")


def _gate_p16_w_03_a_1() -> None:
    with patch("data_pc_runtime.layer4_supervisor.run_supervisor") as mocked:
        run_watch_via_runtime(_script_dir(), skip_wifi_check=True)
        mocked.assert_called_once()


def _gate_p16_w_04_a_1() -> None:
    _assert(
        should_use_runtime_watch({ORIGIN_PIPELINE_ENV: "1", LEGACY_WATCH_ENV: "0"})
    )
    _assert(describe_watch_mode({ORIGIN_PIPELINE_ENV: "1"}) == "runtime_origin")


def _gate_p16_h_01_a_1() -> None:
    root = Path(__file__).resolve().parents[2]
    out = run_live_watch(artifact_dir=root, dry_tick=True, origin_pipeline=True)
    _assert(out["status"] == "ok")
    _assert(out["mode"] == "dry_tick")


def _gate_p16_h_02_a_1() -> None:
    root = Path(__file__).resolve().parents[2]
    _assert((root / ARTIFACT_NAME).is_file())


def _gate_p16_h_03_a_1() -> None:
    from data_pc_watch import run_data_pc_watch

    with patch(
        "data_pc_origin.p16_watch_bridge.should_use_runtime_watch",
        return_value=False,
    ):
        with patch("data_pc_origin.p16_watch_bridge.run_watch_via_runtime") as rt:
            with patch("data_pc_watch.load_watch_config", side_effect=SystemExit(0)):
                try:
                    run_data_pc_watch(_script_dir())
                except SystemExit:
                    pass
    _assert(not rt.called)


def _gate_p16_h_04_a_1() -> None:
    from data_pc_watch import run_data_pc_watch

    os.environ[LEGACY_WATCH_ENV] = "0"
    os.environ[ORIGIN_PIPELINE_ENV] = "1"
    with patch("data_pc_origin.p16_watch_bridge.run_watch_via_runtime") as mocked:
        mocked.return_value = None
        run_data_pc_watch(_script_dir(), skip_wifi_check=True)
    _assert(mocked.called)


_P16_GATES: list[tuple[str, object]] = [
    ("P16-W-01-a-1", _gate_p16_w_01_a_1),
    ("P16-W-02-a-1", _gate_p16_w_02_a_1),
    ("P16-W-03-a-1", _gate_p16_w_03_a_1),
    ("P16-W-04-a-1", _gate_p16_w_04_a_1),
    ("P16-H-01-a-1", _gate_p16_h_01_a_1),
    ("P16-H-02-a-1", _gate_p16_h_02_a_1),
    ("P16-H-03-a-1", _gate_p16_h_03_a_1),
    ("P16-H-04-a-1", _gate_p16_h_04_a_1),
]


def register_p16_gates() -> None:
    for gate_id, fn in _P16_GATES:
        register_gate(gate_id, fn, depends=P16_DEPS[gate_id], layer="P16")  # type: ignore[arg-type]
