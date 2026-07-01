# -*- coding: utf-8 -*-
"""T21 — gc1_runtime.layer0_probes (B-HOST) 단위 테스트."""
from __future__ import annotations

import sys
import unittest

from gc1_runtime.layer0_probes import (
    DisplayMetrics,
    HostProbe,
    build_profile_key,
    read_platform,
    read_python_bitness,
)


class TestHostPlatformLeaves(unittest.TestCase):
    def test_read_platform_non_empty(self):
        self.assertTrue(read_platform())
        self.assertEqual(read_platform(), sys.platform)

    def test_python_bitness_allowed_values(self):
        bitness = read_python_bitness()
        self.assertIn(bitness, ("32bit", "64bit"))


class TestDisplayMetrics(unittest.TestCase):
    def test_profile_key_format(self):
        m = DisplayMetrics(width=1920, height=1080, dpi=96)
        self.assertEqual(m.profile_key, "1920x1080@96")
        self.assertEqual(build_profile_key(1920, 1080, 96), "1920x1080@96")

    def test_frozen_dataclass(self):
        m = DisplayMetrics(800, 600, 120)
        with self.assertRaises(AttributeError):
            m.width = 1024  # type: ignore[misc]


class TestHostProbe(unittest.TestCase):
    def test_injected_metrics_reader(self):
        def fake(_hwnd: int | None) -> DisplayMetrics:
            return DisplayMetrics(2560, 1440, 120)

        probe = HostProbe(metrics_reader=fake)
        self.assertEqual(probe.platform(), sys.platform)
        self.assertIn(probe.python_bitness(), ("32bit", "64bit"))
        metrics = probe.display_metrics(hwnd=12345)
        self.assertEqual(metrics.width, 2560)
        self.assertEqual(metrics.height, 1440)
        self.assertEqual(metrics.dpi, 120)
        self.assertEqual(metrics.profile_key, "2560x1440@120")

    def test_display_metrics_without_hwnd_uses_default_dpi_in_fake(self):
        probe = HostProbe(
            metrics_reader=lambda _h: DisplayMetrics(1024, 768, 96),
        )
        m = probe.display_metrics()
        self.assertEqual(m.profile_key, "1024x768@96")

    @unittest.skipUnless(sys.platform == "win32", "win32 live metrics")
    def test_win32_live_display_metrics_positive(self):
        probe = HostProbe()
        m = probe.display_metrics()
        self.assertGreater(m.width, 0)
        self.assertGreater(m.height, 0)
        self.assertGreaterEqual(m.dpi, 96)
        self.assertIn("@", m.profile_key)


if __name__ == "__main__":
    unittest.main()
