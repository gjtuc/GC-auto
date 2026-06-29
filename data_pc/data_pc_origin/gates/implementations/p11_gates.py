# -*- coding: utf-8
"""P11-K L4 gate bodies — KCH native stage2 live harness."""

from __future__ import annotations

from pathlib import Path

from data_pc_origin.gates.registry import P11_DEPS, register_gate
from data_pc_origin.live_common import make_catalyst_stage2_runner
from data_pc_origin.live_kch import (
    ARTIFACT_NAME,
    prepare_live_kch,
    run_live_kch,
)


def _assert(condition: bool, msg: str = "") -> None:
    if not condition:
        raise AssertionError(msg or "assertion failed")


def _gate_p11_k_01_a_1() -> None:
    prep = prepare_live_kch("")
    _assert(isinstance(prep.ready, bool))
    _assert("kch_path" in prep.to_dict())


def _gate_p11_k_02_a_1() -> None:
    root = Path(__file__).resolve().parents[2]
    out = run_live_kch("", artifact_dir=root, stage2_only=True)
    _assert(out["status"] in ("skipped", "ok", "error", "dry_run"))
    _assert(out.get("data_source") == "kch_raw")


def _gate_p11_k_03_a_1() -> None:
    artifact = Path(__file__).resolve().parents[2] / ARTIFACT_NAME
    _assert(artifact.is_file())


def _gate_p11_k_04_a_1() -> None:
    import data_pc_origin.tests.fixtures.catalyst_mock_module as mock

    def _noop(_msg: str) -> None:
        pass

    runner = make_catalyst_stage2_runner(mock, printer=_noop)
    _assert(callable(runner))
    res = runner(r"G:\in.xlsx")
    _assert(res is not None)
    _assert("mock" in res.metadata.sample_name)


_P11_GATES: list[tuple[str, object]] = [
    ("P11-K-01-a-1", _gate_p11_k_01_a_1),
    ("P11-K-02-a-1", _gate_p11_k_02_a_1),
    ("P11-K-03-a-1", _gate_p11_k_03_a_1),
    ("P11-K-04-a-1", _gate_p11_k_04_a_1),
]


def register_p11_gates() -> None:
    for gate_id, fn in _P11_GATES:
        register_gate(gate_id, fn, depends=P11_DEPS[gate_id], layer="P11")  # type: ignore[arg-type]
