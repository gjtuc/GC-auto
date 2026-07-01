# -*- coding: utf-8 -*-
"""L3 Job runner tests."""
from __future__ import annotations

import os
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PARENT = os.path.dirname(ROOT)
if PARENT not in sys.path:
    sys.path.insert(0, PARENT)

from data_pc_runtime.layer1_state import RuntimePaths, StateStore  # noqa: E402
from data_pc_runtime.layer2_gates import GateAction, GateConfig, GateEvaluator  # noqa: E402
from data_pc_runtime.layer3_job import (  # noqa: E402
    JobConfig,
    JobRunner,
    JobResult,
    _parse_pipeline_result,
)


class TestL3Parse(unittest.TestCase):
    def test_named_tuple(self):
        class R:
            workflow_count = 3
            gdrive_retry_needed = True

        self.assertEqual(_parse_pipeline_result(R()), (3, True))


class TestL3JobRunner(unittest.TestCase):
    def _paths(self, tmp: str) -> RuntimePaths:
        paths = RuntimePaths(tmp, storage_subdir="KCH")
        os.makedirs(paths.storage_dir, exist_ok=True)
        return paths

    def test_gate_wait_skips_pipeline(self):
        with tempfile.TemporaryDirectory() as tmp:
            paths = self._paths(tmp)
            calls = []

            def pipe():
                calls.append(1)
                return type("R", (), {"workflow_count": 1, "gdrive_retry_needed": False})()

            with patch.object(
                GateEvaluator,
                "evaluate",
                return_value=type(
                    "V",
                    (),
                    {
                        "action": GateAction.WAIT,
                        "status_code": "cooldown",
                        "message": "wait",
                        "wifi_ssid": "iptime",
                        "wifi_ready": True,
                        "cooldown_remaining_sec": 100,
                        "detail": "",
                    },
                )(),
            ):
                runner = JobRunner(paths, pipe)
                result = runner.run_once(JobConfig(gate=GateConfig(skip_wifi_check=True)))
            self.assertFalse(result.ran)
            self.assertEqual(len(calls), 0)

    def test_success_marks_state(self):
        with tempfile.TemporaryDirectory() as tmp:
            paths = self._paths(tmp)
            store = StateStore(paths)

            def pipe():
                return type("R", (), {"workflow_count": 2, "gdrive_retry_needed": False})()

            with patch.object(GateEvaluator, "evaluate") as ev:
                ev.return_value = type(
                    "V",
                    (),
                    {
                        "action": GateAction.RUN,
                        "status_code": "ready",
                        "message": "go",
                        "wifi_ssid": "iptime",
                        "wifi_ready": True,
                        "cooldown_remaining_sec": 0,
                        "detail": "",
                    },
                )()
                runner = JobRunner(paths, pipe, store=store)
                result = runner.run_once(JobConfig(gate=GateConfig(skip_wifi_check=True)))

            self.assertTrue(result.ran)
            self.assertEqual(result.workflow_count, 2)
            state = store.load_state()
            self.assertEqual(state.last_pipeline_workflows, 2)
            self.assertFalse(state.gdrive_retry_pending)

    def test_gdrive_retry_state(self):
        with tempfile.TemporaryDirectory() as tmp:
            paths = self._paths(tmp)
            store = StateStore(paths)

            def pipe():
                return type("R", (), {"workflow_count": 0, "gdrive_retry_needed": True})()

            with patch.object(GateEvaluator, "evaluate") as ev:
                ev.return_value = type(
                    "V",
                    (),
                    {
                        "action": GateAction.RUN,
                        "status_code": "ready",
                        "message": "go",
                        "wifi_ssid": None,
                        "wifi_ready": True,
                        "cooldown_remaining_sec": 0,
                        "detail": "",
                    },
                )()
                runner = JobRunner(paths, pipe, store=store)
                result = runner.run_once(JobConfig(gate=GateConfig(skip_wifi_check=True)))

            self.assertTrue(result.gdrive_retry)
            state = store.load_state()
            self.assertTrue(state.gdrive_retry_pending)

    def test_lock_prevents_double_run(self):
        with tempfile.TemporaryDirectory() as tmp:
            paths = self._paths(tmp)
            with open(paths.pipeline_lock, "w", encoding="ascii") as f:
                f.write(str(os.getpid()))

            calls = []

            def pipe():
                calls.append(1)
                return type("R", (), {"workflow_count": 1, "gdrive_retry_needed": False})()

            with patch.object(GateEvaluator, "evaluate") as ev:
                ev.return_value = type(
                    "V",
                    (),
                    {
                        "action": GateAction.RUN,
                        "status_code": "ready",
                        "message": "go",
                        "wifi_ssid": None,
                        "wifi_ready": True,
                        "cooldown_remaining_sec": 0,
                        "detail": "",
                    },
                )()
                runner = JobRunner(paths, pipe)
                result = runner.run_once(JobConfig(gate=GateConfig(skip_wifi_check=True)))

            self.assertFalse(result.ran)
            self.assertEqual(result.status_code, "processing")
            self.assertEqual(len(calls), 0)


if __name__ == "__main__":
    unittest.main()
