# -*- coding: utf-8
"""P18 L4 gate bodies — production full E2E."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

from data_pc_origin.gates.registry import P18_DEPS, register_gate
from data_pc_origin.live_production_e2e import ARTIFACT_NAME, run_live_production_e2e
from data_pc_origin.p14_runtime_bridge import ORIGIN_PIPELINE_ENV
from data_pc_origin.p18_production_e2e import (
    E2E_LIVE_ENV,
    PRODUCTION_STACK,
    apply_production_e2e_env,
    e2e_live_enabled,
    prepare_production_e2e,
)


def _assert(condition: bool, msg: str = "") -> None:
    if not condition:
        raise AssertionError(msg or "assertion failed")


def _script_dir() -> str:
    return str(Path(__file__).resolve().parents[2].parent)


def _gate_p18_p_01_a_1() -> None:
    prep = prepare_production_e2e(
        _script_dir(),
        environ={ORIGIN_PIPELINE_ENV: "1", "DATA_PC_SKIP_ORIGIN": "0"},
    )
    _assert(prep.stack == PRODUCTION_STACK)
    _assert(isinstance(prep.to_dict(), dict))


def _gate_p18_p_02_a_1() -> None:
    prep = prepare_production_e2e(
        _script_dir(),
        environ={ORIGIN_PIPELINE_ENV: "1", "DATA_PC_SKIP_ORIGIN": "0"},
    )
    _assert(prep.full_e2e_ready is True)


def _gate_p18_p_03_a_1() -> None:
    prep = prepare_production_e2e(
        _script_dir(),
        environ={ORIGIN_PIPELINE_ENV: "1", "DATA_PC_SKIP_ORIGIN": "1"},
    )
    _assert(prep.ready is False)
    _assert(prep.skip_origin is True)


def _gate_p18_p_04_a_1() -> None:
    prep = prepare_production_e2e(
        _script_dir(),
        environ={ORIGIN_PIPELINE_ENV: "0", "DATA_PC_SKIP_ORIGIN": "0"},
    )
    _assert(prep.origin_pipeline is False)


def _gate_p18_l_01_a_1() -> None:
    root = Path(__file__).resolve().parents[2]
    out = run_live_production_e2e(artifact_dir=root, dry_prep=True)
    _assert(out["status"] == "ok")
    _assert(out["mode"] == "dry_prep")


def _gate_p18_l_02_a_1() -> None:
    root = Path(__file__).resolve().parents[2]
    _assert((root / ARTIFACT_NAME).is_file())


def _gate_p18_l_03_a_1() -> None:
    apply_production_e2e_env()
    _assert(e2e_live_enabled({E2E_LIVE_ENV: "0"}) is False)
    _assert(e2e_live_enabled({E2E_LIVE_ENV: "1"}) is True)


def _gate_p18_l_04_a_1() -> None:
    with patch("data_pc_origin.live_production_e2e.e2e_live_enabled", return_value=True):
        with patch(
            "data_pc_origin.live_production_e2e.run_production_imap_once",
            return_value={"status": "ok", "workflow_ok": True, "row_count": 1},
        ):
            out = run_live_production_e2e(live=True)
    _assert(out["mode"] == "live")
    imap = out.get("imap") if isinstance(out.get("imap"), dict) else {}
    _assert(imap.get("workflow_ok") is True)


_P18_GATES: list[tuple[str, object]] = [
    ("P18-P-01-a-1", _gate_p18_p_01_a_1),
    ("P18-P-02-a-1", _gate_p18_p_02_a_1),
    ("P18-P-03-a-1", _gate_p18_p_03_a_1),
    ("P18-P-04-a-1", _gate_p18_p_04_a_1),
    ("P18-L-01-a-1", _gate_p18_l_01_a_1),
    ("P18-L-02-a-1", _gate_p18_l_02_a_1),
    ("P18-L-03-a-1", _gate_p18_l_03_a_1),
    ("P18-L-04-a-1", _gate_p18_l_04_a_1),
]


def register_p18_gates() -> None:
    for gate_id, fn in _P18_GATES:
        register_gate(gate_id, fn, depends=P18_DEPS[gate_id], layer="P18")  # type: ignore[arg-type]
