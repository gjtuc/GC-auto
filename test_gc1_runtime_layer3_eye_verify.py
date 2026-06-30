# -*- coding: utf-8 -*-
"""layer3_eye — loose tab / raw verify."""
from __future__ import annotations

import unittest

from gc1_runtime.layer3_eye import verify_loose_tab, verify_raw_in_text


class TestLooseTabVerify(unittest.TestCase):
    def test_analysis_full(self):
        self.assertTrue(verify_loose_tab("분석목록", "analysis"))

    def test_analysis_split(self):
        self.assertTrue(verify_loose_tab("분석\n목록 탭", "analysis"))

    def test_control_split(self):
        self.assertTrue(verify_loose_tab("제어 목록", "control"))

    def test_fail_garbage(self):
        self.assertFalse(verify_loose_tab("| AGES", "analysis"))


class TestRawVerify(unittest.TestCase):
    def test_dot_raw(self):
        self.assertTrue(verify_raw_in_text("행 1.raw 파일"))

    def test_compact_raw(self):
        self.assertTrue(verify_raw_in_text("2raw"))


if __name__ == "__main__":
    unittest.main()
