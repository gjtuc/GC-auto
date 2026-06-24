# -*- coding: utf-8 -*-
"""data_pc_watch 단위 검증 — Wi-Fi poll·1시간 쿨다운·파이프라인 콜백."""
import os
import sys
import tempfile
import time
import unittest
from datetime import datetime
from unittest.mock import patch

REPO = os.path.dirname(os.path.abspath(__file__))
DATA_PC = os.path.join(REPO, "data_pc")
if DATA_PC not in sys.path:
    sys.path.insert(0, DATA_PC)

from data_pc_watch import (  # noqa: E402
    DataPcWatchRunner,
    _read_last_pipeline_epoch,
    _save_last_pipeline,
    _state_json_path,
    load_watch_config,
)


class TestDataPcWatch(unittest.TestCase):
    def test_load_watch_config_defaults(self):
        with tempfile.TemporaryDirectory() as tmp:
            cfg = load_watch_config(tmp)
            self.assertIn("iptime", cfg["required_ssid"])
            self.assertEqual(cfg["cooldown_sec"], 3600)
            self.assertEqual(cfg["cooldown_hours"], 1)
            self.assertEqual(cfg["interval_sec"], 15)

    def test_load_watch_config_from_env_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            env = os.path.join(tmp, "gc_automation.env")
            with open(env, "w", encoding="utf-8") as f:
                f.write("REQUIRED_HOTSPOT=iPhone\n")
                f.write("DATA_PC_AUTO_MAIL_COOLDOWN_HOURS=2\n")
            cfg = load_watch_config(tmp)
            self.assertEqual(cfg["required_ssid"], "iPhone")
            self.assertEqual(cfg["cooldown_sec"], 7200)

    def test_cooldown_blocks_second_pipeline(self):
        calls = []

        def fake_process():
            calls.append(time.time())
            return 0

        with tempfile.TemporaryDirectory() as tmp:
            state = _state_json_path(tmp)
            _save_last_pipeline(state)
            config = {
                "required_ssid": "iptime",
                "cooldown_sec": 3600,
                "cooldown_hours": 1,
                "interval_sec": 1,
                "reconnect_min_sec": 90,
                "skip_wifi_check": True,
                "status_json": os.path.join(tmp, "status.json"),
                "state_json": state,
            }
            runner = DataPcWatchRunner(tmp, config, fake_process)
            with patch.object(runner, "_is_connected", return_value=True):
                with patch.object(runner, "_get_ssid", return_value="iptime"):
                    with patch.object(runner, "_wait_reason", return_value=""):
                        runner._tick()
            self.assertEqual(len(calls), 0)
            self.assertGreater(runner._cooldown_remaining(), 3500)

    def test_wifi_connected_runs_pipeline_when_cooldown_clear(self):
        calls = []

        def fake_process():
            calls.append(1)
            return 0

        with tempfile.TemporaryDirectory() as tmp:
            config = {
                "required_ssid": "iptime",
                "cooldown_sec": 0,
                "cooldown_hours": 0,
                "interval_sec": 1,
                "reconnect_min_sec": 90,
                "skip_wifi_check": True,
                "status_json": os.path.join(tmp, "status.json"),
                "state_json": _state_json_path(tmp),
            }
            runner = DataPcWatchRunner(tmp, config, fake_process)
            with patch.object(runner, "_is_connected", return_value=True):
                with patch.object(runner, "_get_ssid", return_value="iptime"):
                    with patch.object(runner, "_wait_reason", return_value=""):
                        runner._tick()
            self.assertEqual(len(calls), 1)

    def test_no_mail_returns_zero_without_exception(self):
        calls = []

        def fake_process():
            calls.append(1)
            return 0

        with tempfile.TemporaryDirectory() as tmp:
            config = {
                "required_ssid": "iptime",
                "cooldown_sec": 0,
                "cooldown_hours": 0,
                "interval_sec": 1,
                "reconnect_min_sec": 90,
                "skip_wifi_check": True,
                "status_json": os.path.join(tmp, "status.json"),
                "state_json": _state_json_path(tmp),
            }
            runner = DataPcWatchRunner(tmp, config, fake_process)
            with patch.object(runner, "_is_connected", return_value=True):
                with patch.object(runner, "_get_ssid", return_value="iptime"):
                    with patch.object(runner, "_wait_reason", return_value=""):
                        runner._run_pipeline("test")
            self.assertEqual(calls, [1])

    def test_state_roundtrip(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = _state_json_path(tmp)
            os.makedirs(os.path.dirname(path), exist_ok=True)
            self.assertIsNone(_read_last_pipeline_epoch(path))
            _save_last_pipeline(path)
            epoch = _read_last_pipeline_epoch(path)
            self.assertIsNotNone(epoch)
            self.assertAlmostEqual(epoch, datetime.now().timestamp(), delta=5)


if __name__ == "__main__":
    unittest.main()
