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

from data_pc_runtime.layer1_state import RuntimePaths, RuntimeStatus, StateStore  # noqa: E402
from data_pc_runtime.layer2_gates import GateConfig  # noqa: E402
from data_pc_runtime.layer3_job import JobConfig, JobResult, JobRunner  # noqa: E402
from data_pc_runtime.layer4_supervisor import (  # noqa: E402
    Supervisor,
    SupervisorConfig,
    ensure_supervisor_once,
    is_supervisor_healthy,
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
            job = JobRunner(paths, pipe, store=StateStore(paths))
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
                    "data_pc_runtime.layer4_supervisor.spawn_supervisor",
                    return_value=True,
                ) as sp:
                    started = ensure_supervisor_once(tmp)
            self.assertTrue(started)
            sp.assert_called_once()


if __name__ == "__main__":
    unittest.main()
