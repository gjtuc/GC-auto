# -*- coding: utf-8
"""P3-S L4 gate bodies."""

from __future__ import annotations

from data_pc_origin.gates.registry import P3_DEPS, register_gate
from data_pc_origin.o2_env import SKIP_ORIGIN_ENV
from data_pc_origin.p0_types import WorkflowOptions
from data_pc_origin.p3_skip import (
    STAGE4_SKIP_MSG,
    resolve_skip_stage4,
    should_execute_stage4,
    skip_env_key,
    stage4_skip_reason,
)


def _assert(condition: bool, msg: str = "") -> None:
    if not condition:
        raise AssertionError(msg or "assertion failed")


def _gate_p3_s_01_a_1() -> None:
    env = {SKIP_ORIGIN_ENV: "1"}
    _assert(resolve_skip_stage4(environ=env) is True)


def _gate_p3_s_02_a_1() -> None:
    env = {SKIP_ORIGIN_ENV: "1"}
    _assert(resolve_skip_stage4(explicit=False, environ=env) is False)
    _assert(resolve_skip_stage4(explicit=True, environ={}) is True)


def _gate_p3_s_03_a_1() -> None:
    _assert(should_execute_stage4(explicit=True) is False)
    _assert(should_execute_stage4(explicit=False, environ={}) is True)
    opts = WorkflowOptions(skip_stage4=True)
    _assert(should_execute_stage4(options=opts, explicit=False) is False)


def _gate_p3_s_04_a_1() -> None:
    msg = stage4_skip_reason(explicit=True)
    _assert(STAGE4_SKIP_MSG in msg)
    _assert(stage4_skip_reason(explicit=False, environ={}) == "")
    _assert(skip_env_key() == SKIP_ORIGIN_ENV)


_P3_GATES: list[tuple[str, object]] = [
    ("P3-S-01-a-1", _gate_p3_s_01_a_1),
    ("P3-S-02-a-1", _gate_p3_s_02_a_1),
    ("P3-S-03-a-1", _gate_p3_s_03_a_1),
    ("P3-S-04-a-1", _gate_p3_s_04_a_1),
]


def register_p3_gates() -> None:
    for gate_id, fn in _P3_GATES:
        register_gate(gate_id, fn, depends=P3_DEPS[gate_id], layer="P3")  # type: ignore[arg-type]
