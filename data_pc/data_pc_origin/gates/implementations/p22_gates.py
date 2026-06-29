# -*- coding: utf-8
"""P22 L4 gate bodies — autostart / watch integration smoke."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

from data_pc_origin.gates.registry import P22_DEPS, register_gate
from data_pc_origin.live_autostart import ARTIFACT_NAME, run_live_autostart
from data_pc_origin.p14_runtime_bridge import ORIGIN_PIPELINE_ENV
from data_pc_origin.p16_watch_bridge import LEGACY_WATCH_ENV
from data_pc_origin.p22_autostart import (
    build_autostart_manifest,
    scan_autostart_artifact,
    validate_autostart_artifact,
    verify_vbs_runtime_entry,
    verify_watchdog_delegation,
)


def _assert(condition: bool, msg: str = "") -> None:
    if not condition:
        raise AssertionError(msg or "assertion failed")


def _script_dir() -> str:
    return str(Path(__file__).resolve().parents[2].parent)


def _gate_p22_a_01_a_1() -> None:
    m = build_autostart_manifest(_script_dir())
    _assert(all(m.artifacts.values()), f"missing: {[k for k, v in m.artifacts.items() if not v]}")


def _gate_p22_a_02_a_1() -> None:
    chk = verify_vbs_runtime_entry(_script_dir())
    _assert(chk.ok, chk.detail)


def _gate_p22_a_03_a_1() -> None:
    chk = verify_watchdog_delegation(_script_dir())
    _assert(chk.ok, chk.detail)


def _gate_p22_a_04_a_1() -> None:
    from data_pc_watch import run_data_pc_watch

    with patch("data_pc_origin.p16_watch_bridge.run_watch_via_runtime") as mocked:
        run_data_pc_watch(_script_dir(), skip_wifi_check=True)
    _assert(mocked.called)


def _gate_p22_h_01_a_1() -> None:
    root = Path(__file__).resolve().parents[2]
    out = run_live_autostart(artifact_dir=root, script_dir=_script_dir())
    _assert(out["status"] == "ok")
    _assert(out.get("artifact_valid") is True)


def _gate_p22_h_02_a_1() -> None:
    root = Path(__file__).resolve().parents[2]
    _assert((root / ARTIFACT_NAME).is_file())


def _gate_p22_h_03_a_1() -> None:
    m = build_autostart_manifest(
        _script_dir(),
        environ={ORIGIN_PIPELINE_ENV: "1", LEGACY_WATCH_ENV: "0"},
    )
    _assert(m.ready)
    _assert(m.watch_mode == "runtime_origin")


def _gate_p22_h_04_a_1() -> None:
    root = Path(__file__).resolve().parents[2]
    out = run_live_autostart(artifact_dir=root, script_dir=_script_dir())
    _assert(validate_autostart_artifact(out))
    bat = scan_autostart_artifact(_script_dir(), "gc_data_pc_watch_loop.bat")
    _assert(bat.ok, bat.detail)


_P22_GATES: list[tuple[str, object]] = [
    ("P22-A-01-a-1", _gate_p22_a_01_a_1),
    ("P22-A-02-a-1", _gate_p22_a_02_a_1),
    ("P22-A-03-a-1", _gate_p22_a_03_a_1),
    ("P22-A-04-a-1", _gate_p22_a_04_a_1),
    ("P22-H-01-a-1", _gate_p22_h_01_a_1),
    ("P22-H-02-a-1", _gate_p22_h_02_a_1),
    ("P22-H-03-a-1", _gate_p22_h_03_a_1),
    ("P22-H-04-a-1", _gate_p22_h_04_a_1),
]


def register_p22_gates() -> None:
    for gate_id, fn in _P22_GATES:
        register_gate(gate_id, fn, depends=P22_DEPS[gate_id], layer="P22")  # type: ignore[arg-type]
