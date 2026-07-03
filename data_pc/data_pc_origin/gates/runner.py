# -*- coding: utf-8 -*-
"""Gate runner — single gate, rollup, LOCKED."""

from __future__ import annotations

from typing import FrozenSet, Iterable, List, Set, Tuple

from data_pc_origin.gates.registry import (
    GateSpec,
    get_gate,
    is_registered,
    locked_reason,
    rollup_gate_ids,
)


class GateLockedError(Exception):
    def __init__(self, gate_id: str, blocker: str) -> None:
        super().__init__(f"LOCKED {gate_id} (need {blocker})")
        self.gate_id = gate_id
        self.blocker = blocker


class GateAssertError(Exception):
    def __init__(self, gate_id: str, message: str) -> None:
        super().__init__(f"ASSERT {gate_id}: {message}")
        self.gate_id = gate_id
        self.message = message


def run_gate_spec(spec: GateSpec, passed: Set[str]) -> None:
    blocker = locked_reason(spec.gate_id, frozenset(passed))
    if blocker:
        raise GateLockedError(spec.gate_id, blocker)
    try:
        spec.run()
    except AssertionError as exc:
        raise GateAssertError(spec.gate_id, str(exc) or "assertion failed") from exc
    passed.add(spec.gate_id)


def run_gate(gate_id: str, passed: Set[str] | None = None) -> Tuple[int, Set[str]]:
    """
    Returns (exit_code, passed_set).
    exit: 0 OK, 1 ASSERT, 2 LOCKED, 3 unknown gate
    """
    if passed is None:
        passed = set()
    if not is_registered(gate_id):
        return 3, passed
    spec = get_gate(gate_id)
    try:
        run_gate_spec(spec, passed)
        return 0, passed
    except GateLockedError:
        return 2, passed
    except GateAssertError:
        return 1, passed


def run_rollup(rollup_id: str) -> Tuple[int, List[str], Set[str]]:
    """Run rollup in order. Returns (exit_code, log_lines, passed)."""
    passed: Set[str] = set()
    log: List[str] = []
    try:
        gate_ids = rollup_gate_ids(rollup_id)
    except KeyError:
        return 3, [f"unknown rollup: {rollup_id}"], passed

    for gid in gate_ids:
        code, passed = run_gate(gid, passed)
        if code == 0:
            log.append(f"[PASS] {gid}")
        elif code == 2:
            blocker = locked_reason(gid, frozenset(passed)) or "?"
            log.append(f"[LOCKED] {gid} (need {blocker})")
            return 2, log, passed
        else:
            log.append(f"[FAIL] {gid}")
            return 1, log, passed
    log.append(f"[OK] rollup {rollup_id} ({len(gate_ids)} gates)")
    return 0, log, passed


def run_gates_in_order(gate_ids: Iterable[str]) -> Tuple[int, List[str], Set[str]]:
    passed: Set[str] = set()
    log: List[str] = []
    for gid in gate_ids:
        code, passed = run_gate(gid, passed)
        if code == 0:
            log.append(f"[PASS] {gid}")
        elif code == 2:
            blocker = locked_reason(gid, frozenset(passed)) or "?"
            log.append(f"[LOCKED] {gid} (need {blocker})")
            return 2, log, passed
        else:
            log.append(f"[FAIL] {gid}")
            return 1, log, passed
    return 0, log, passed
