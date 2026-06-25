# -*- coding: utf-8 -*-
"""data_pc_runtime L0~L2 단위 테스트."""
from __future__ import annotations

import os
import subprocess
import sys
import tempfile
import time
import unittest
from unittest.mock import MagicMock

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from data_pc_runtime.layer0_probes import (  # noqa: E402
    GDriveProbe,
    WifiProbe,
    WifiProbeKind,
    parse_required_ssids,
)
from data_pc_runtime.layer1_state import RuntimePaths, StateStore  # noqa: E402
from data_pc_runtime.layer2_gates import GateAction, GateConfig, GateEvaluator  # noqa: E402
from data_pc_runtime.layer2_lock import PipelineLock  # noqa: E402


class TestL0Wifi(unittest.TestCase):
    def test_parse_ssids(self):
        self.assertEqual(
            parse_required_ssids("iptime, iptime 2, iptime_5G"),
            ("iptime", "iptime 2", "iptime_5G"),
        )

    def test_connected_ok(self):
        def fake_netsh():
            m = MagicMock()
            m.returncode = 0
            m.stdout = "    SSID                   : iptime\n"
            return m

        probe = WifiProbe(netsh_runner=fake_netsh, max_attempts=1)
        result = probe.check(("iptime",))
        self.assertEqual(result.kind, WifiProbeKind.CONNECTED_OK)
        self.assertTrue(result.ready)

    def test_probe_failed_uses_cache(self):
        calls = {"n": 0}

        def fail_netsh():
            calls["n"] += 1
            raise subprocess.TimeoutExpired(cmd="netsh", timeout=30)

        probe = WifiProbe(netsh_runner=fail_netsh, max_attempts=1, cache_ttl_sec=60)
        probe._cache_at = time.time()
        probe._cache_ssid = "iptime"
        result = probe.check(("iptime",))
        self.assertEqual(result.kind, WifiProbeKind.CONNECTED_OK)
        self.assertEqual(result.ssid, "iptime")
        self.assertIn("cache", result.detail)


class TestL1State(unittest.TestCase):
    def test_atomic_save_and_cooldown(self):
        with tempfile.TemporaryDirectory() as tmp:
            paths = RuntimePaths(tmp, storage_subdir="KCH")
            os.makedirs(paths.storage_dir)
            store = StateStore(paths)
            store.mark_pipeline_finished(workflow_count=2, gdrive_retry=False)
            rem = store.cooldown_remaining_sec(
                cooldown_sec=3600,
                gdrive_retry_sec=900,
                gdrive_available=True,
            )
            self.assertGreater(rem, 3500)

    def test_zero_workflow_no_cooldown(self):
        with tempfile.TemporaryDirectory() as tmp:
            paths = RuntimePaths(tmp, storage_subdir="KCH")
            os.makedirs(paths.storage_dir)
            store = StateStore(paths)
            store.mark_pipeline_finished(workflow_count=0, gdrive_retry=False)
            rem = store.cooldown_remaining_sec(
                cooldown_sec=3600,
                gdrive_retry_sec=900,
                gdrive_available=True,
            )
            self.assertEqual(rem, 0)

    def test_gdrive_retry_bypasses_cooldown_when_available(self):
        with tempfile.TemporaryDirectory() as tmp:
            paths = RuntimePaths(tmp, storage_subdir="KCH")
            os.makedirs(paths.storage_dir)
            store = StateStore(paths)
            store.mark_pipeline_finished(workflow_count=0, gdrive_retry=True)
            rem = store.cooldown_remaining_sec(
                cooldown_sec=3600,
                gdrive_retry_sec=900,
                gdrive_available=True,
            )
            self.assertEqual(rem, 0)


class TestL2Gates(unittest.TestCase):
    def test_wifi_blocks(self):
        with tempfile.TemporaryDirectory() as tmp:
            paths = RuntimePaths(tmp, storage_subdir="KCH")
            os.makedirs(paths.storage_dir)
            wifi = WifiProbe(
                netsh_runner=lambda: (_ for _ in ()).throw(
                    subprocess.TimeoutExpired(cmd="netsh", timeout=30)
                ),
                max_attempts=1,
            )
            ev = GateEvaluator(paths, wifi=wifi)
            v = ev.evaluate(GateConfig())
            self.assertEqual(v.action, GateAction.WAIT)
            self.assertEqual(v.status_code, "wifi_probe_failed")

    def test_ready_when_skip_wifi(self):
        with tempfile.TemporaryDirectory() as tmp:
            paths = RuntimePaths(tmp, storage_subdir="KCH")
            os.makedirs(paths.storage_dir)
            ev = GateEvaluator(paths, gdrive=GDriveProbe(root=tmp))
            v = ev.evaluate(GateConfig(skip_wifi_check=True))
            self.assertEqual(v.action, GateAction.RUN)
            self.assertEqual(v.status_code, "ready")


class TestL2Lock(unittest.TestCase):
    def test_exclusive_lock(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "t.lock")
            a = PipelineLock(path)
            b = PipelineLock(path)
            self.assertTrue(a.try_acquire())
            self.assertFalse(b.try_acquire())
            a.release()
            self.assertTrue(b.try_acquire())
            b.release()


if __name__ == "__main__":
    unittest.main()
