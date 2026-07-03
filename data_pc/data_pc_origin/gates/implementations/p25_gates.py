# -*- coding: utf-8
"""P25 L4 gate bodies — native env production live."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

from data_pc_origin.gates.registry import P25_DEPS, register_gate
from data_pc_origin.live_native_production import ARTIFACT_NAME, run_live_native_production
from data_pc_origin.p19_live_assert import fixture_ok_imap_payload
from data_pc_origin.p25_native_live import (
    NATIVE_LIVE_ENV,
    native_live_enabled,
    prep_native_production_live,
    run_native_production_imap_once,
    validate_native_live_artifact,
)


def _assert(condition: bool, msg: str = "") -> None:
    if not condition:
        raise AssertionError(msg or "assertion failed")


def _script_dir() -> str:
    return str(Path(__file__).resolve().parents[2].parent)


def _gate_p25_n_01_a_1() -> None:
    prep = prep_native_production_live(_script_dir())
    _assert(prep.skip_origin is False, "SKIP_ORIGIN should be 0 in env file")
    _assert(prep.full_e2e_ready is True)


def _gate_p25_n_02_a_1() -> None:
    with patch("data_pc_origin.p18_production_e2e.apply_production_e2e_env") as mocked:
        with patch(
            "data_pc_origin.live_imap.run_live_imap",
            return_value={"status": "skipped", "reason": "no pending"},
        ):
            run_native_production_imap_once()
    _assert(not mocked.called)


def _gate_p25_n_03_a_1() -> None:
    prep = prep_native_production_live(_script_dir())
    _assert(prep.ops_ready is True)


def _gate_p25_n_04_a_1() -> None:
    _assert(native_live_enabled({NATIVE_LIVE_ENV: "1"}))
    _assert(not native_live_enabled({NATIVE_LIVE_ENV: "0"}))


def _gate_p25_h_01_a_1() -> None:
    root = Path(__file__).resolve().parents[2]
    out = run_live_native_production(artifact_dir=root)
    _assert(out["status"] in ("ok", "partial"))
    _assert(out.get("native_env") is True)


def _gate_p25_h_02_a_1() -> None:
    root = Path(__file__).resolve().parents[2]
    _assert((root / ARTIFACT_NAME).is_file())


def _gate_p25_h_03_a_1() -> None:
    out = run_live_native_production(live=True)
    _assert(out["mode"] == "live")
    _assert(out["status"] == "skipped")


def _gate_p25_h_04_a_1() -> None:
    with patch(
        "data_pc_origin.live_native_production.run_native_production_imap_once",
        return_value=fixture_ok_imap_payload(),
    ):
        with patch.dict("os.environ", {NATIVE_LIVE_ENV: "1"}, clear=False):
            out = run_live_native_production(live=True)
    _assert(out["mode"] == "live")
    _assert(out.get("validation", {}).get("ok") is True)
    _assert(validate_native_live_artifact(out))


_P25_GATES: list[tuple[str, object]] = [
    ("P25-N-01-a-1", _gate_p25_n_01_a_1),
    ("P25-N-02-a-1", _gate_p25_n_02_a_1),
    ("P25-N-03-a-1", _gate_p25_n_03_a_1),
    ("P25-N-04-a-1", _gate_p25_n_04_a_1),
    ("P25-H-01-a-1", _gate_p25_h_01_a_1),
    ("P25-H-02-a-1", _gate_p25_h_02_a_1),
    ("P25-H-03-a-1", _gate_p25_h_03_a_1),
    ("P25-H-04-a-1", _gate_p25_h_04_a_1),
]


def register_p25_gates() -> None:
    for gate_id, fn in _P25_GATES:
        register_gate(gate_id, fn, depends=P25_DEPS[gate_id], layer="P25")  # type: ignore[arg-type]
