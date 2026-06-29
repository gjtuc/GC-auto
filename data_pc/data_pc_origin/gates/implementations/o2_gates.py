# -*- coding: utf-8 -*-
"""O2 L4 gate bodies."""

from __future__ import annotations

import os
import tempfile
from dataclasses import FrozenInstanceError
from pathlib import Path

from data_pc_origin.gates.registry import O2_DEPS, register_gate
from data_pc_origin.o0_types import ProbeResult
from data_pc_origin.o2_env import (
    SKIP_ORIGIN_ENV,
    origin_feature_enabled,
    parse_bool_env,
    read_env_raw,
    skip_origin_active,
)
from data_pc_origin.o2_gate_chain import GateVerdict, evaluate_origin_gate
from data_pc_origin.o2_origin_lock import OriginLock
from data_pc_origin.o2_paths import origin_lock_path
from data_pc_origin.o2_pipeline_lock import pid_alive, pipeline_busy, read_pipeline_lock


def _assert(condition: bool, msg: str = "") -> None:
    if not condition:
        raise AssertionError(msg or "assertion failed")


def _gate_o2_e_01_a_1() -> None:
    _assert(read_env_raw("UNSET_KEY_XYZ", environ={}) == "")


def _gate_o2_e_01_b_1() -> None:
    _assert(read_env_raw("K", environ={"K": "  TRUE  "}) == "true")


def _gate_o2_e_02_a_1() -> None:
    for v in ("1", "true", "yes", "on"):
        _assert(parse_bool_env(v))


def _gate_o2_e_02_b_1() -> None:
    _assert(not parse_bool_env("0"))
    _assert(not parse_bool_env("off"))


def _gate_o2_e_03_a_1() -> None:
    _assert(skip_origin_active(environ={SKIP_ORIGIN_ENV: "1"}))


def _gate_o2_e_04_a_1() -> None:
    _assert(not origin_feature_enabled(environ={SKIP_ORIGIN_ENV: "1"}))
    _assert(origin_feature_enabled(environ={SKIP_ORIGIN_ENV: "0"}))


def _gate_o2_l_01_a_1() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        lock = os.path.join(tmp, ".data_pc_pipeline.lock")
        Path(lock).write_text("12345", encoding="ascii")
        _assert(read_pipeline_lock(lock).exists)


def _gate_o2_l_01_b_1() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        lock = os.path.join(tmp, "lock")
        Path(lock).write_text(str(os.getpid()), encoding="ascii")
        _assert(read_pipeline_lock(lock).pid == os.getpid())


def _gate_o2_l_01_c_1() -> None:
    _assert(pid_alive(os.getpid()))
    _assert(not pid_alive(999_999_999))


def _gate_o2_l_02_a_1() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        lock = os.path.join(tmp, "lock")
        Path(lock).write_text(str(os.getpid()), encoding="ascii")
        _assert(pipeline_busy(lock))


def _gate_o2_l_03_a_1() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        base = Path(tmp)
        path = origin_lock_path(base)
        _assert(path.endswith(".origin_update.lock"))


def _gate_o2_l_04_a_1() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        lock = os.path.join(tmp, "origin.lock")
        ol = OriginLock(lock)
        _assert(ol.try_acquire())
        ol.release()
        _assert(not os.path.isfile(lock))


def _gate_o2_l_04_b_1() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        lock = os.path.join(tmp, "origin.lock")
        Path(lock).write_text("999999999", encoding="ascii")
        ol = OriginLock(lock)
        _assert(ol.try_acquire())
        ol.release()


def _gate_o2_l_04_c_1() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        lock = os.path.join(tmp, "origin.lock")
        Path(lock).write_text(str(os.getpid()), encoding="ascii")
        ol = OriginLock(lock, timeout_sec=0.0)
        _assert(not ol.try_acquire())


def _gate_o2_l_05_a_1() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        lock = os.path.join(tmp, "origin.lock")
        with OriginLock(lock):
            _assert(os.path.isfile(lock))
        _assert(not os.path.isfile(lock))


