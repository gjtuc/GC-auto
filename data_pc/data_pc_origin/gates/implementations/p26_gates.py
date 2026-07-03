# -*- coding: utf-8
"""P26 L4 gate bodies — watch resident smoke."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

from data_pc_origin.gates.registry import P26_DEPS, register_gate
from data_pc_origin.live_watch_resident import ARTIFACT_NAME, run_live_watch_resident
from data_pc_origin.p26_watch_resident import (
    inspect_watchdog_runtime_command,
    prep_watch_resident_smoke,
    run_watch_resident_delegate,
    validate_watch_resident_artifact,
)


def _assert(condition: bool, msg: str = "") -> None:
    if not condition:
        raise AssertionError(msg or "assertion failed")


def _script_dir() -> str:
    return str(Path(__file__).resolve().parents[2].parent)


def _gate_p26_w_01_a_1() -> None:
    prep = prep_watch_resident_smoke(_script_dir())
    _assert(prep.runtime_watch is True)
    _assert(prep.skip_origin is False)


def _gate_p26_w_02_a_1() -> None:
    state = {"n": 0}

    def _once(_sd: str) -> None:
        state["n"] += 1

    with patch("data_pc_runtime.layer4_supervisor.run_supervisor", side_effect=_once):
        run_watch_resident_delegate(_script_dir(), skip_wifi_check=True)
    _assert(state["n"] == 1)


def _gate_p26_w_03_a_1() -> None:
    wd = inspect_watchdog_runtime_command(_script_dir())
    _assert(wd["ok"] is True)


def _gate_p26_w_04_a_1() -> None:
    prep = prep_watch_resident_smoke(_script_dir())
    _assert(prep.watch_mode == "runtime_origin")
    _assert(prep.autostart_ready is True)


def _gate_p26_h_01_a_1() -> None:
    root = Path(__file__).resolve().parents[2]
    out = run_live_watch_resident(artifact_dir=root, script_dir=_script_dir())
    _assert(out["status"] in ("ok", "partial"))
    _assert(out.get("native_env") is True)


def _gate_p26_h_02_a_1() -> None:
    root = Path(__file__).resolve().parents[2]
    _assert((root / ARTIFACT_NAME).is_file())


def _gate_p26_h_03_a_1() -> None:
    root = Path(__file__).resolve().parents[2]
    out = run_live_watch_resident(artifact_dir=root, script_dir=_script_dir(), delegate=True)
    _assert(out["mode"] == "delegate")
    _assert(out["status"] == "ok")
    _assert(out.get("supervisor_called") is True)


def _gate_p26_h_04_a_1() -> None:
    root = Path(__file__).resolve().parents[2]
    out = run_live_watch_resident(artifact_dir=root, script_dir=_script_dir(), delegate=True)
    _assert(validate_watch_resident_artifact(out))


_P26_GATES: list[tuple[str, object]] = [
    ("P26-W-01-a-1", _gate_p26_w_01_a_1),
    ("P26-W-02-a-1", _gate_p26_w_02_a_1),
    ("P26-W-03-a-1", _gate_p26_w_03_a_1),
    ("P26-W-04-a-1", _gate_p26_w_04_a_1),
    ("P26-H-01-a-1", _gate_p26_h_01_a_1),
    ("P26-H-02-a-1", _gate_p26_h_02_a_1),
    ("P26-H-03-a-1", _gate_p26_h_03_a_1),
    ("P26-H-04-a-1", _gate_p26_h_04_a_1),
]


def register_p26_gates() -> None:
    for gate_id, fn in _P26_GATES:
        register_gate(gate_id, fn, depends=P26_DEPS[gate_id], layer="P26")  # type: ignore[arg-type]
