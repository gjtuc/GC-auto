# -*- coding: utf-8 -*-
"""
L3 — Job: 게이트 통과 시 파이프라인 **정확히 1회** 실행.

하위 단계:
  J1  GateEvaluator.evaluate
  J2  RUN 아니면 종료 (상태만 기록)
  J3  PipelineLock.try_acquire
  J4  status → running_pipeline
  J5  pipeline_callback()  (촉매 반응 계산.process_new_gc_emails)
  J6  결과 파싱 (workflow_count, gdrive_retry_needed)
  J7  StateStore.mark_pipeline_finished
  J8  status → pipeline_done | gdrive_retry | error
  J9  lock.release
"""

from __future__ import annotations

import os
import traceback
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Callable

from data_pc_runtime.layer1_state import RuntimePaths, RuntimeStatus, StateStore
from data_pc_runtime.layer2_gates import GateAction, GateConfig, GateEvaluator, GateVerdict
from data_pc_runtime.layer2_lock import PipelineLock

PipelineCallback = Callable[[], Any]

_RUNTIME_LOG = os.path.join(
    os.path.expanduser("~"), ".cursor", "gc-runtime-temp", "data_pc_runtime.log"
)


@dataclass(frozen=True)
class JobResult:
    ran: bool
    status_code: str
    message: str
    workflow_count: int = 0
    gdrive_retry: bool = False


@dataclass(frozen=True)
class JobConfig:
    gate: GateConfig
    reason: str = "메일 확인 → 계산 → G: → Origin (자동)"


def _log(line: str) -> None:
    os.makedirs(os.path.dirname(_RUNTIME_LOG), exist_ok=True)
    stamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    try:
        with open(_RUNTIME_LOG, "a", encoding="utf-8") as f:
            f.write(f"{stamp} {line}\n")
    except OSError:
        pass


def _parse_pipeline_result(result: Any) -> tuple[int, bool]:
    if hasattr(result, "workflow_count"):
        return (
            int(result.workflow_count),
            bool(getattr(result, "gdrive_retry_needed", False)),
        )
    if isinstance(result, tuple) and len(result) >= 2:
        return int(result[0]), bool(result[1])
    if isinstance(result, int):
        return result, False
    return 0, False


def load_gate_config(script_dir: str) -> GateConfig:
    """gc_automation.env → GateConfig."""
    try:
        from dotenv import load_dotenv
    except ImportError:
        load_dotenv = None  # type: ignore

    env_path = os.path.join(script_dir, "gc_automation.env")
    if load_dotenv and os.path.isfile(env_path):
        load_dotenv(env_path)

    def _int(name: str, default: int) -> int:
        try:
            return int(os.getenv(name, str(default)).strip())
        except (TypeError, ValueError):
            return default

    required = (
        os.getenv("REQUIRED_HOTSPOT", "").strip()
        or os.getenv("REQUIRED_HOTSPOT_SSID", "").strip()
        or "iptime,iptime 2,iptime_5G"
    )
    hours = _int("DATA_PC_AUTO_MAIL_COOLDOWN_HOURS", 1)
    return GateConfig(
        required_hotspot=required,
        cooldown_sec=max(0, hours) * 3600,
        gdrive_retry_sec=_int("DATA_PC_GDRIVE_RETRY_SEC", 900),
        skip_wifi_check=os.getenv("DATA_PC_SKIP_WIFI_CHECK", "").strip().lower()
        in ("1", "true", "yes"),
        check_imap_tcp=False,
    )


def load_calc_pipeline(script_dir: str) -> PipelineCallback:
    """촉매 반응 계산.py 의 process_new_gc_emails 로드."""
    import importlib.util

    calc_path = os.path.join(script_dir, "촉매 반응 계산.py")
    spec = importlib.util.spec_from_file_location("gc_calc_runtime_job", calc_path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"스크립트 로드 실패: {calc_path}")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    fn = getattr(mod, "process_new_gc_emails", None)
    if not callable(fn):
        raise RuntimeError("process_new_gc_emails 없음")
    return fn


