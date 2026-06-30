# -*- coding: utf-8 -*-
"""
T83 — ``gc3_screen_read.py`` 스켈레톤 검증.

정적 검증: JSON 스키마·box 해석·import
실행 검증: ``--dry-run`` CLI·``read_region`` mock 텍스트·subprocess ``--help``

실행:
  python -m py_compile gc3_screen_read.py test_gc3_screen_read.py
  python -m unittest test_gc3_screen_read -v
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import unittest
from unittest import mock

REPO = os.path.dirname(os.path.abspath(__file__))
CONFIG_PATH = os.path.join(REPO, "deploy", "screen_regions.gc3.json")
MODULE_PATH = os.path.join(REPO, "gc3_screen_read.py")

import gc3_screen_read as g3  # noqa: E402 — repo 루트


class TestGc3ScreenReadStatic(unittest.TestCase):
    """정적 검증 — 설정·좌표 해석 (캡처·OCR 미실행)."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.config = g3.load_config(CONFIG_PATH)

    def test_config_json_valid(self):
        with open(CONFIG_PATH, encoding="utf-8") as fh:
            raw = json.load(fh)
        self.assertIn("chem32_status_bar", raw["regions"])
        self.assertEqual(raw["window_title_contains"], "ChemStation")

    def test_list_region_ids_sorted(self):
        ids = g3.list_region_ids(self.config)
        self.assertEqual(ids, sorted(ids))
        self.assertGreaterEqual(len(ids), 2)

    def test_resolve_status_bar_inside_window(self):
        win = g3.Box(100, 50, 800, 600)
        box, scale = g3.resolve_region_box(self.config, "chem32_status_bar", win)
        self.assertEqual(scale, 2.0)
        self.assertGreater(box.top, win.top)
        self.assertLess(box.bottom, win.bottom + 1)
        self.assertEqual(box.left, win.left)
        self.assertEqual(box.width, win.width)

    def test_default_config_path_exists(self):
        self.assertTrue(os.path.isfile(g3.DEFAULT_CONFIG))


class TestGc3ScreenReadExecution(unittest.TestCase):
    """실행 검증 — dry-run 경로 (Chem32·Tesseract 불필요)."""

    def test_read_region_dry_run_text(self):
        config = g3.load_config(CONFIG_PATH)
        result = g3.read_region(config, "chem32_status_bar", dry_run=True)
        self.assertTrue(result.dry_run)
        self.assertIn("Idle", result.plain_text)
        self.assertIsNotNone(result.region_box)
        self.assertEqual(result.method, "ocr")

    def test_main_list_dry_run(self):
        rc = g3.main(["--dry-run", "--config", CONFIG_PATH, "list"])
        self.assertEqual(rc, 0)

    def test_main_read_dry_run(self):
        rc = g3.main(
            [
                "--dry-run",
                "--config",
                CONFIG_PATH,
                "read",
                "--region",
                "chem32_status_bar",
            ]
        )
        self.assertEqual(rc, 0)

    def test_main_probe_dry_run_all_ok(self):
        rc = g3.main(["--dry-run", "--config", CONFIG_PATH, "probe"])
        self.assertEqual(rc, 0)

    def test_cli_help_subprocess(self):
        proc = subprocess.run(
            [sys.executable, MODULE_PATH, "read", "--help"],
            cwd=REPO,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=30,
        )
        self.assertEqual(proc.returncode, 0)
        self.assertIn("--region", proc.stdout)

    def test_live_read_without_window_raises(self):
        config = g3.load_config(CONFIG_PATH)
        with mock.patch.object(g3, "find_chem32_window_box", return_value=None):
            with self.assertRaises(RuntimeError) as ctx:
                g3.read_region(config, "chem32_status_bar", dry_run=False)
        self.assertIn("Chem32", str(ctx.exception))


if __name__ == "__main__":
    unittest.main()
