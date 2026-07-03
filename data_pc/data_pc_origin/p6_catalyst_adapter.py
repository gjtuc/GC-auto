# -*- coding: utf-8
"""P6 — 촉매 반응 계산.py importlib adapter (테스트는 mock module)."""

from __future__ import annotations

import importlib.util
import os
import sys
from pathlib import Path
from typing import Any, Mapping, Optional

from data_pc_origin.p0_types import Stage2Artifacts, WorkflowOptions
from data_pc_origin.p1_payload import assemble_stage2_metadata
from data_pc_origin.p4_origin_stage import OriginRunner
from data_pc_origin.p5_workflow import (
    Stage2RunResult,
    Stage2Runner,
    Stage3Result,
    Stage3Runner,
    WorkflowResult,
    run_workflow_stages,
)

_ADAPTER_ROOT = Path(__file__).resolve().parent.parent


class CatalystLoadError(OSError):
    """촉매 스크립트 로드 실패."""


def default_catalyst_path() -> Path:
    return _ADAPTER_ROOT / "촉매 반응 계산.py"


def load_catalyst_module(path: Path | None = None) -> Any:
    """importlib — P6 게이트·live는 mock/fixture 권장."""
    script = (path or default_catalyst_path()).resolve()
    if not script.is_file():
        raise CatalystLoadError(f"catalyst script not found: {script}")
    mod_name = f"_catalyst_pipeline_{script.stem}"
    spec = importlib.util.spec_from_file_location(mod_name, script)
    if spec is None or spec.loader is None:
        raise CatalystLoadError(f"cannot load spec: {script}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[mod_name] = module
    spec.loader.exec_module(module)
    return module


def _unpack_sample_name(module, excel_path, saved_excel, warnings):
    eq = (
        module.equipment_from_output_file(saved_excel)
        if hasattr(module, "equipment_from_output_file")
        else None
    )
    result = module.generate_sample_name(excel_path, equipment=eq)
    if isinstance(result, tuple):
        name, extra_warn, needs_input, question = result[0], list(result[1]), result[2], result[3]
        warnings = list(warnings or ())
        warnings.extend(extra_warn)
        origin_skip = ""
        if needs_input:
            origin_skip = question
            warnings.append(f"❌ Origin Comments 확인 필요:\n{question}")
        if not name:
            name = f"UNRESOLVED_{os.path.basename(excel_path)[:40]}"
        return name, tuple(warnings), origin_skip
    return result, tuple(warnings or ()), ""


def make_stage2_runner(module: Any) -> Stage2Runner:
    """촉매 process_excel → P5 Stage2RunResult."""

    def _run(excel_path: str) -> Stage2RunResult | None:
        df, saved_excel, warnings, _feed = module.process_excel(excel_path)
        if df is None:
            return None
        sample_name, warn_tuple, origin_skip = _unpack_sample_name(
            module, excel_path, str(saved_excel or ""), warnings
        )
        meta = assemble_stage2_metadata(
            sample_name=sample_name,
            identity_key=module._experiment_identity_key(excel_path),
            saved_excel=str(saved_excel or ""),
        )
        arts = Stage2Artifacts(
            df=df,
            saved_excel=str(saved_excel or ""),
            warnings=warn_tuple,
            feed_source_desc=str(_feed or ""),
            origin_skip_reason=origin_skip,
        )
        return Stage2RunResult(artifacts=arts, metadata=meta)

    return _run


def make_stage3_runner(module: Any) -> Stage3Runner:
    """촉매 setup_experiment_folder → P5 Stage3Result."""

    def _run(excel_path: str, stage2: Stage2RunResult) -> Stage3Result | None:
        reaction = module.reaction_type_from_output_file(stage2.metadata.saved_excel)
        _folder, target_opju, archive_xlsx = module.setup_experiment_folder(
            excel_path,
            stage2.metadata.saved_excel,
            reaction,
        )
        if not target_opju:
            return None
        return Stage3Result(
            target_opju=str(target_opju),
            archive_xlsx=str(archive_xlsx or ""),
        )

    return _run


def run_workflow_with_catalyst(
    excel_path: str,
    options: WorkflowOptions,
    *,
    catalyst_path: Path | None = None,
    module: Any | None = None,
    origin_runner: OriginRunner | None = None,
    explicit_skip: Optional[bool] = None,
    environ: Optional[Mapping[str, str]] = None,
) -> WorkflowResult:
    """P5 + importlib — 촉매 `run_workflow_for_file` 대체 진입 (mock/live)."""
    mod = module if module is not None else load_catalyst_module(catalyst_path)
    return run_workflow_stages(
        excel_path,
        options,
        stage2_runner=make_stage2_runner(mod),
        stage3_runner=make_stage3_runner(mod),
        origin_runner=origin_runner,
        explicit_skip=explicit_skip,
        environ=environ,
    )
