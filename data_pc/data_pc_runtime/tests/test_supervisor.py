# -*- coding: utf-8 -*-
"""L4 Supervisor tests."""
from __future__ import annotations

import os
import sys
import tempfile
import time
import unittest
from datetime import datetime
from unittest.mock import patch

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PARENT = os.path.dirname(ROOT)
if PARENT not in sys.path:
    sys.path.insert(0, PARENT)

from data_pc_runtime.layer0_probes import GDriveProbe  # noqa: E402
from data_pc_runtime.layer1_state import RuntimePaths, RuntimeStatus, StateStore  # noqa: E402
from data_pc_runtime.layer2_gates import GateConfig, GateEvaluator  # noqa: E402
from data_pc_runtime.layer3_job import JobConfig, JobResult, JobRunner  # noqa: E402
from data_pc_runtime.layer4_supervisor import (  # noqa: E402
    Supervisor,
    SupervisorConfig,
    ensure_supervisor_once,
    is_supervisor_healthy,
    restart_supervisor,
    stop_supervisor,
)


class TestL4Health(unittest.TestCase):
    def _fresh_status(self, paths: RuntimePaths, store: StateStore) -> None:
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        store.save_status(
            RuntimeStatus(
                alive=True,
                status_code="starting",
                message="ok",
                pid=os.getpid(),
                last_heartbeat=now,
                updated_at=now,
            )
        )

    def test_healthy_when_fresh(self):
        with tempfile.TemporaryDirectory() as tmp:
            paths = RuntimePaths(tmp, "KCH")
            os.makedirs(paths.storage_dir)
            store = StateStore(paths)
            self._fresh_status(paths, store)
            self.assertTrue(is_supervisor_healthy(paths, stale_sec=180))

    def test_unhealthy_when_stale(self):
        with tempfile.TemporaryDirectory() as tmp:
            paths = RuntimePaths(tmp, "KCH")
            os.makedirs(paths.storage_dir)
            store = StateStore(paths)
            store.save_status(
                RuntimeStatus(
                    alive=True,
                    pid=os.getpid(),
                    last_heartbeat="2020-01-01 00:00:00",
                )
            )
            self.assertFalse(is_supervisor_healthy(paths, stale_sec=180))


class TestL4Supervisor(unittest.TestCase):
    def test_run_once_tick_calls_job(self):
        with tempfile.TemporaryDirectory() as tmp:
            paths = RuntimePaths(tmp, "KCH")
            os.makedirs(paths.storage_dir)
            calls = []

            def pipe():
                calls.append(1)
                return type("R", (), {"workflow_count": 0, "gdrive_retry_needed": False})()

            gate = GateConfig(skip_wifi_check=True, cooldown_sec=0)
            store = StateStore(paths)
            evaluator = GateEvaluator(paths, gdrive=GDriveProbe(root=tmp), store=store)
            job = JobRunner(paths, pipe, store=store, evaluator=evaluator)
            sup = Supervisor(
                tmp,
                pipeline=pipe,
                job=job,
                sup_cfg=SupervisorConfig(boot_mail_check=False, poll_sec=1),
                gate=gate,
            )
            sup.run_once_tick()
            self.assertEqual(len(calls), 1)

    def test_ensure_skips_when_healthy(self):
        with tempfile.TemporaryDirectory() as tmp:
            paths = RuntimePaths(tmp, "KCH")
            os.makedirs(paths.storage_dir)
            now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            StateStore(paths).save_status(
                RuntimeStatus(alive=True, pid=os.getpid(), last_heartbeat=now)
            )
            with patch("data_pc_runtime.layer4_supervisor.spawn_supervisor") as sp:
                started = ensure_supervisor_once(tmp)
            self.assertFalse(started)
            sp.assert_not_called()

    def test_ensure_spawns_when_stale(self):
        with tempfile.TemporaryDirectory() as tmp:
            with patch(
                "data_pc_runtime.layer4_supervisor.is_supervisor_healthy",
                return_value=False,
            ):
                with patch(
                    "data_pc_runtime.layer4_supervisor._is_stale_supervisor",
                    return_value=False,
                ):
                    with patch(
                        "data_pc_runtime.layer4_supervisor.spawn_supervisor",
                        return_value=True,
                    ) as sp:
                        started = ensure_supervisor_once(tmp)
            self.assertTrue(started)
            sp.assert_called_once()

    def test_ensure_stops_stale_before_spawn(self):
        with tempfile.TemporaryDirectory() as tmp:
            paths = RuntimePaths(tmp, "KCH")
            os.makedirs(paths.storage_dir)
            StateStore(paths).save_status(
                RuntimeStatus(
                    alive=True,
                    pid=os.getpid(),
                    last_heartbeat="2020-01-01 00:00:00",
                )
            )
            with patch(
                "data_pc_runtime.layer4_supervisor.is_supervisor_healthy",
                return_value=False,
            ):
                with patch(
                    "data_pc_runtime.layer4_supervisor.stop_supervisor",
                    return_value=True,
                ) as stop:
                    with patch(
                        "data_pc_runtime.layer4_supervisor.spawn_supervisor",
                        return_value=True,
                    ) as spawn:
                        started = ensure_supervisor_once(tmp)
            self.assertTrue(started)
            stop.assert_called_once_with(tmp)
            spawn.assert_called_once_with(tmp)

    def test_ensure_recovery_cap_skips_spawn(self):
        with tempfile.TemporaryDirectory() as tmp:
            paths = RuntimePaths(tmp, "KCH")
            os.makedirs(paths.storage_dir)
            cfg = SupervisorConfig(
                ensure_max_recoveries=2,
                ensure_recovery_window_sec=900,
            )
            now = time.time()
            with patch(
                "data_pc_runtime.layer4_supervisor.load_supervisor_config",
                return_value=cfg,
            ):
                with patch(
                    "data_pc_runtime.layer4_supervisor.is_supervisor_healthy",
                    return_value=False,
                ):
                    with patch(
                        "data_pc_runtime.layer4_supervisor._load_ensure_recovery_times",
                        return_value=[now - 60, now - 30],
                    ):
                        with patch(
                            "data_pc_runtime.layer4_supervisor.spawn_supervisor",
                        ) as spawn:
                            started = ensure_supervisor_once(tmp)
            self.assertFalse(started)
            spawn.assert_not_called()

    def test_restart_stops_then_spawns(self):
        with tempfile.TemporaryDirectory() as tmp:
            with patch(
                "data_pc_runtime.layer4_supervisor.stop_supervisor",
                return_value=True,
            ) as stop:
                with patch(
                    "data_pc_runtime.layer4_supervisor.spawn_supervisor",
                    return_value=True,
                ) as spawn:
                    ok = restart_supervisor(tmp)
            self.assertTrue(ok)
            stop.assert_called_once_with(tmp)
            spawn.assert_called_once_with(tmp)

    def test_ensure_skips_when_watch_disabled(self):
        with tempfile.TemporaryDirectory() as tmp:
            paths = RuntimePaths(tmp, "KCH")
            os.makedirs(paths.storage_dir)
            with patch(
                "data_pc_runtime.layer4_supervisor.is_watch_enabled",
                return_value=False,
            ):
                with patch(
                    "data_pc_runtime.layer4_supervisor.spawn_supervisor",
                ) as spawn:
                    started = ensure_supervisor_once(tmp)
            self.assertFalse(started)
            spawn.assert_not_called()
            status = StateStore(paths).load_status()
            self.assertEqual(status.status_code, "manual_only")
            self.assertFalse(status.alive)


if __name__ == "__main__":
    unittest.main()
