# -*- coding: utf-8
"""P15 L4 gate bodies — Supervisor ↔ resolve_job_pipeline."""

from __future__ import annotations

import os
import tempfile
from pathlib import Path
from unittest.mock import patch

from data_pc_origin.gates.registry import P15_DEPS, register_gate
from data_pc_origin.live_supervisor import ARTIFACT_NAME, build_dry_supervisor_tick, run_live_supervisor
from data_pc_origin.p14_runtime_bridge import ORIGIN_PIPELINE_ENV, origin_pipeline_enabled, resolve_job_pipeline


def _assert(condition: bool, msg: str = "") -> None:
    if not condition:
        raise AssertionError(msg or "assertion failed")


def _script_dir() -> str:
    return str(Path(__file__).resolve().parents[2].parent)


def _gate_p15_s_01_a_1() -> None:
    from data_pc_runtime.layer1_state import RuntimePaths, StateStore
    from data_pc_runtime.layer2_gates import GateConfig
    from data_pc_runtime.layer4_supervisor import Supervisor, SupervisorConfig

    script_dir = _script_dir()
    with tempfile.TemporaryDirectory() as tmp:
        os.makedirs(os.path.join(tmp, "KCH"), exist_ok=True)
        with patch(
            "data_pc_origin.p14_runtime_bridge.resolve_job_pipeline",
            return_value=lambda: type(
                "R",
                (),
                {"workflow_count": 0, "gdrive_retry_needed": False},
            )(),
        ) as mocked:
            sup = Supervisor(
                tmp,
                sup_cfg=SupervisorConfig(boot_mail_check=False),
                gate=GateConfig(skip_wifi_check=True, cooldown_sec=0),
            )
            _assert(mocked.called)
            _assert(sup.job is not None)


def _gate_p15_s_02_a_1() -> None:
    tick, _ = build_dry_supervisor_tick(
        _script_dir(),
        origin_pipeline=True,
        dry_run_pipeline=True,
    )
    _assert(tick["status_code"] == "pipeline_done")


def _gate_p15_s_03_a_1() -> None:
    cb = resolve_job_pipeline(
        _script_dir(),
        dry_run=True,
        environ={ORIGIN_PIPELINE_ENV: "1"},
    )
    _assert(callable(cb))


def _gate_p15_s_04_a_1() -> None:
    _assert(origin_pipeline_enabled({ORIGIN_PIPELINE_ENV: "1"}))
    _assert(not origin_pipeline_enabled({ORIGIN_PIPELINE_ENV: "0"}))


def _gate_p15_h_01_a_1() -> None:
    root = Path(__file__).resolve().parents[2]
    out = run_live_supervisor(artifact_dir=root, dry_tick=True, origin_pipeline=True)
    _assert(out["status"] == "ok")
    _assert(out["mode"] == "dry_tick")


def _gate_p15_h_02_a_1() -> None:
    root = Path(__file__).resolve().parents[2]
    _assert((root / ARTIFACT_NAME).is_file())


def _gate_p15_h_03_a_1() -> None:
    from data_pc_runtime.layer1_state import RuntimePaths, StateStore
    from data_pc_runtime.layer2_gates import GateConfig
    from data_pc_runtime.layer3_job import JobRunner
    from data_pc_runtime.layer4_supervisor import Supervisor, SupervisorConfig

    calls = {"n": 0}

    def _noop():
        calls["n"] += 1
        return type("R", (), {"workflow_count": 0, "gdrive_retry_needed": False})()

    with tempfile.TemporaryDirectory() as tmp:
        paths = RuntimePaths(tmp, storage_subdir="KCH")
        os.makedirs(paths.storage_dir, exist_ok=True)
        gate = GateConfig(skip_wifi_check=True, cooldown_sec=0)
        job = JobRunner(paths, _noop, store=StateStore(paths))
        sup = Supervisor(
            tmp,
            job=job,
            sup_cfg=SupervisorConfig(boot_mail_check=False),
            gate=gate,
        )
        sup.run_once_tick()
    _assert(calls["n"] == 1)


def _gate_p15_h_04_a_1() -> None:
    tick, _ = build_dry_supervisor_tick(
        _script_dir(),
        origin_pipeline=True,
        dry_run_pipeline=True,
    )
    _assert("workflows=0" in str(tick.get("gate_detail", "")))


_P15_GATES: list[tuple[str, object]] = [
    ("P15-S-01-a-1", _gate_p15_s_01_a_1),
    ("P15-S-02-a-1", _gate_p15_s_02_a_1),
    ("P15-S-03-a-1", _gate_p15_s_03_a_1),
    ("P15-S-04-a-1", _gate_p15_s_04_a_1),
    ("P15-H-01-a-1", _gate_p15_h_01_a_1),
    ("P15-H-02-a-1", _gate_p15_h_02_a_1),
    ("P15-H-03-a-1", _gate_p15_h_03_a_1),
    ("P15-H-04-a-1", _gate_p15_h_04_a_1),
]


def register_p15_gates() -> None:
    for gate_id, fn in _P15_GATES:
        register_gate(gate_id, fn, depends=P15_DEPS[gate_id], layer="P15")  # type: ignore[arg-type]
