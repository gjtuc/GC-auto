# -*- coding: utf-8 -*-
"""workflow gate + OCR learn merge."""
from __future__ import annotations

import json
import os
import tempfile
import unittest
from pathlib import Path

from gc1_runtime.layer3_ocr_learn import (
    _apply_report_to_overlay,
    merge_config_with_learnings,
)
from gc1_runtime.layer3_workflow_gate import (
    classify_failure,
    user_question_if_needed,
)


class TestWorkflowGate(unittest.TestCase):
    def test_ocr_ui_class(self):
        self.assertEqual(classify_failure("OCR gate fail: P1 / eye_active_tab"), "ocr_ui")

    def test_workflow_ask_mtd(self):
        self.assertEqual(classify_failure("분석방법.MTD 파일 없음"), "workflow_ask")
        self.assertIsNotNone(user_question_if_needed("분석방법.MTD 파일 없음"))

    def test_ocr_no_user_question(self):
        self.assertIsNone(user_question_if_needed("sync anchor .raw not found"))


class TestLearnMerge(unittest.TestCase):
    def test_merge_zoom_hints(self):
        base = {
            "regions": {
                "bottom_tab_labels": {"box": [0, 0, 1, 1], "zoom_hints": {"step_min": 1.5}}
            }
        }
        merged = merge_config_with_learnings(
            {
                **base,
                "regions": {
                    **base["regions"],
                },
            }
        )
        # without overlay file, unchanged
        self.assertEqual(
            merged["regions"]["bottom_tab_labels"]["zoom_hints"]["step_min"], 1.5
        )

    def test_apply_explore_step(self):
        overlay: dict = {"regions": {}}
        report = {
            "exploration": [
                {
                    "region": "bottom_tab_labels",
                    "zoom_sweep": [{"step": 2.0, "needle_hits": 2}],
                }
            ],
            "regions": [],
        }
        notes = _apply_report_to_overlay(overlay, report)
        self.assertTrue(notes)
        self.assertGreaterEqual(
            overlay["regions"]["bottom_tab_labels"]["zoom_hints"]["step_min"], 1.85
        )


if __name__ == "__main__":
    unittest.main()
