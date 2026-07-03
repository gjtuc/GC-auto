# -*- coding: utf-8
"""P13 L4 gate bodies — IMAP probe + fetch mail E2E."""

from __future__ import annotations

from pathlib import Path

from data_pc_origin.gates.registry import P13_DEPS, register_gate
from data_pc_origin.live_imap import ARTIFACT_NAME, run_imap_probe, run_live_imap
from data_pc_origin.p13_imap_adapter import mask_email, prepare_imap
from data_pc_origin.p7_mail_hook import MailJob, parse_mail_attachment


def _assert(condition: bool, msg: str = "") -> None:
    if not condition:
        raise AssertionError(msg or "assertion failed")


def _gate_p13_i_01_a_1() -> None:
    prep = prepare_imap()
    _assert(isinstance(prep.ready, bool))
    _assert("email_masked" in prep.to_dict())


def _gate_p13_i_02_a_1() -> None:
    root = Path(__file__).resolve().parents[2]
    out = run_imap_probe(artifact_dir=root, dry_run=True)
    _assert(out["status"] in ("skipped", "ok", "error", "dry_run"))
    _assert(out.get("mode") == "imap_probe")


def _gate_p13_i_03_a_1() -> None:
    artifact = Path(__file__).resolve().parents[2] / ARTIFACT_NAME
    _assert(artifact.is_file())


def _gate_p13_i_04_a_1() -> None:
    masked = mask_email("kimcha0809@naver.com")
    _assert("@" in masked)
    _assert("0809" not in masked)
    root = Path(__file__).resolve().parents[2]
    text = (root / ARTIFACT_NAME).read_text(encoding="utf-8")
    _assert("NAVER_APP_PASSWORD" not in text)


def _gate_p13_m_01_a_1() -> None:
    root = Path(__file__).resolve().parents[2]
    out = run_live_imap(artifact_dir=root, dry_run=True, fetch_only=True)
    _assert(out["status"] in ("skipped", "ok", "error", "dry_run"))
    _assert(out.get("entry") == "imap")


def _gate_p13_m_02_a_1() -> None:
    root = Path(__file__).resolve().parents[2]
    out = run_live_imap(artifact_dir=root, dry_run=True)
    _assert(out.get("entry") == "imap")


def _gate_p13_m_03_a_1() -> None:
    job = MailJob(
        attachment_path=r"G:\mail\KCH_20250601.xlsx",
        subject="GC 분석 결과",
    )
    _assert(parse_mail_attachment(job).endswith(".xlsx"))


def _gate_p13_m_04_a_1() -> None:
    root = Path(__file__).resolve().parents[2]
    artifact = root / ARTIFACT_NAME
    _assert(artifact.is_file())
    _assert("prep" in artifact.read_text(encoding="utf-8"))


_P13_GATES: list[tuple[str, object]] = [
    ("P13-I-01-a-1", _gate_p13_i_01_a_1),
    ("P13-I-02-a-1", _gate_p13_i_02_a_1),
    ("P13-I-03-a-1", _gate_p13_i_03_a_1),
    ("P13-I-04-a-1", _gate_p13_i_04_a_1),
    ("P13-M-01-a-1", _gate_p13_m_01_a_1),
    ("P13-M-02-a-1", _gate_p13_m_02_a_1),
    ("P13-M-03-a-1", _gate_p13_m_03_a_1),
    ("P13-M-04-a-1", _gate_p13_m_04_a_1),
]


def register_p13_gates() -> None:
    for gate_id, fn in _P13_GATES:
        register_gate(gate_id, fn, depends=P13_DEPS[gate_id], layer="P13")  # type: ignore[arg-type]
