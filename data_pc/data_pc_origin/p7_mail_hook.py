# -*- coding: utf-8
"""P7 — 메일 1건 → P5 workflow (mock E2E)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping, Optional

from data_pc_origin.p0_types import WorkflowOptions
from data_pc_origin.p4_origin_stage import OriginRunner
from data_pc_origin.p5_workflow import (
    Stage2Runner,
    Stage3Runner,
    WorkflowResult,
    run_workflow_stages,
)


class MailAttachmentError(ValueError):
    """첨부가 KCH 엑셀이 아님."""


@dataclass(frozen=True)
class MailJob:
    """촉매 1단계 IMAP 1건 — attachment 경로만 (P7 mock)."""

    attachment_path: str
    subject: str = ""


def parse_mail_attachment(job: MailJob) -> str:
    path = (job.attachment_path or "").strip()
    lower = path.lower()
    if not lower.endswith((".xlsx", ".xls")):
        raise MailAttachmentError(f"not excel: {path!r}")
    return path


def run_mail_workflow(
    job: MailJob,
    options: WorkflowOptions,
    *,
    stage2_runner: Stage2Runner,
    stage3_runner: Stage3Runner | None = None,
    origin_runner: OriginRunner | None = None,
    explicit_skip: Optional[bool] = None,
    environ: Optional[Mapping[str, str]] = None,
) -> WorkflowResult:
    """메일 첨부 → P5 — P6 adapter runner 주입."""
    excel_path = parse_mail_attachment(job)
    return run_workflow_stages(
        excel_path,
        options,
        stage2_runner=stage2_runner,
        stage3_runner=stage3_runner,
        origin_runner=origin_runner,
        explicit_skip=explicit_skip,
        environ=environ,
    )
