# -*- coding: utf-8
"""P5 — workflow 2→3→4 오케스트레이션 (mock runner 주입, 촉매·originpro 금지)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Mapping, Optional

from data_pc_origin.p0_routing import resolve_workflow_mode
from data_pc_origin.p0_types import Stage2Artifacts, WorkflowMode, WorkflowOptions
from data_pc_origin.p1_payload import Stage2Metadata, build_payload_from_stage2
from data_pc_origin.p2_paths import normalize_opju_path, probe_stage4_suffix
from data_pc_origin.p4_origin_stage import OriginRunner, Stage4Result, maybe_run_stage4

Stage2Runner = Callable[[str], Optional["Stage2RunResult"]]
Stage3Runner = Callable[[str, "Stage2RunResult"], Optional["Stage3Result"]]
PreStage4Hook = Callable[
    [WorkflowMode, WorkflowOptions, "Stage2RunResult", Optional["Stage3Result"]],
    Optional[str],
]


@dataclass(frozen=True)
class Stage2RunResult:
    """2단계 mock/live 산출 — P6 adapter가 채움."""

    artifacts: Stage2Artifacts
    metadata: Stage2Metadata


@dataclass(frozen=True)
class Stage3Result:
    """3단계 G: archive — 촉매 setup_experiment_folder 대응."""

    target_opju: str
    archive_xlsx: str
    ok: bool = True


@dataclass(frozen=True)
class WorkflowResult:
    ok: bool
    mode: WorkflowMode
    stage2: Stage2RunResult | None
    stage3: Stage3Result | None
    stage4: Stage4Result | None
    error_message: str = ""


def plan_workflow_stages(mode: WorkflowMode) -> tuple[int, ...]:
    """촉매 L2227–2245 — 실행할 단계 번호."""
    if mode == WorkflowMode.CALC_ONLY:
        return (2,)
    if mode == WorkflowMode.OPJU_ONLY:
        return (2, 4)
    return (2, 3, 4)


def resolve_stage4_opju(
    mode: WorkflowMode,
    options: WorkflowOptions,
    stage3: Stage3Result | None,
) -> str:
    if mode == WorkflowMode.OPJU_ONLY:
        return normalize_opju_path(options.opju_path)
    if stage3 is not None:
        return normalize_opju_path(stage3.target_opju)
    return ""


def build_workflow_payload(
    stage2: Stage2RunResult,
    *,
    opju_path: str,
    mode: WorkflowMode,
):
    """P1 payload — mode별 save_in_place."""
    return build_payload_from_stage2(
        stage2.artifacts,
        stage2.metadata,
        opju_path=opju_path,
        mode=mode,
    )


def run_workflow_stages(
    excel_path: str,
    options: WorkflowOptions,
    *,
    stage2_runner: Stage2Runner,
    stage3_runner: Stage3Runner | None = None,
    origin_runner: OriginRunner | None = None,
    explicit_skip: Optional[bool] = None,
    environ: Optional[Mapping[str, str]] = None,
    pre_stage4_hook: PreStage4Hook | None = None,
) -> WorkflowResult:
    """
    P0 routing + P1–P4 조합 — 촉매 `run_workflow_for_file` mock 대응.

    stage2_runner / stage3_runner 는 P6에서 importlib로 교체.
    """
    mode = resolve_workflow_mode(options)
    plan = plan_workflow_stages(mode)

    stage2 = stage2_runner(excel_path)
    if stage2 is None:
        return WorkflowResult(
            ok=False,
            mode=mode,
            stage2=None,
            stage3=None,
            stage4=None,
        )

    stage3: Stage3Result | None = None
    if 3 in plan:
        if stage3_runner is None:
            return WorkflowResult(
                ok=False,
                mode=mode,
                stage2=stage2,
                stage3=None,
                stage4=None,
            )
        stage3 = stage3_runner(excel_path, stage2)
        if stage3 is None or not stage3.ok:
            return WorkflowResult(
                ok=False,
                mode=mode,
                stage2=stage2,
                stage3=stage3,
                stage4=None,
            )

    stage4: Stage4Result | None = None
    if 4 in plan:
        opju = resolve_stage4_opju(mode, options, stage3)
        if pre_stage4_hook is not None:
            hook_err = pre_stage4_hook(mode, options, stage2, stage3)
            if hook_err:
                return WorkflowResult(
                    ok=False,
                    mode=mode,
                    stage2=stage2,
                    stage3=stage3,
                    stage4=None,
                    error_message=hook_err,
                )
        probe = probe_stage4_suffix(opju)
        if not probe.ok:
            return WorkflowResult(
                ok=False,
                mode=mode,
                stage2=stage2,
                stage3=stage3,
                stage4=None,
            )
        payload = build_workflow_payload(stage2, opju_path=opju, mode=mode)
        stage4 = maybe_run_stage4(
            payload,
            options=options,
            explicit=explicit_skip,
            environ=environ,
            runner=origin_runner,
        )
        if not stage4.ok:
            return WorkflowResult(
                ok=False,
                mode=mode,
                stage2=stage2,
                stage3=stage3,
                stage4=stage4,
            )

    return WorkflowResult(
        ok=True,
        mode=mode,
        stage2=stage2,
        stage3=stage3,
        stage4=stage4,
    )
