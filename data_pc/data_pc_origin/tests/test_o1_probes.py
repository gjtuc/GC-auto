# -*- coding: utf-8 -*-
"""O1 probe 함수 단위 테스트."""

from __future__ import annotations

import os
import tempfile
import unittest
import unittest.mock as mock
from pathlib import Path

from data_pc_origin.o0_types import ProbeResult
from data_pc_origin.o1_opju_path import (
    normalize_g_path,
    probe_g_drive_root_accessible,
    probe_opju_path,
    probe_path_nonempty,
    probe_suffix_opju,
)
from data_pc_origin.o1_opju_writable import probe_opju_writable


class TestO1OpjuPath(unittest.TestCase):
    def test_nonempty(self) -> None:
        self.assertFalse(probe_path_nonempty("").ok)
        self.assertTrue(probe_path_nonempty(r"G:\a.opju").ok)

    def test_suffix(self) -> None:
        self.assertTrue(probe_suffix_opju(r"G:\x.OPJU").ok)
        self.assertFalse(probe_suffix_opju(r"G:\x.opj").ok)

    def test_normalize_g(self) -> None:
        self.assertTrue(normalize_g_path(r"g:\a").startswith("G:"))

    def test_aggregate_empty_fails_p01(self) -> None:
        r = probe_opju_path("")
        self.assertFalse(r.ok)
        self.assertEqual(r.code, "P01")

    def test_g_root_mock(self) -> None:
        with mock.patch("data_pc_origin.o1_opju_path.experiment_data_root", return_value=r"G:\root"):
            with mock.patch("os.path.isdir", return_value=True):
                self.assertTrue(probe_g_drive_root_accessible().ok)


class TestO1Writable(unittest.TestCase):
    def test_writable_temp_file(self) -> None:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".opju") as f:
            path = f.name
        try:
            self.assertTrue(probe_opju_writable(path).ok)
        finally:
            os.remove(path)


if __name__ == "__main__":
    unittest.main()
