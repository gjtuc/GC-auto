# -*- coding: utf-8
"""P0 L4 gate bodies."""

from __future__ import annotations

from data_pc_origin.gates.registry import P0_DEPS, register_gate
from data_pc_origin.p0_routing import resolve_workflow_mode, should_run_stage4
from data_pc_origin.p0_types import (
    OriginJobPayload,
    Stage2Artifacts,
    WorkflowMode,
    WorkflowOptions,
    build_origin_payload,
    payload_row_count,
)


def _assert(condition: bool, msg: str = "") -> None:
    if not condition:
        raise AssertionError(msg or "assertion failed")


class _FakeDf:
    def __init__(self, n: int) -> None:
        self._n = n

    def __len__(self) -> int:
        return self._n


def _gate_p0_t_01_a_1() -> None:
    _assert(len(WorkflowMode) == 3)
    _assert(WorkflowMode.OPJU_ONLY.value == "opju_only")


def _gate_p0_t_02_a_1() -> None:
    o = WorkflowOptions(opju_path=r"G:\x.opju", skip_stage4=True)
    _assert(o.opju_path.endswith(".opju"))
    _assert(o.skip_stage4 is True)


def _gate_p0_t_03_a_1() -> None:
    art = Stage2Artifacts(_FakeDf(3), r"G:\out.xlsx", ("w",), "feed")
    _assert(len(art.df) == 3)
    _assert(art.warnings[0] == "w")


def _gate_p0_t_04_a_1() -> None:
    p = OriginJobPayload("p.opju", "s", ("20260101", "k"), True, _FakeDf(1))
    _assert(p.sample_name == "s")
    _assert(p.save_in_place is True)


def _gate_p0_t_05_a_1() -> None:
    art = Stage2Artifacts(_FakeDf(2), "x.xlsx")
    p = build_origin_payload(
        art,
        opju_path=r"G:\a.opju",
        sample_name="n",
        identity_key=("d", "k"),
        mode=WorkflowMode.OPJU_ONLY,
    )
    _assert(p.save_in_place is False)
    p2 = build_origin_payload(
        art,
        opju_path=r"G:\a.opju",
        sample_name="n",
        identity_key=("d", "k"),
        mode=WorkflowMode.FULL_ARCHIVE,
    )
    _assert(p2.save_in_place is True)


def _gate_p0_t_06_a_1() -> None:
    art = Stage2Artifacts(_FakeDf(108), "x.xlsx")
    p = build_origin_payload(
        art,
        opju_path="p",
        sample_name="n",
        identity_key=("d", "k"),
        mode=WorkflowMode.FULL_ARCHIVE,
    )
    _assert(payload_row_count(p) == 108)


def _gate_p0_r_01_a_1() -> None:
    m = resolve_workflow_mode(WorkflowOptions(opju_path=r"G:\x.opju"))
    _assert(m == WorkflowMode.OPJU_ONLY)


def _gate_p0_r_02_a_1() -> None:
    m = resolve_workflow_mode(WorkflowOptions(auto_archive=False))
    _assert(m == WorkflowMode.CALC_ONLY)


def _gate_p0_r_03_a_1() -> None:
    m = resolve_workflow_mode(WorkflowOptions())
    _assert(m == WorkflowMode.FULL_ARCHIVE)


def _gate_p0_r_04_a_1() -> None:
    _assert(should_run_stage4(WorkflowOptions()) is True)
    _assert(should_run_stage4(WorkflowOptions(skip_stage4=True)) is False)


_P0_GATES: list[tuple[str, object]] = [
    ("P0-T-01-a-1", _gate_p0_t_01_a_1),
    ("P0-T-02-a-1", _gate_p0_t_02_a_1),
    ("P0-T-03-a-1", _gate_p0_t_03_a_1),
    ("P0-T-04-a-1", _gate_p0_t_04_a_1),
    ("P0-T-05-a-1", _gate_p0_t_05_a_1),
    ("P0-T-06-a-1", _gate_p0_t_06_a_1),
    ("P0-R-01-a-1", _gate_p0_r_01_a_1),
    ("P0-R-02-a-1", _gate_p0_r_02_a_1),
    ("P0-R-03-a-1", _gate_p0_r_03_a_1),
    ("P0-R-04-a-1", _gate_p0_r_04_a_1),
]


def register_p0_gates() -> None:
    for gate_id, fn in _P0_GATES:
        register_gate(gate_id, fn, depends=P0_DEPS[gate_id], layer="P0")  # type: ignore[arg-type]