class JobRunner:
    def __init__(
        self,
        paths: RuntimePaths,
        pipeline: PipelineCallback,
        *,
        evaluator: GateEvaluator | None = None,
        store: StateStore | None = None,
    ) -> None:
        self.paths = paths
        self.pipeline = pipeline
        self.store = store or StateStore(paths)
        self.evaluator = evaluator or GateEvaluator(paths, store=self.store)

    def run_once(self, config: JobConfig) -> JobResult:
        verdict = self.evaluator.evaluate(config.gate)
        self._write_status_from_verdict(verdict, running=False)

        if verdict.action != GateAction.RUN:
            _log(f"[job] skip code={verdict.status_code} msg={verdict.message}")
            return JobResult(
                ran=False,
                status_code=verdict.status_code,
                message=verdict.message,
            )

        lock = PipelineLock(self.paths.pipeline_lock)
        if not lock.try_acquire():
            msg = "다른 파이프라인 실행 중"
            self._write_status("processing", msg, verdict)
            _log(f"[job] skip lock busy")
            return JobResult(ran=False, status_code="processing", message=msg)

        try:
            return self._execute(config, verdict)
        finally:
            lock.release()

    def _execute(self, config: JobConfig, verdict: GateVerdict) -> JobResult:
        reason = config.reason
        _log(f"[job] start reason={reason}")
        self._write_status("running_pipeline", reason, verdict)

        try:
            raw = self.pipeline()
            workflow_count, gdrive_retry = _parse_pipeline_result(raw)
        except Exception as exc:
            msg = f"파이프라인 실패: {exc}"
            _log(f"[job] error {type(exc).__name__}: {exc}")
            _log(traceback.format_exc())
            self._write_status("error", msg, verdict)
            return JobResult(
                ran=True,
                status_code="error",
                message=msg,
                workflow_count=0,
                gdrive_retry=False,
            )

        self.store.mark_pipeline_finished(
            workflow_count=workflow_count,
            gdrive_retry=gdrive_retry,
        )

        if gdrive_retry:
            retry_min = config.gate.gdrive_retry_sec // 60
            msg = (
                f"G: 잠금 — {retry_min}분 후 재시도 "
                f"(workflow={workflow_count})"
            )
            code = "gdrive_retry"
        else:
            msg = f"파이프라인 완료 — {workflow_count}건 시료 반영"
            code = "pipeline_done"

        _log(f"[job] done code={code} workflows={workflow_count} gdrive_retry={gdrive_retry}")
        self._write_status(code, msg, verdict, workflow_count=workflow_count)
        return JobResult(
            ran=True,
            status_code=code,
            message=msg,
            workflow_count=workflow_count,
            gdrive_retry=gdrive_retry,
        )

    def _write_status_from_verdict(self, verdict: GateVerdict, *, running: bool) -> None:
        if verdict.action == GateAction.RUN and not running:
            return
        self._write_status(verdict.status_code, verdict.message, verdict)

    def _write_status(
        self,
        code: str,
        message: str,
        verdict: GateVerdict,
        *,
        workflow_count: int | None = None,
    ) -> None:
        status = self.store.load_status()
        status.alive = True
        status.status_code = code
        status.message = message
        status.pid = os.getpid()
        status.wifi_ssid = verdict.wifi_ssid
        status.wifi_ready = verdict.wifi_ready
        status.gate_detail = verdict.detail
        status.cooldown_remaining_sec = verdict.cooldown_remaining_sec
        status.updated_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        status.last_heartbeat = status.updated_at
        if workflow_count is not None:
            status.gate_detail = f"workflows={workflow_count}"
        self.store.save_status(status)


def run_job_once(
    script_dir: str,
    *,
    reason: str | None = None,
    skip_wifi_check: bool = False,
    pipeline: PipelineCallback | None = None,
) -> JobResult:
    """CLI/감시에서 호출하는 1회 실행 진입점."""
    paths = RuntimePaths(script_dir)
    gate = load_gate_config(script_dir)
    if skip_wifi_check:
        gate = GateConfig(
            required_hotspot=gate.required_hotspot,
            cooldown_sec=gate.cooldown_sec,
            gdrive_retry_sec=gate.gdrive_retry_sec,
            skip_wifi_check=True,
            check_imap_tcp=gate.check_imap_tcp,
        )
    job = JobRunner(
        paths,
        pipeline or load_calc_pipeline(script_dir),
    )
    return job.run_once(
        JobConfig(
            gate=gate,
            reason=reason or "메일 확인 → 계산 → G: → Origin (자동)",
        )
    )
