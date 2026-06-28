# -*- coding: utf-8
"""P10 L4 gate bodies — FULL_ARCHIVE + mail live harness."""

from __future__ import annotations

from pathlib import Path

from data_pc_origin.gates.registry import P10_DEPS, register_gate
from data_pc_origin.live_full_archive import (
    ARTIFACT_NAME as FULL_ARTIFACT,
    prepare_live_full_archive,
    run_live_full_archive,
)
from data_pc_origin.live_mail import (
    ARTIFACT_NAME as MAIL_ARTIFACT,
    prepare_live_mail,
    run_live_mail,
)
from data_pc_origin.p7_mail_hook import MailAttachmentError, MailJob, parse_mail_attachment


def _assert(condition: bool, msg: str = "") -> None:
    if not condition:
        raise AssertionError(msg or "assertion failed")


def _gate_p10_f_01_a_1() -> None:
    prep = prepare_live_full_archive("")
    _assert(isinstance(prep.ready, bool))


def _gate_p10_f_02_a_1() -> None:
    root = Path(__file__).resolve().parents[2]
    out = run_live_full_archive("", artifact_dir=root)
    _assert(out["status"] in ("skipped", "ok", "error", "dry_run"))
    _assert(out["mode"] == "full_archive")


def _gate_p10_f_03_a_1() -> None:
    artifact = Path(__file__).resolve().parents[2] / FULL_ARTIFACT
    _assert(artifact.is_file())


def _gate_p10_m_01_a_1() -> None:
    prep = prepare_live_mail("")
    _assert(isinstance(prep.ready, bool))


def _gate_p10_m_02_a_1() -> None:
    root = Path(__file__).resolve().parents[2]
    out = run_live_mail("", artifact_dir=root)
    _assert(out["status"] in ("skipped", "ok", "error", "dry_run"))
    _assert(out.get("entry") == "mail")


def _gate_p10_m_03_a_1() -> None:
    artifact = Path(__file__).resolve().parents[2] / MAIL_ARTIFACT
    _assert(artifact.is_file())


def _gate_p10_m_04_a_1() -> None:
    try:
        parse_mail_attachment(MailJob(attachment_path=r"G:\x.pdf"))
        _assert(False, "expected MailAttachmentError")
    except MailAttachmentError:
        pass


_P10_GATES: list[tuple[str, object]] = [
    ("P10-F-01-a-1", _gate_p10_f_01_a_1),
    ("P10-F-02-a-1", _gate_p10_f_02_a_1),
    ("P10-F-03-a-1", _gate_p10_f_03_a_1),
    ("P10-M-01-a-1", _gate_p10_m_01_a_1),
    ("P10-M-02-a-1", _gate_p10_m_02_a_1),
    ("P10-M-03-a-1", _gate_p10_m_03_a_1),
    ("P10-M-04-a-1", _gate_p10_m_04_a_1),
]


def register_p10_gates() -> None:
    for gate_id, fn in _P10_GATES:
        register_gate(gate_id, fn, depends=P10_DEPS[gate_id], layer="P10")  # type: ignore[arg-type]
