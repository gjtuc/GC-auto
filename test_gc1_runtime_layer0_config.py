# -*- coding: utf-8 -*-
"""T22 — gc1_runtime.layer0_config (B-CFG) 단위 테스트."""
from __future__ import annotations

import os
import tempfile
import unittest

from gc1_runtime.layer0_config import (
    ConfigReader,
    parse_bool,
    parse_frac,
    parse_hotspot_csv,
    parse_int_nonneg,
    parse_optional_file,
    read_analysis_method_dir,
    read_autochro_enabled,
    read_gc1_use_runtime,
    read_hancom_wait_sec,
    read_list_neutral_x_frac,
    read_required_hotspot,
    read_window_title_pattern,
)


class TestCfgParsers(unittest.TestCase):
    def test_parse_bool_invalid_falls_back(self):
        self.assertTrue(parse_bool("yes", False))
        self.assertFalse(parse_bool("no", True))
        self.assertTrue(parse_bool("maybe", True))  # invalid → default

    def test_parse_int_nonneg_invalid(self):
        self.assertEqual(parse_int_nonneg("120", 60), 120)
        self.assertEqual(parse_int_nonneg("-5", 60), 60)
        self.assertEqual(parse_int_nonneg("x", 60), 60)

    def test_parse_frac_bounds(self):
        self.assertAlmostEqual(parse_frac("0.78", 0.5), 0.78)
        self.assertAlmostEqual(parse_frac("1.5", 0.88), 0.88)
        self.assertAlmostEqual(parse_frac("0", 0.88), 0.88)

    def test_parse_hotspot_csv(self):
        self.assertEqual(parse_hotspot_csv("iPhone, iPad", "x"), ("iPhone", "iPad"))
        self.assertEqual(parse_hotspot_csv("", "iPhone"), ("iPhone",))


class TestCfgReadLeaves(unittest.TestCase):
    def test_defaults_when_empty_env(self):
        env: dict[str, str] = {}
        self.assertFalse(read_autochro_enabled(env))
        self.assertEqual(read_window_title_pattern(env), "Autochro")
        self.assertFalse(read_gc1_use_runtime(env))
        self.assertEqual(read_hancom_wait_sec(env), 120)
        self.assertAlmostEqual(read_list_neutral_x_frac(env), 0.88)
        self.assertEqual(read_required_hotspot(env), ("iPhone",))

    def test_trim_and_bool_true(self):
        env = {
            "AUTOCHRO_ENABLED": "  true  ",
            "GC1_USE_RUNTIME": "1",
        }
        self.assertTrue(read_autochro_enabled(env))
        self.assertTrue(read_gc1_use_runtime(env))

    def test_invalid_int_fallback(self):
        env = {"AUTOCHRO_HANCOM_WAIT_SEC": "not-a-number"}
        self.assertEqual(read_hancom_wait_sec(env), 120)

    def test_invalid_frac_fallback(self):
        env = {"AUTOCHRO_LIST_NEUTRAL_X_FRAC": "2.0"}
        self.assertAlmostEqual(read_list_neutral_x_frac(env), 0.88)

    def test_analysis_method_dir_existing(self):
        with tempfile.TemporaryDirectory() as tmp:
            env = {"AUTOCHRO_ANALYSIS_METHOD_DIR": tmp}
            self.assertEqual(read_analysis_method_dir(env), os.path.normpath(tmp))

    def test_analysis_method_dir_invalid_falls_back_desktop(self):
        env = {"AUTOCHRO_ANALYSIS_METHOD_DIR": r"Z:\no_such_dir_abc123"}
        got = read_analysis_method_dir(env)
        self.assertTrue(os.path.isdir(got))

    def test_optional_crm_missing_file(self):
        from gc1_runtime.layer0_config import read_crm_path

        env = {"AUTOCHRO_CRM_PATH": r"Z:\missing.crm"}
        self.assertEqual(read_crm_path(env), "")

    def test_optional_crm_existing_file(self):
        from gc1_runtime.layer0_config import read_crm_path

        with tempfile.NamedTemporaryFile(suffix=".crm", delete=False) as fh:
            path = fh.name
        try:
            env = {"AUTOCHRO_CRM_PATH": path}
            self.assertEqual(read_crm_path(env), os.path.normpath(path))
        finally:
            os.unlink(path)


class TestConfigReader(unittest.TestCase):
    def test_load_snapshot_fields(self):
        with tempfile.TemporaryDirectory() as tmp:
            cfg = ConfigReader().load(
                {
                    "AUTOCHRO_ENABLED": "1",
                    "AUTOCHRO_WINDOW_TITLE_PATTERN": "Autochro-3000",
                    "AUTOCHRO_ANALYSIS_METHOD_DIR": tmp,
                    "REQUIRED_HOTSPOT": "iPhone,MyHotspot",
                }
            )
            self.assertTrue(cfg.autochro_enabled)
            self.assertEqual(cfg.window_title_pattern, "Autochro-3000")
            self.assertEqual(cfg.analysis_method_dir, os.path.normpath(tmp))
            self.assertEqual(cfg.required_hotspot, ("iPhone", "MyHotspot"))
            self.assertFalse(cfg.gc1_use_runtime)


if __name__ == "__main__":
    unittest.main()
