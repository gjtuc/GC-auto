# -*- coding: utf-8
"""P12-F L4 gate bodies — FULL_ARCHIVE native stage2+3 live harness."""

from __future__ import annotations

from pathlib import Path

from data_pc_origin.gates.registry import P12_DEPS, register_gate
from data_pc_origin.live_full_native import (
    ARTIFACT_NAME,
    prepare_live_full_native,
    run_live_full_native,
)
from data_pc_origin.p6_catalyst_adapter import make_stage3_runner
from data_pc_origin.p5_workflow import Stage2RunResult
from data_pc_origin.p0_types import Stage2Artifacts
from data_pc_origin.p1_payload import assemble_stage2_metadata


def _assert(condition: bool, msg: str = "") -> None:
    if not condition:
        raise AssertionError(msg or "assertion failed")


def _gate_p12_f_01_a_1() -> None:
    prep = prepare_live_full_native("")
    _assert(isinstance(prep.ready, bool))
    _assert("kch_path" in prep.to_dict())


def _gate_p12_f_02_a_1() -> None:
    root = Path(__file__).resolve().parents[2]
    out = run_live_full_native("", artifact_dir=root)
    _assert(out["status"] in ("skipped", "ok", "error", "dry_run"))
    _assert(out["mode"] == "full_archive")
    _assert(out.get("data_source") == "kch_raw")
    _assert(out.get("native_stage3") is True)


def _gate_p12_f_03_a_1() -> None:
    artifact = Path(__file__).resolve().parents[2] / ARTIFACT_NAME
    _assert(artifact.is_file())


def _gate_p12_f_04_a_1() -> None:
    import data_pc_origin.tests.fixtures.catalyst_mock_module as mock

    sample_name, *_ = mock.generate_sample_name(r"G:\in.xlsx")
    s3 = make_stage3_runner(mock)
    s2 = Stage2RunResult(
        artifacts=Stage2Artifacts(mock.process_excel(r"G:\in.xlsx")[0], r"G:\mock\calc.xlsx"),
        metadata=assemble_stage2_metadata(
            sample_name=sample_name,
            identity_key=mock._experiment_identity_key(r"G:\in.xlsx"),
            saved_excel=r"G:\mock\calc.xlsx",
        ),
    )
    res = s3(r"G:\in.xlsx", s2)
    _assert(res is not None)
    _assert(str(res.target_opju).endswith(".opju"))


_P12_GATES: list[tuple[str, object]] = [
    ("P12-F-01-a-1", _gate_p12_f_01_a_1),
    ("P12-F-02-a-1", _gate_p12_f_02_a_1),
    ("P12-F-03-a-1", _gate_p12_f_03_a_1),
    ("P12-F-04-a-1", _gate_p12_f_04_a_1),
]


def register_p12_gates() -> None:
    for gate_id, fn in _P12_GATES:
        register_gate(gate_id, fn, depends=P12_DEPS[gate_id], layer="P12")  # type: ignore[arg-type]
