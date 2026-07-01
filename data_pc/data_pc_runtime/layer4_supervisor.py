# -*- coding: utf-8 -*-
"""
L4 — Supervisor: **프로세스 1개**로 감시 루프 + Job 호출.

기존 watchdog(watch 감시) + watch(폴링) + Ensure(중복 기동) 을 대체.

하위 단계:
  S1  시작 · status=starting · heartbeat 스레드
  S2  부팅 시 Job 1회 (선택, IMAP TCP 대기 후)
  S3  루프: JobRunner.run_once → sleep(poll_sec)
  S4  Ensure: is_supervisor_healthy? → 아니면 S5
  S5  spawn pythonw -m data_pc_runtime (중복 spawn 없음)
"""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
import threading
import time
from dataclasses import dataclass
from datetime import datetime

from data_pc_runtime.layer0_probes import ImapReachabilityProbe, PidProbe
from data_pc_runtime.layer1_state import RuntimePaths, RuntimeStatus, StateStore
from data_pc_runtime.layer2_gates import GateConfig
from data_pc_runtime.layer3_job import (
    JobConfig,
    JobRunner,
    PipelineCallback,
    _log,
    load_calc_pipeline,
    load_gate_config,
)

_RUNTIME_LOG = os.path.join(
    os.path.expanduser("~"), ".cursor", "gc-runtime-temp", "data_pc_runtime.log"
)

_SUBPROCESS_FLAGS = 0
if sys.platform == "win32" and hasattr(subprocess, "CREATE_NO_WINDOW"):
    _SUBPROCESS_FLAGS = subprocess.CREATE_NO_WINDOW


@dataclass(frozen=True)
class SupervisorConfig:
    poll_sec: int = 15
    boot_mail_check: bool = True
    boot_network_wait_sec: int = 90
    heartbeat_stale_sec: int = 180


def _env_int(name: str, default: int, minimum: int = 0) -> int:
    try:
        return max(minimum, int(os.getenv(name, str(default)).strip()))
    except (TypeError, ValueError):
        return default


def _env_bool(name: str, default: bool = False) -> bool:
    raw = os.getenv(name, "").strip().lower()
    if not raw:
        return default
    return raw in ("1", "true", "yes", "on")


def load_supervisor_config(script_dir: str) -> SupervisorConfig:
    try:
        from dotenv import load_dotenv
    except ImportError:
        load_dotenv = None  # type: ignore

    env_path = os.path.join(script_dir, "gc_automation.env")
    if load_dotenv and os.path.isfile(env_path):
        load_dotenv(env_path)

    return SupervisorConfig(
        poll_sec=_env_int("DATA_PC_WATCH_INTERVAL_SEC", 15, minimum=5),
        boot_mail_check=_env_bool("DATA_PC_BOOT_MAIL_CHECK", True),
        boot_network_wait_sec=_env_int("DATA_PC_BOOT_NETWORK_WAIT_SEC", 90, minimum=10),
        heartbeat_stale_sec=_env_int("DATA_PC_WATCH_HEARTBEAT_STALE_SEC", 180, minimum=60),
    )


def _parse_heartbeat_epoch(status: RuntimeStatus) -> float | None:
    raw = status.last_heartbeat or status.updated_at
    if not raw:
        return None
    try:
        return datetime.strptime(str(raw), "%Y-%m-%d %H:%M:%S").timestamp()
    except ValueError:
        return None


def is_supervisor_healthy(
    paths: RuntimePaths,
    *,
    stale_sec: int = 180,
) -> bool:
    """S4: status JSON + PID + heartbeat 로 단일 supervisor 생존 판정."""
    store = StateStore(paths)
    status = store.load_status()
    if not status.alive:
        return False
    pid = status.pid
    if pid and not PidProbe.alive(pid):
        return False
    hb = _parse_heartbeat_epoch(status)
    if hb is None:
        return False
    return (time.time() - hb) <= stale_sec


def spawn_supervisor(script_dir: str) -> bool:
    """S5: 숨김 pythonw 로 supervisor 1개만 기동."""
    pythonw = _pythonw_executable()
    cmd = [
        pythonw,
        "-m",
        "data_pc_runtime",
        "--script-dir",
        script_dir,
    ]
    try:
        subprocess.Popen(
            cmd,
            cwd=script_dir,
            creationflags=_SUBPROCESS_FLAGS,
        )
        _log(f"[supervisor] spawn pid requested script_dir={script_dir}")
        return True
    except OSError as exc:
        _log(f"[supervisor] spawn failed: {exc}")
        return False


def _pythonw_executable() -> str:
    exe = sys.executable
    if os.path.basename(exe).lower() == "pythonw.exe":
        return exe
    candidate = os.path.join(os.path.dirname(exe), "pythonw.exe")
    if os.path.isfile(candidate):
        return candidate
    return exe


