"""
data_pc_runtime — 데이터 PC 자동화 감시·게이트·파이프라인 호출

[사용자 관점] PC 로그인 후 백그라운드 상주 → Wi-Fi·G:·쿨다운 확인 →
  `촉매 반응 계산.process_new_gc_emails` (메일 → 엑셀 → G: → Origin).

[2026-06] data_pc_watch + data_pc_watchdog 이중 프로세스를 **supervisor 1개**로 통합.
  Origin Read-Only 팝업은 촉매 반응 계산.py 의 .origin_update.lock 이 담당.

레이어 (아래만 의존, 위는 조합):

  L0 probes   — 읽기만, 부작용 없음 (Wi-Fi / G: / IMAP / PID)
  L1 state    — JSON 원자 저장 (단일 진실 공급원)
  L2 gates    — L0+L1+설정 → 실행 허용 여부
  L2 lock     — 파이프라인 동시 실행 1개

L3 job runner · L4 supervisor — 진입: pythonw -m data_pc_runtime --script-dir <DIR>
검증: python -m data_pc_runtime.verify --live --dry-job --dry-supervisor
"""

from data_pc_runtime.layer0_probes import (
    GDriveProbe,
    GDriveProbeResult,
    ImapReachabilityProbe,
    NetworkProbeResult,
    PidProbe,
    WifiProbe,
    WifiProbeResult,
)
from data_pc_runtime.layer1_state import RuntimePaths, RuntimeState, StateStore
from data_pc_runtime.layer2_gates import GateConfig, GateEvaluator, GateVerdict
from data_pc_runtime.layer2_lock import PipelineLock
from data_pc_runtime.layer3_job import JobConfig, JobResult, JobRunner, load_gate_config, run_job_once
from data_pc_runtime.layer4_supervisor import (
    Supervisor,
    SupervisorConfig,
    cli_main,
    ensure_supervisor_once,
    is_supervisor_healthy,
    run_supervisor,
)

__all__ = [
    "GDriveProbe",
    "GDriveProbeResult",
    "GateConfig",
    "GateEvaluator",
    "GateVerdict",
    "JobConfig",
    "JobResult",
    "JobRunner",
    "ImapReachabilityProbe",
    "is_supervisor_healthy",
    "ensure_supervisor_once",
    "run_supervisor",
    "Supervisor",
    "SupervisorConfig",
    "cli_main",
    "NetworkProbeResult",
    "PidProbe",
    "PipelineLock",
    "RuntimePaths",
    "RuntimeState",
    "StateStore",
    "load_gate_config",
    "run_job_once",
    "WifiProbe",
    "WifiProbeResult",
]
