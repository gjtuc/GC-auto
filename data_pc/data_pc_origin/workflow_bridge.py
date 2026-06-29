# -*- coding: utf-8
"""P8 — 촉매 `run_workflow_for_file` ↔ P5/P6 workflow bridge."""

from __future__ import annotations

import os
import sys
from typing import Any, Callable, Mapping, Optional

from data_pc_origin.p0_routing import resolve_workflow_mode
from data_pc_origin.p0_types import Stage2Artifacts, WorkflowMode, WorkflowOptions
from data_pc_origin.p4_origin_stage import OriginRunner
from data_pc_origin.p5_workflow import (
    PreStage4Hook,
    Stage2RunResult,
    Stage3Result,
    WorkflowResult,
    run_workflow_stages,
)
from data_pc_origin.p6_catalyst_adapter import make_stage2_runner, make_stage3_runner, Stage2Runner
from data_pc_origin.pipeline_bridge import ensure_import_path, run_origin_update

PrintFn = Callable[[str], None]


def build_workflow_options(
    *,
    opju_path: str | None = None,
    auto_archive: bool = True,
) -> WorkflowOptions:
    """촉매 CLI 인자 → P0 `WorkflowOptions`."""
    return WorkflowOptions(
        opju_path=(opju_path or "").strip(),
        auto_archive=auto_archive,
        skip_stage4=False,
    )


def _default_origin_runner(payload) -> Any:
    return run_origin_update(
        payload.opju_path,
        payload.df,
        payload.sample_name,
        save_in_place=payload.save_in_place,
        identity_key=payload.identity_key,
    )


def make_stage2_runner_with_ux(
    module: Any,
    *,
    printer: PrintFn = print,
) -> Callable[[str], Stage2RunResult | None]:
    """촉매 2단계 UX + P6 runner."""
    inner = make_stage2_runner(module)

    def _run(excel_path: str) -> Stage2RunResult | None:
        printer(f"\n[2단계] KCH 원본 계산 중: {os.path.basename(excel_path)}")
        stage2 = inner(excel_path)
        if stage2 is None:
            printer("❌ 장비를 판별할 수 없습니다. (수소 피크 유무 확인)")
            return None
        _print_stage2_success(stage2, module, printer)
        return stage2

    return _run


def _print_stage2_success(
    stage2: Stage2RunResult,
    module: Any,
    printer: PrintFn,
) -> None:
    saved = stage2.metadata.saved_excel
    printer(f" ✅ 엑셀 계산 완료: {os.path.basename(saved)}")
    processed = getattr(module, "DATA_PC_PROCESSED_DIR", "")
    work = getattr(module, "_DATA_PC_WORK", "DATA_PC")
    if processed and os.path.normpath(os.path.dirname(saved)) == os.path.normpath(
        processed
    ):
        printer(f"    검토용 사본: {work}\\processed\\")
    feed = stage2.artifacts.feed_source_desc
    if feed:
        printer(f" 📊 Feed ppm 기준: {feed}")
    printer(f" 🏷️ Origin 시료명: {stage2.metadata.sample_name}")
    if hasattr(module, "generate_experiment_basename") and hasattr(
        module, "reaction_type_from_output_file"
    ):
        base = module.generate_experiment_basename(saved)
        rxn = module.reaction_type_from_output_file(saved)
        printer(f" 📁 실험 폴더명: {base} ({rxn})")
    if stage2.artifacts.warnings:
        printer("\n" + "!" * 65)
        printer(" 🚨 [장비/데이터 상태 점검] 엑셀 처리 중 특이사항이 감지되었습니다!")
        for w in stage2.artifacts.warnings:
            printer(f"   - {w}")
        printer("!" * 65)


def make_opju_pre_stage4_hook(module: Any) -> PreStage4Hook:
    """촉매 L2228–2236 — OPJU_ONLY opju 사전 검사 (2단계 이후)."""

    def _hook(
        mode: WorkflowMode,
        options: WorkflowOptions,
        stage2: Stage2RunResult,
        _stage3: Stage3Result | None,
    ) -> Optional[str]:
        if mode != WorkflowMode.OPJU_ONLY:
            return None
        opju = (options.opju_path or "").strip()
        if opju.upper().startswith("G:") and hasattr(module, "_require_g_drive_access"):
            try:
                module._require_g_drive_access()
            except Exception as exc:
                gdrive = getattr(module, "GDriveUnavailableError", None)
                if gdrive is not None and isinstance(exc, gdrive):
                    return module._g_drive_unavailable_message()
                return str(exc)
        if os.path.exists(opju) and opju.lower().endswith(".opju"):
            return None
        if opju.upper().startswith("G:") and hasattr(module, "_is_g_drive_available"):
            if not module._is_g_drive_available():
                saved = stage2.metadata.saved_excel
                msg = module._g_drive_unavailable_message()
                if saved:
                    return f"{msg}\n    (계산 파일: {saved})"
                return msg
        return "❌ 올바른 Origin 파일(.opju)이 아닙니다."

    return _hook


