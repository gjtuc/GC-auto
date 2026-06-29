# -*- coding: utf-8
"""P7 L4 gate bodies — mail → workflow mock."""

from __future__ import annotations

from data_pc_origin.gates.registry import P7_DEPS, register_gate
from data_pc_origin.o8_fixtures import OPJU_FX, SAMPLE_JOB, fx_job_df_full, fx_job_op_full
from data_pc_origin.o9_facade import update_from_dataframe
from data_pc_origin.p0_types import Stage2Artifacts, WorkflowOptions
from data_pc_origin.p1_payload import Stage2Metadata, assemble_stage2_metadata
from data_pc_origin.p5_workflow import Stage2RunResult, Stage3Result
from data_pc_origin.p7_mail_hook import (
    MailAttachmentError,
    MailJob,
    parse_mail_attachment,
    run_mail_workflow,
)


def _assert(condition: bool, msg: str = "") -> None:
    if not condition:
        raise AssertionError(msg or "assertion failed")


def _fx_stage2(_path: str) -> Stage2RunResult:
    art = Stage2Artifacts(fx_job_df_full(), r"G:\calc.xlsx")
    meta = assemble_stage2_metadata(
        sample_name=SAMPLE_JOB,
        identity_key=("20250601", "seed"),
        saved_excel=r"G:\calc.xlsx",
    )
    return Stage2RunResult(artifacts=art, metadata=meta)


def _mock_origin(payload):
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


def _gate_p7_m_01_a_1() -> None:
    job = MailJob(attachment_path=r"G:\mail\KCH.xlsx", subject="gc")
    _assert(parse_mail_attachment(job).endswith(".xlsx"))


def _gate_p7_m_02_a_1() -> None:
    job = MailJob(attachment_path=r"G:\mail\KCH.xlsx")
    res = run_mail_workflow(
        job,
        WorkflowOptions(opju_path=OPJU_FX),
        stage2_runner=_fx_stage2,
        origin_runner=_mock_origin,
    )
    _assert(res.ok is True)
    assert res.stage4 is not None and res.stage4.origin is not None
    _assert(res.stage4.origin.sheets_updated == 8)


def _gate_p7_r_01_a_1() -> None:
    job = MailJob(attachment_path=r"G:\mail\KCH.xlsx")
    res = run_mail_workflow(
        job,
        WorkflowOptions(auto_archive=False),
        stage2_runner=_fx_stage2,
    )
    _assert(res.ok is True)
    _assert(res.stage4 is None)


def _gate_p7_r_02_a_1() -> None:
    job = MailJob(attachment_path=r"G:\mail\report.pdf")
    try:
        parse_mail_attachment(job)
        _assert(False, "expected MailAttachmentError")
    except MailAttachmentError:
        pass


_P7_GATES: list[tuple[str, object]] = [
    ("P7-M-01-a-1", _gate_p7_m_01_a_1),
    ("P7-M-02-a-1", _gate_p7_m_02_a_1),
    ("P7-R-01-a-1", _gate_p7_r_01_a_1),
    ("P7-R-02-a-1", _gate_p7_r_02_a_1),
]


def register_p7_gates() -> None:
    for gate_id, fn in _P7_GATES:
        register_gate(gate_id, fn, depends=P7_DEPS[gate_id], layer="P7")  # type: ignore[arg-type]
