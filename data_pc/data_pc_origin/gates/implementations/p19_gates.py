# -*- coding: utf-8
"""P19 L4 gate bodies — live artifact validation."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

from data_pc_origin.gates.registry import P19_DEPS, register_gate
from data_pc_origin.live_production_run import ARTIFACT_NAME, run_production_live_validated, run_validate_fixture
from data_pc_origin.p19_live_assert import (
    assert_no_secrets,
    fixture_ok_imap_payload,
    validate_imap_live_payload,
    validate_production_run_result,
)


def _assert(condition: bool, msg: str = "") -> None:
    if not condition:
        raise AssertionError(msg or "assertion failed")


def _gate_p19_v_01_a_1() -> None:
    v = validate_imap_live_payload(fixture_ok_imap_payload())
    _assert(v.ok is True)


def _gate_p19_v_02_a_1() -> None:
    bad = {"status": "ok", "workflow_ok": False, "row_count": 10}
    v = validate_imap_live_payload(bad)
    _assert(v.ok is False)


def _gate_p19_v_03_a_1() -> None:
    v = validate_imap_live_payload({"status": "skipped", "reason": "no pending gc mail"})
    _assert(v.ok is True)


def _gate_p19_v_04_a_1() -> None:
    _assert(assert_no_secrets('{"email":"ok"}'))
    _assert(not assert_no_secrets('password=secret123'))


def _gate_p19_r_01_a_1() -> None:
    root = Path(__file__).resolve().parents[2]
    out = run_validate_fixture(artifact_dir=root)
    _assert(out["status"] == "ok")
    _assert(out["mode"] == "validate_fixture")


def _gate_p19_r_02_a_1() -> None:
    root = Path(__file__).resolve().parents[2]
    _assert((root / ARTIFACT_NAME).is_file())


def _gate_p19_r_03_a_1() -> None:
    with patch(
        "data_pc_origin.p18_production_e2e.run_production_imap_once",
        return_value=fixture_ok_imap_payload(),
    ):
        out = run_production_live_validated(force_live=True)
    _assert(out["mode"] == "live")
    val = out.get("validation")
    _assert(isinstance(val, dict) and val.get("ok") is True)


def _gate_p19_r_04_a_1() -> None:
    out = {
        "status": "ok",
        "mode": "live",
        "imap": fixture_ok_imap_payload(),
        "validation": validate_imap_live_payload(fixture_ok_imap_payload()).to_dict(),
    }
    v = validate_production_run_result(out)
    _assert(v.ok is True)


_P19_GATES: list[tuple[str, object]] = [
    ("P19-V-01-a-1", _gate_p19_v_01_a_1),
    ("P19-V-02-a-1", _gate_p19_v_02_a_1),
    ("P19-V-03-a-1", _gate_p19_v_03_a_1),
    ("P19-V-04-a-1", _gate_p19_v_04_a_1),
    ("P19-R-01-a-1", _gate_p19_r_01_a_1),
    ("P19-R-02-a-1", _gate_p19_r_02_a_1),
    ("P19-R-03-a-1", _gate_p19_r_03_a_1),
    ("P19-R-04-a-1", _gate_p19_r_04_a_1),
]


def register_p19_gates() -> None:
    for gate_id, fn in _P19_GATES:
        register_gate(gate_id, fn, depends=P19_DEPS[gate_id], layer="P19")  # type: ignore[arg-type]
