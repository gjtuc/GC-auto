# -*- coding: utf-8 -*-
"""data_pc_watch 단위 검증 — 핫스팟 edge·delay·파이프라인 콜백."""
import os
import sys
import tempfile
import time
import unittest
from unittest.mock import patch

REPO = os.path.dirname(os.path.abspath(__file__))
DATA_PC = os.path.join(REPO, "data_pc")
if DATA_PC not in sys.path:
    sys.path.insert(0, DATA_PC)

from data_pc_watch import DataPcWatchRunner, load_watch_config  # noqa: E402


class TestDataPcWatch(unittest.TestCase):
    def test_load_watch_config_defaults(self):
        with tempfile.TemporaryDirectory() as tmp:
            cfg = load_watch_config(tmp)
            self.assertEqual(cfg["required_ssid"], "iPhone")
            self.assertEqual(cfg["delay_sec"], 300)
            self.assertEqual(cfg["interval_sec"], 15)

    def test_hotspot_edge_triggers_pipeline_after_delay(self):
        calls = []

        def fake_process():
            calls.append(time.time())
            return 1

        config = {
            "required_ssid": "iPhone",
            "delay_sec": 1,
            "interval_sec": 1,
            "reconnect_min_sec": 90,
            "skip_wifi_check": True,
            "status_json": os.path.join(tempfile.gettempdir(), "test_watch_status.json"),
        }
        runner = DataPcWatchRunner("/tmp", config, fake_process)

        with patch.object(runner, "_is_connected", return_value=True):
            with patch.object(runner, "_get_ssid", return_value="iPhone"):
                with patch.object(runner, "_wait_reason", return_value=""):
                    runner._tick()
                    self.assertIsNotNone(runner._run_after_mono)
                    self.assertFalse(runner._session_processed)
                    time.sleep(1.1)
                    runner._tick()
                    self.assertEqual(len(calls), 1)
                    self.assertTrue(runner._session_processed)


if __name__ == "__main__":
    unittest.main()
