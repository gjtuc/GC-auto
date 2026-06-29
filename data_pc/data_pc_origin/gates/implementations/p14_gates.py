# -*- coding: utf-8
"""P14 L4 gate bodies — runtime bridge."""

from __future__ import annotations

from pathlib import Path

from data_pc_origin.gates.registry import P14_DEPS, register_gate
from data_pc_origin.live_runtime import ARTIFACT_NAME, run_live_runtime
from data_pc_origin.p14_runtime_bridge import (
    RuntimePipelineResult,
    make_runtime_job_callback,
    origin_pipeline_enabled,
    parse_imap_workflow_result,
    resolve_job_pipeline,
)


def _assert(condition: bool, msg: str = "") -> None:
    if not condition:
        raise AssertionError(msg or "assertion failed")


def _gate_p14_r_01_a_1() -> None:
    r = RuntimePipelineResult(2, True)
    _assert(r.workflow_count == 2 and r.gdrive_retry_needed is True)


def _gate_p14_r_02_a_1() -> None:
    parsed = parse_imap_workflow_result(
        {"status": "ok", "workflow_ok": True, "row_count": 108}
    )
    _assert(parsed.workflow_count == 1)


def _gate_p14_r_03_a_1() -> None:
    parsed = parse_imap_workflow_result(
        {
            "status": "skipped",
            "reason": "G: drive not available",
        }
    )
    _assert(parsed.gdrive_retry_needed is True)


def _gate_p14_r_04_a_1() -> None:
    parsed = parse_imap_workflow_result({"status": "skipped", "reason": "no pending"})
    _assert(parsed.workflow_count == 0 and not parsed.gdrive_retry_needed)


def _gate_p14_j_01_a_1() -> None:
    cb = make_runtime_job_callback(dry_run=True)
    _assert(callable(cb))


def _gate_p14_j_02_a_1() -> None:
    root = Path(__file__).resolve().parents[2]
    out = run_live_runtime(artifact_dir=root, dry_run=True)
    _assert(out["status"] in ("skipped", "ok", "error", "dry_run"))


def _gate_p14_j_03_a_1() -> None:
    root = Path(__file__).resolve().parents[2]
    out = run_live_runtime(artifact_dir=root, dry_job=True)
    path = root / ARTIFACT_NAME
    _assert(path.is_file())
    _assert(out.get("mode") == "dry_job")
    _assert(out.get("job_ran") is True)
    _assert(out.get("job_status_code") == "pipeline_done")


def _gate_p14_j_04_a_1() -> None:
    from data_pc_runtime.layer3_job import _parse_pipeline_result

    r = RuntimePipelineResult(1, False)
    wc, gd = _parse_pipeline_result(r)
    _assert(wc == 1 and gd is False)
    script_dir = str(Path(__file__).resolve().parents[2].parent)
    cb = resolve_job_pipeline(
        script_dir,
        environ={"DATA_PC_ORIGIN_PIPELINE": "0"},
    )
    _assert(callable(cb))


_P14_GATES: list[tuple[str, object]] = [
    ("P14-R-01-a-1", _gate_p14_r_01_a_1),
    ("P14-R-02-a-1", _gate_p14_r_02_a_1),
    ("P14-R-03-a-1", _gate_p14_r_03_a_1),
    ("P14-R-04-a-1", _gate_p14_r_04_a_1),
    ("P14-J-01-a-1", _gate_p14_j_01_a_1),
    ("P14-J-02-a-1", _gate_p14_j_02_a_1),
    ("P14-J-03-a-1", _gate_p14_j_03_a_1),
    ("P14-J-04-a-1", _gate_p14_j_04_a_1),
]


def register_p14_gates() -> None:
    for gate_id, fn in _P14_GATES:
        register_gate(gate_id, fn, depends=P14_DEPS[gate_id], layer="P14")  # type: ignore[arg-type]
