# -*- coding: utf-8 -*-
"""O4 L4 gate bodies — mock originpro."""

from __future__ import annotations

import unittest
from types import ModuleType, SimpleNamespace

from data_pc_origin.gates.registry import O4_DEPS, register_gate
from data_pc_origin.o4_errors import OriginOpenError
from data_pc_origin.o4_project import (
    open_project,
    open_project_with_retry,
    save_project,
    save_project_as,
    try_open_project,
    validate_opju_path,
)


def _assert(condition: bool, msg: str = "") -> None:
    if not condition:
        raise AssertionError(msg or "assertion failed")


def _fake_op(*, open_ok: bool = True, open_calls: list | None = None) -> ModuleType:
    calls = open_calls if open_calls is not None else []

    class FakeOp(SimpleNamespace):
        def set_show(self, value: bool) -> None:
            pass

        def oext(self, value: bool) -> None:
            pass

        def open(self, path: str) -> bool:
            calls.append(path)
            return open_ok

        def save(self, path: str) -> None:
            calls.append(f"save:{path}")

        def exit(self) -> None:
            pass

    op = FakeOp()
    op._open_calls = calls  # type: ignore[attr-defined]
    return op  # type: ignore[return-value]


def _gate_o4_v_01_a_1() -> None:
    r = validate_opju_path("")
    _assert(not r.ok)
    _assert(r.code == "P01")


def _gate_o4_o_01_a_1() -> None:
    op = _fake_op()
    path = r"G:\mock\sample.opju"
    try_open_project(op, path)
    _assert(op._open_calls == [path])  # type: ignore[attr-defined]


def _gate_o4_o_01_b_1() -> None:
    op = _fake_op(open_ok=True)
    _assert(try_open_project(op, r"G:\x.opju") is True)


def _gate_o4_o_01_c_1() -> None:
    op = _fake_op(open_ok=False)
    try:
        open_project(op, r"G:\bad.opju")
        raise AssertionError("expected OriginOpenError")
    except OriginOpenError:
        pass


def _gate_o4_o_02_a_1() -> None:
    n = {"i": 0}
    op = _fake_op(open_ok=False)

    def flaky(path: str) -> bool:
        n["i"] += 1
        return n["i"] >= 2

    op.open = flaky  # type: ignore[method-assign]
    open_project_with_retry(op, r"G:\retry.opju", max_retries=1)
    _assert(n["i"] == 2)


def _gate_o4_s_01_a_1() -> None:
    op = _fake_op()
    path = r"G:\mock\sample.opju"
    save_project(op, path)
    _assert("save:" + path in op._open_calls)  # type: ignore[attr-defined]


def _gate_o4_s_02_a_1() -> None:
    op = _fake_op()
    new_path = r"G:\mock\sample_Updated.opju"
    save_project_as(op, new_path)
    _assert(f"save:{new_path}" in op._open_calls)  # type: ignore[attr-defined]


def _gate_o4_r_01_a_1() -> None:
    path = r"G:\mock\roundtrip.opju"
    events: list[str] = []

    class FakeOp(SimpleNamespace):
        def open(self, p: str) -> bool:
            events.append(f"open:{p}")
            return True

        def save(self, p: str) -> None:
            events.append(f"save:{p}")

        def exit(self) -> None:
            events.append("exit")

    op = FakeOp()
    open_project(op, path)  # type: ignore[arg-type]
    save_project(op, path)  # type: ignore[arg-type]
    op.exit()
    _assert(events == [f"open:{path}", f"save:{path}", "exit"])


_O4_GATES = [
    ("O4-V-01-a-1", _gate_o4_v_01_a_1),
    ("O4-O-01-a-1", _gate_o4_o_01_a_1),
    ("O4-O-01-b-1", _gate_o4_o_01_b_1),
    ("O4-O-01-c-1", _gate_o4_o_01_c_1),
    ("O4-O-02-a-1", _gate_o4_o_02_a_1),
    ("O4-S-01-a-1", _gate_o4_s_01_a_1),
    ("O4-S-02-a-1", _gate_o4_s_02_a_1),
    ("O4-R-01-a-1", _gate_o4_r_01_a_1),
]


def register_o4_gates() -> None:
    for gate_id, fn in _O4_GATES:
        register_gate(gate_id, fn, depends=O4_DEPS[gate_id], layer="O4")
