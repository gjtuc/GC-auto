# -*- coding: utf-8
"""P0-R — workflow mode resolution."""

from __future__ import annotations

from data_pc_origin.p0_types import WorkflowMode, WorkflowOptions


def resolve_workflow_mode(options: WorkflowOptions) -> WorkflowMode:
    """
    촉매 분기 우선순위 (L2227–2245):
      1. opju_path 지정 → OPJU_ONLY
      2. auto_archive False → CALC_ONLY
      3. else → FULL_ARCHIVE
    """
    if (options.opju_path or "").strip():
        return WorkflowMode.OPJU_ONLY
    if not options.auto_archive:
        return WorkflowMode.CALC_ONLY
    return WorkflowMode.FULL_ARCHIVE


def should_run_stage4(options: WorkflowOptions) -> bool:
    return not options.skip_stage4