def print_workflow_outcome(result: WorkflowResult, *, printer: PrintFn = print) -> None:
    """촉매 L2238–2257 완료 메시지."""
    if not result.ok:
        if result.error_message:
            printer(result.error_message)
        return
    if result.mode == WorkflowMode.CALC_ONLY:
        printer("\n[3~4단계] --no-archive: G: 폴더 생성 및 Origin 연동을 건너뜁니다.")
        return
    if result.stage4 is not None and result.stage4.skipped:
        printer(f"\n{result.stage4.skip_reason}")
        if result.mode == WorkflowMode.FULL_ARCHIVE and result.stage3 is not None:
            printer("\n ✅ 완료 — G: 엑셀 반영 (Origin 생략)")
            printer(f"    {result.stage3.archive_xlsx}")
        return
    if result.mode == WorkflowMode.FULL_ARCHIVE and result.stage3 is not None:
        printer("\n ✅ 전체 완료 — G: 실험 폴더 및 Origin 반영")
        printer(f"    {result.stage3.archive_xlsx}")


def run_workflow_bridged(
    excel_path: str,
    *,
    opju_path: str | None = None,
    auto_archive: bool = True,
    skip_origin: bool | None = None,
    catalyst_module: Any,
    origin_runner: OriginRunner | None = None,
    environ: Mapping[str, str] | None = None,
    printer: PrintFn = print,
) -> bool:
    """촉매 `run_workflow_for_file` 대체 진입 — P5/P6 위임."""
    ok, _result = run_workflow_bridged_detailed(
        excel_path,
        opju_path=opju_path,
        auto_archive=auto_archive,
        skip_origin=skip_origin,
        catalyst_module=catalyst_module,
        origin_runner=origin_runner,
        environ=environ,
        printer=printer,
    )
    return ok


def run_workflow_bridged_detailed(
    excel_path: str,
    *,
    opju_path: str | None = None,
    auto_archive: bool = True,
    skip_origin: bool | None = None,
    catalyst_module: Any,
    origin_runner: OriginRunner | None = None,
    environ: Mapping[str, str] | None = None,
    printer: PrintFn = print,
    stage2_runner: Stage2Runner | None = None,
    stage3_runner: Stage3Runner | None = None,
) -> tuple[bool, WorkflowResult | None]:
    """
    `run_workflow_bridged` + `WorkflowResult` — live harness artifact용.

    `skip_origin`: None 이면 env, True/False 명시 override.
    """
    ensure_import_path()
    path = (excel_path or "").strip()
    if not os.path.exists(path) or not path.lower().endswith((".xlsx", ".xls")):
        printer("❌ 올바른 엑셀 파일이 아닙니다.")
        return False, None

    options = build_workflow_options(opju_path=opju_path, auto_archive=auto_archive)
    env = environ if environ is not None else os.environ
    saved_excel: str | None = None

    try:
        result = run_workflow_stages(
            path,
            options,
            stage2_runner=stage2_runner
            or make_stage2_runner_with_ux(catalyst_module, printer=printer),
            stage3_runner=stage3_runner or make_stage3_runner(catalyst_module),
            origin_runner=origin_runner or _default_origin_runner,
            explicit_skip=skip_origin,
            environ=env,
            pre_stage4_hook=make_opju_pre_stage4_hook(catalyst_module),
        )
        if result.stage2 is not None:
            saved_excel = result.stage2.metadata.saved_excel
        print_workflow_outcome(result, printer=printer)
        return result.ok, result
    except Exception as exc:
        gdrive = getattr(catalyst_module, "GDriveUnavailableError", None)
        if gdrive is not None and isinstance(exc, gdrive):
            printer(catalyst_module._g_drive_unavailable_message())
            if saved_excel:
                printer(f"    (계산 파일: {saved_excel})")
            return False, None
        if isinstance(exc, FileNotFoundError):
            if hasattr(catalyst_module, "_is_g_drive_available") and (
                not catalyst_module._is_g_drive_available()
            ):
                printer(catalyst_module._g_drive_unavailable_message())
                if saved_excel:
                    printer(f"    (계산 파일: {saved_excel})")
            else:
                printer(f"❌ 경로 오류: {exc}")
            return False, None
        if isinstance(exc, OSError):
            if auto_archive and hasattr(catalyst_module, "_is_g_drive_available"):
                if not catalyst_module._is_g_drive_available():
                    printer(catalyst_module._g_drive_unavailable_message())
                    if saved_excel:
                        printer(f"    (계산 파일: {saved_excel})")
                    return False, None
            printer(f"❌ 파일 시스템 오류: {exc}")
            return False, None
        if isinstance(exc, FileExistsError):
            printer(f"❌ {exc}")
            return False, None
        printer(f"❌ 분석 중 치명적 에러가 발생했습니다: {exc}")
        originpro = getattr(catalyst_module, "_originpro", None)
        if originpro is not None:
            try:
                originpro.exit()
            except Exception:
                pass
        return False, None


def catalyst_module_from_sys() -> Any | None:
    """로드된 촉매 모듈 탐색 — 테스트·게이트용."""
    for mod in sys.modules.values():
        file_path = getattr(mod, "__file__", "") or ""
        if file_path.endswith("촉매 반응 계산.py") and hasattr(mod, "process_excel"):
            return mod
    return None