def ensure_supervisor_once(script_dir: str) -> bool:
    """Ensure 작업 스케줄러 진입 — 살아있으면 False, 기동했으면 True."""
    paths = RuntimePaths(script_dir)
    cfg = load_supervisor_config(script_dir)
    if is_supervisor_healthy(paths, stale_sec=cfg.heartbeat_stale_sec):
        _log("[ensure] supervisor already healthy")
        return False
    _log("[ensure] supervisor missing or stale — spawning")
    return spawn_supervisor(script_dir)


class Supervisor:
    def __init__(
        self,
        script_dir: str,
        *,
        pipeline: PipelineCallback | None = None,
        job: JobRunner | None = None,
        sup_cfg: SupervisorConfig | None = None,
        gate: GateConfig | None = None,
    ) -> None:
        self.script_dir = script_dir
        self.paths = RuntimePaths(script_dir)
        self.store = StateStore(self.paths)
        self.sup_cfg = sup_cfg or load_supervisor_config(script_dir)
        self.gate = gate or load_gate_config(script_dir)
        self.job = job or JobRunner(
            self.paths,
            pipeline or load_calc_pipeline(script_dir),
            store=self.store,
        )
        self._stop = threading.Event()
        self._hb_interval = max(15, self.sup_cfg.poll_sec)

    def run_forever(self) -> None:
        _log(
            f"[supervisor] start pid={os.getpid()} poll={self.sup_cfg.poll_sec}s "
            f"stale={self.sup_cfg.heartbeat_stale_sec}s"
        )
        self._publish("starting", "data_pc_runtime supervisor")

        hb = threading.Thread(target=self._heartbeat_worker, daemon=True, name="supervisor-hb")
        hb.start()

        if self.sup_cfg.boot_mail_check:
            self._boot_mail_job()

        try:
            while not self._stop.is_set():
                self.job.run_once(
                    JobConfig(
                        gate=self.gate,
                        reason="메일 확인 → 계산 → G: → Origin (자동)",
                    )
                )
                self._stop.wait(self.sup_cfg.poll_sec)
        except KeyboardInterrupt:
            _log("[supervisor] KeyboardInterrupt")
        finally:
            self._stop.set()
            self._publish("stopped", "supervisor 종료", alive=False)

    def run_once_tick(self) -> None:
        """테스트용: 루프 1회."""
        self.job.run_once(
            JobConfig(gate=self.gate, reason="supervisor-tick"),
        )

    def _boot_mail_job(self) -> None:
        if not self._wait_imap(self.sup_cfg.boot_network_wait_sec):
            _log("[supervisor] boot IMAP wait timeout")
            self._publish("boot_network_wait", "부팅 후 네트워크 대기")
            return
        boot_gate = GateConfig(
            required_hotspot=self.gate.required_hotspot,
            cooldown_sec=0,
            gdrive_retry_sec=self.gate.gdrive_retry_sec,
            skip_wifi_check=self.gate.skip_wifi_check,
            check_imap_tcp=False,
        )
        self.job.run_once(
            JobConfig(
                gate=boot_gate,
                reason="부팅 후 미처리 메일 → 계산 → Origin",
            )
        )

    def _wait_imap(self, max_sec: int) -> bool:
        probe = ImapReachabilityProbe()
        attempts = max(1, max_sec // 5)
        for i in range(attempts):
            if probe.check().imap_reachable:
                return True
            if i == 0:
                _log("[supervisor] boot waiting for IMAP tcp")
            time.sleep(5)
        return False

    def _heartbeat_worker(self) -> None:
        while not self._stop.wait(self._hb_interval):
            status = self.store.load_status()
            status.alive = True
            status.pid = os.getpid()
            status.last_heartbeat = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            self.store.save_status(status)

    def _publish(self, code: str, message: str, *, alive: bool = True) -> None:
        status = self.store.load_status()
        status.alive = alive
        status.status_code = code
        status.message = message
        status.pid = os.getpid()
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        status.updated_at = now
        status.last_heartbeat = now
        if not status.started_at:
            status.started_at = now
        self.store.save_status(status)


def run_supervisor(script_dir: str) -> None:
    Supervisor(script_dir).run_forever()


def cli_main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="data_pc_runtime L4 supervisor")
    parser.add_argument(
        "--script-dir",
        default=os.path.join(os.path.expanduser("~"), "Desktop", ".cursor"),
    )
    parser.add_argument(
        "--ensure-once",
        action="store_true",
        help="supervisor 생존 확인 후 없으면 1회 기동 (작업 스케줄러)",
    )
    args = parser.parse_args(argv)

    if args.ensure_once:
        ensure_supervisor_once(args.script_dir)
        return 0

    run_supervisor(args.script_dir)
    return 0