def _gate_o2_g_01_a_1() -> None:
    v = evaluate_origin_gate(
        opju_probe=ProbeResult(True, "ok"),
        pipeline_lock_path="/none",
        origin_lock_path="/none2",
        skip_origin=True,
        acquire_origin_lock=False,
    )
    _assert(v.code == "skip_origin")


def _gate_o2_g_02_a_1() -> None:
    v = evaluate_origin_gate(
        opju_probe=ProbeResult(False, "bad path", "P01"),
        pipeline_lock_path="/none",
        origin_lock_path="/none2",
        skip_origin=False,
        acquire_origin_lock=False,
    )
    _assert(v.code == "wait")
    _assert(v.reason == "probe_fail")


def _gate_o2_g_03_a_1() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        lock = os.path.join(tmp, "pipe.lock")
        Path(lock).write_text(str(os.getpid()), encoding="ascii")
        v = evaluate_origin_gate(
            opju_probe=ProbeResult(True, "ok"),
            pipeline_lock_path=lock,
            origin_lock_path=os.path.join(tmp, "o.lock"),
            skip_origin=False,
            acquire_origin_lock=False,
        )
        _assert(v.code == "wait")
        _assert(v.reason == "pipeline_busy")


def _gate_o2_g_04_a_1() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        olock = os.path.join(tmp, "origin.lock")
        Path(olock).write_text(str(os.getpid()), encoding="ascii")
        v = evaluate_origin_gate(
            opju_probe=ProbeResult(True, "ok"),
            pipeline_lock_path=os.path.join(tmp, "free.pipe"),
            origin_lock_path=olock,
            skip_origin=False,
            acquire_origin_lock=True,
        )
        _assert(v.code == "wait")
        _assert(v.reason == "origin_lock")


def _gate_o2_g_05_a_1() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        v = evaluate_origin_gate(
            opju_probe=ProbeResult(True, "ok"),
            pipeline_lock_path=os.path.join(tmp, "free.pipe"),
            origin_lock_path=os.path.join(tmp, "free.origin.lock"),
            skip_origin=False,
            acquire_origin_lock=True,
        )
        _assert(v.code == "ready")


def _gate_o2_g_06_a_1() -> None:
    v = GateVerdict(code="ready", detail="ok")
    try:
        v.code = "wait"  # type: ignore[misc]
        raise AssertionError("not frozen")
    except FrozenInstanceError:
        pass


_O2_GATES = [
    ("O2-E-01-a-1", _gate_o2_e_01_a_1),
    ("O2-E-01-b-1", _gate_o2_e_01_b_1),
    ("O2-E-02-a-1", _gate_o2_e_02_a_1),
    ("O2-E-02-b-1", _gate_o2_e_02_b_1),
    ("O2-E-03-a-1", _gate_o2_e_03_a_1),
    ("O2-E-04-a-1", _gate_o2_e_04_a_1),
    ("O2-L-01-a-1", _gate_o2_l_01_a_1),
    ("O2-L-01-b-1", _gate_o2_l_01_b_1),
    ("O2-L-01-c-1", _gate_o2_l_01_c_1),
    ("O2-L-02-a-1", _gate_o2_l_02_a_1),
    ("O2-L-03-a-1", _gate_o2_l_03_a_1),
    ("O2-L-04-a-1", _gate_o2_l_04_a_1),
    ("O2-L-04-b-1", _gate_o2_l_04_b_1),
    ("O2-L-04-c-1", _gate_o2_l_04_c_1),
    ("O2-L-05-a-1", _gate_o2_l_05_a_1),
    ("O2-G-01-a-1", _gate_o2_g_01_a_1),
    ("O2-G-02-a-1", _gate_o2_g_02_a_1),
    ("O2-G-03-a-1", _gate_o2_g_03_a_1),
    ("O2-G-04-a-1", _gate_o2_g_04_a_1),
    ("O2-G-05-a-1", _gate_o2_g_05_a_1),
    ("O2-G-06-a-1", _gate_o2_g_06_a_1),
]


def register_o2_gates() -> None:
    for gate_id, fn in _O2_GATES:
        register_gate(gate_id, fn, depends=O2_DEPS[gate_id], layer="O2")
