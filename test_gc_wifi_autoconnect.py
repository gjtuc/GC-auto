# -*- coding: utf-8 -*-
"""gc_wifi_autoconnect 단위 테스트 (netsh mock)."""
from __future__ import annotations

import os
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import gc_wifi_autoconnect as wac


class TestGcWifiAutoconnect(unittest.TestCase):
    def test_connect_order_prefers_5g(self) -> None:
        order = wac._connect_order(("iptime", "iptime_5G", "iptime 2"))
        self.assertEqual(order[0], "iptime_5G")

    def test_profile_xml_escapes_ssid(self) -> None:
        xml = wac._profile_xml("iptime 2", "12121212")
        self.assertIn("<name>iptime 2</name>", xml)
        self.assertIn("12121212", xml)
        self.assertIn("connectionMode>auto", xml)

    @patch.dict(os.environ, {"REQUIRED_HOTSPOT": "iptime,iptime_5G", "IPTIME_WIFI_PSK": "12121212"}, clear=False)
    def test_load_config_from_env(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            ssids, psk = wac._load_config(tmp)
        self.assertIn("iptime", ssids)
        self.assertEqual(psk, "12121212")

    @patch.object(wac, "_connected_ssid", return_value="iptime_5G")
    def test_already_connected(self, _mock: object) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            self.assertTrue(wac.ensure_wifi_connected(tmp))

    @patch.object(wac, "_try_connect", return_value=True)
    @patch.object(wac, "_saved_profiles", return_value={"iptime_5G"})
    @patch.object(wac, "_connected_ssid", return_value=None)
    @patch.object(wac, "_disable_wifi_power_save")
    @patch.object(wac, "_enable_wifi_interface")
    @patch.object(wac, "_ensure_profiles")
    def test_connects_when_profile_exists(
        self,
        _ensure: object,
        _enable: object,
        _power: object,
        _ssid: object,
        _profiles: object,
        _connect: object,
    ) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            self.assertTrue(wac.ensure_wifi_connected(tmp))
        _connect.assert_called()


if __name__ == "__main__":
    unittest.main()
