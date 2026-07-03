# -*- coding: utf-8
"""P4 L4 gate bodies — mock origin only."""

from __future__ import annotations

from data_pc_origin.gates.registry import P4_DEPS, register_gate
from data_pc_origin.o2_env import SKIP_ORIGIN_ENV
from data_pc_origin.o8_fixtures import OPJU_FX, SAMPLE_JOB, fx_job_df_full, fx_job_op_full
from data_pc_origin.o9_facade import OriginUpdateResult, update_from_dataframe
from data_pc_origin.p0_types import OriginJobPayload, WorkflowOptions
from data_pc_origin.p4_origin_stage import (
    Stage4Result,
    bridge_kwargs_from_payload,
    maybe_run_stage4,
    run_stage4_origin,
)


def _assert(condition: bool, msg: str = "") -> None:
    if not condition:
        raise AssertionError(msg or "assertion failed")


def _fx_payload(*, save_in_place: bool = False) -> OriginJobPayload:
    return OriginJobPayload(
        opju_path=OPJU_FX,
        sample_name=SAMPLE_JOB,
        identity_key=("20250601", "seed"),
        save_in_place=save_in_place,
        df=fx_job_df_full(),
    )


def _mock_runner(payload: OriginJobPayload) -> OriginUpdateResult:
    op, _ = fx_job_op_full()
    return update_from_dataframe(
        payload.opju_path,
        payload.df,
        payload.sample_name,
        save_in_place=payload.save_in_place,
        identity_key=payload.identity_key,
        op=op,
        skip_gate=True,
        printer=lambda _m: None,
        log_fn=lambda _m: None,
    )


def _gate_p4_o_01_a_1() -> None:
    res = run_stage4_origin(_fx_payload(), runner=_mock_runner)
    _assert(isinstance(res, Stage4Result))
    _assert(res.skipped is False)
    _assert(res.origin is not None)
    _assert(res.origin.sheets_updated == 8)


def _gate_p4_o_02_a_1() -> None:
    payload = _fx_payload(save_in_place=True)
    kw = bridge_kwargs_from_payload(payload)
    _assert(kw["opju_path"] == OPJU_FX)
    _assert(kw["sample_name"] == SAMPLE_JOB)
    _assert(kw["save_in_place"] is True)
    _assert(kw["identity_key"] == ("20250601", "seed"))


def _gate_p4_m_01_a_1() -> None:
    seen: list[OriginJobPayload] = []

    def track(payload: OriginJobPayload) -> OriginUpdateResult:
        seen.append(payload)
        return _mock_runner(payload)

    run_stage4_origin(_fx_payload(), runner=track)
    _assert(len(seen) == 1)
    _assert(seen[0].opju_path == OPJU_FX)


def _gate_p4_m_02_a_1() -> None:
    calls = 0

    def track(_payload: OriginJobPayload) -> OriginUpdateResult:
        nonlocal calls
        calls += 1
        return _mock_runner(_payload)

    res = maybe_run_stage4(
        _fx_payload(),
        explicit=True,
        runner=track,
    )
    _assert(res.skipped is True)
    _assert(calls == 0)


def _gate_p4_r_01_a_1() -> None:
    res = maybe_run_stage4(
        _fx_payload(),
        options=WorkflowOptions(skip_stage4=True),
    )
    _assert(res.skipped is True)
    _assert(res.ok is True)
    _assert(res.origin is None)
    _assert("Origin" in res.skip_reason)


def _gate_p4_r_02_a_1() -> None:
    def fail(_payload: OriginJobPayload) -> OriginUpdateResult:
        return OriginUpdateResult(
            ok=False,
            sheets_updated=0,
            row_count=0,
            warnings=(),
            opju_path=OPJU_FX,
            sample_name=SAMPLE_JOB,
        )

    res = run_stage4_origin(_fx_payload(), runner=fail)
    _assert(res.skipped is False)
    _assert(res.ok is False)
    _assert(res.origin is not None and res.origin.ok is False)


_P4_GATES: list[tuple[str, object]] = [
    ("P4-O-01-a-1", _gate_p4_o_01_a_1),
    ("P4-O-02-a-1", _gate_p4_o_02_a_1),
    ("P4-M-01-a-1", _gate_p4_m_01_a_1),
    ("P4-M-02-a-1", _gate_p4_m_02_a_1),
    ("P4-R-01-a-1", _gate_p4_r_01_a_1),
    ("P4-R-02-a-1", _gate_p4_r_02_a_1),
]


def register_p4_gates() -> None:
    for gate_id, fn in _P4_GATES:
        register_gate(gate_id, fn, depends=P4_DEPS[gate_id], layer="P4")  # type: ignore[arg-type]
