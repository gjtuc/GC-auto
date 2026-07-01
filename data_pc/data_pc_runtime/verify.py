# -*- coding: utf-8 -*-
"""
data_pc_runtime 검증 — L0~L4 변경 후 **반드시** 실행 후 배포.

  python -m data_pc_runtime.verify              # 단위 테스트
  python -m data_pc_runtime.verify --live       # Wi-Fi/G: 프로브
  python -m data_pc_runtime.verify --dry-job    # L3 Job mock
  python -m data_pc_runtime.verify --dry-supervisor  # L4 tick mock
"""
from __future__ import annotations

import argparse
import os
import sys
import tempfile
import unittest
from pathlib import Path

from data_pc_runtime.layer2_gates import GateConfig

_ROOT = Path(__file__).resolve().parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))


def _run_unit_tests() -> bool:
    loader = unittest.TestLoader()
    suite = loader.discover(
        str(Path(__file__).parent / "tests"),
        pattern="test_*.py",
    )
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    return result.wasSuccessful()


def _run_live_probes() -> bool:
    from data_pc_runtime.layer0_probes import GDriveProbe, WifiProbe, parse_required_ssids
    from data_pc_runtime.layer1_state import RuntimePaths, StateStore
    from data_pc_runtime.layer2_gates import GateConfig, GateEvaluator

    script_dir = str(_ROOT)
    paths = RuntimePaths(script_dir)
    allowed = parse_required_ssids("iptime,iptime 2,iptime_5G")

    wifi = WifiProbe()
    w = wifi.check(allowed)
    print(f"[live] Wi-Fi kind={w.kind.value} ssid={w.ssid!r} detail={w.detail}")

    g = GDriveProbe().check()
    print(f"[live] G: available={g.available} root={g.root} detail={g.detail}")

    ev = GateEvaluator(paths, wifi=wifi, gdrive=GDriveProbe(g.root))
    verdict = ev.evaluate(GateConfig())
    print(
        f"[live] Gate action={verdict.action.value} "
        f"code={verdict.status_code} remaining={verdict.cooldown_remaining_sec}s"
    )

    store = StateStore(paths)
    state = store.load_state()
    print(
        f"[live] State workflows={state.last_pipeline_workflows} "
        f"gdrive_retry={state.gdrive_retry_pending}"
    )
    return True


def _run_dry_job() -> bool:
    """L3: 실제 IMAP 없이 게이트+락+상태 기록 경로 (temp dir, pipeline mock)."""
    import tempfile

    from data_pc_runtime.layer1_state import RuntimePaths
    from data_pc_runtime.layer3_job import JobConfig, JobRunner

    def _noop():
        class R:
            workflow_count = 0
            gdrive_retry_needed = False

        return R()

    with tempfile.TemporaryDirectory() as tmp:
        paths = RuntimePaths(tmp, storage_subdir="KCH")
        os.makedirs(paths.storage_dir, exist_ok=True)
        gate = GateConfig(skip_wifi_check=True, cooldown_sec=0)
        runner = JobRunner(paths, _noop)
        result = runner.run_once(JobConfig(gate=gate, reason="verify-dry-job"))
        print(f"[dry-job] ran={result.ran} code={result.status_code} msg={result.message}")
        if not result.ran or result.status_code != "pipeline_done":
            print("[FAIL] dry job expected ran=True pipeline_done")
            return False
    return True


def _run_dry_supervisor() -> bool:
    """L4: supervisor 1 tick, boot skip, mock pipeline."""
    from data_pc_runtime.layer1_state import RuntimePaths
    from data_pc_runtime.layer3_job import JobRunner
    from data_pc_runtime.layer4_supervisor import Supervisor, SupervisorConfig

    calls = {"n": 0}

    def _noop():
        calls["n"] += 1

        class R:
            workflow_count = 0
            gdrive_retry_needed = False

        return R()

    with tempfile.TemporaryDirectory() as tmp:
        paths = RuntimePaths(tmp, storage_subdir="KCH")
        os.makedirs(paths.storage_dir, exist_ok=True)
        gate = GateConfig(skip_wifi_check=True, cooldown_sec=0)
        job = JobRunner(paths, _noop)
        sup = Supervisor(
            tmp,
            job=job,
            sup_cfg=SupervisorConfig(boot_mail_check=False),
            gate=gate,
        )
        sup.run_once_tick()
    if calls["n"] != 1:
        print(f"[FAIL] dry-supervisor expected 1 job call, got {calls['n']}")
        return False
    print("[dry-supervisor] 1 tick, 1 job call OK")
    return True


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="data_pc_runtime L0~L2 검증")
    parser.add_argument(
        "--live",
        action="store_true",
        help="단위 테스트 후 이 PC에서 Wi-Fi/G: 프로브 (읽기만)",
    )
    parser.add_argument(
        "--dry-job",
        action="store_true",
        help="L3 Job 게이트 경로 dry-run (IMAP 미실행, skip_wifi)",
    )
    parser.add_argument(
        "--dry-supervisor",
        action="store_true",
        help="L4 supervisor 1 tick (mock pipeline)",
    )
    args = parser.parse_args(argv)

    print("=== data_pc_runtime verify: unit tests ===")
    if not _run_unit_tests():
        print("\n[FAIL] unit tests failed - do not proceed to next layer")
        return 1
    print("\n[OK] unit tests passed")

    if args.live:
        print("\n=== data_pc_runtime verify: live probes ===")
        try:
            _run_live_probes()
        except Exception as exc:
            print(f"\n[FAIL] live probe error: {exc}")
            return 1
        print("\n[OK] live probe done (informational only)")

    if args.dry_job:
        print("\n=== data_pc_runtime verify: dry job (L3) ===")
        try:
            _run_dry_job()
        except Exception as exc:
            print(f"\n[FAIL] dry job error: {exc}")
            return 1
        print("\n[OK] dry job path exercised")

    if args.dry_supervisor:
        print("\n=== data_pc_runtime verify: dry supervisor (L4) ===")
        from data_pc_runtime.layer1_state import RuntimePaths

        try:
            if not _run_dry_supervisor():
                return 1
        except Exception as exc:
            print(f"\n[FAIL] dry supervisor error: {exc}")
            return 1
        print("\n[OK] dry supervisor path exercised")

    print("\n[PASS] verification complete - safe to start next layer")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
