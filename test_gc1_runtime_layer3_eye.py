# -*- coding: utf-8 -*-
"""T41 — gc1_runtime.layer3_eye (geometry·token·TASK, Tesseract 없음)."""
from __future__ import annotations

import os
import unittest

from gc_screen_read import Box, OcrToken
from gc1_runtime.layer3_eye import (
    EyeActuator,
    box_from_fraction,
    filter_tokens_by_confidence,
    load_config,
    parse_tesseract_token_dict,
    resolve_region_box,
    upscale_image,
    verify_active_tab_analysis,
    verify_peak_table_cleared,
    verify_peak_table_has_data,
    verify_read_task,
)


class TestEyeGeometry(unittest.TestCase):
    def test_box_from_fraction(self):
        parent = Box(100, 200, 1000, 800)
        child = box_from_fraction(parent, [0.1, 0.2, 0.5, 0.3])
        self.assertEqual((child.left, child.top, child.width, child.height), (200, 360, 500, 240))

    def test_resolve_region_chain(self):
        cfg_path = os.path.join(
            os.path.dirname(__file__), "deploy", "screen_regions.gc1.json",
        )
        cfg = load_config(cfg_path)
        win = Box(0, 0, 1920, 1080)
        box, chain = resolve_region_box(cfg, "bottom_peak_table_fine", win)
        self.assertIn("autochro_window", chain)
        self.assertEqual(chain[-1], "bottom_peak_table_fine")
        self.assertGreater(box.height, 50)

    def test_upscale(self):
        from PIL import Image

        img = Image.new("RGB", (100, 40), color=(255, 255, 255))
        up = upscale_image(img, 2.5)
        self.assertEqual(up.size, (250, 100))

    def test_eye_actuator_resolve(self):
        cfg_path = os.path.join(
            os.path.dirname(__file__), "deploy", "screen_regions.gc1.json",
        )
        eye = EyeActuator(load_config(cfg_path))
        box, chain = eye.resolve_region("bottom_tabs", Box(0, 0, 1200, 800))
        self.assertTrue(chain)
        self.assertGreater(box.width, 0)


class TestEyeTokenFilter(unittest.TestCase):
    def test_parse_tesseract_dict_filters_low_conf(self):
        data = {
            "text": ["분석목록", "noise", "1.23"],
            "conf": ["90", "10", "30"],
            "left": [0, 10, 20],
            "top": [0, 0, 0],
            "width": [50, 50, 40],
            "height": [12, 12, 12],
        }
        tokens = parse_tesseract_token_dict(data)
        texts = [t.text for t in tokens]
        self.assertIn("분석목록", texts)
        self.assertIn("1.23", texts)
        self.assertNotIn("noise", texts)

    def test_filter_by_confidence(self):
        toks = (
            OcrToken("a", 90.0, Box(0, 0, 10, 10)),
            OcrToken("b", 20.0, Box(0, 0, 10, 10)),
            OcrToken("c", -1.0, Box(0, 0, 10, 10)),
        )
        kept = filter_tokens_by_confidence(toks)
        self.assertEqual([t.text for t in kept], ["a", "c"])

    def test_find_token_via_actuator(self):
        cfg_path = os.path.join(
            os.path.dirname(__file__), "deploy", "screen_regions.gc1.json",
        )
        eye = EyeActuator(load_config(cfg_path))
        hits = eye.find_token(
            [OcrToken("분석목록 탭", 80.0, Box(0, 0, 1, 1))],
            "분석목록",
        )
        self.assertEqual(len(hits), 1)


class TestEyeTaskVerify(unittest.TestCase):
    def test_active_tab(self):
        self.assertTrue(verify_active_tab_analysis("메뉴 분석목록 제어목록"))
        self.assertFalse(verify_active_tab_analysis("제어목록만"))

    def test_peak_has_data(self):
        self.assertTrue(verify_peak_table_has_data("peak 0.12 3.45"))
        self.assertFalse(verify_peak_table_has_data("no numbers"))

    def test_peak_cleared(self):
        self.assertTrue(verify_peak_table_cleared("0 0 0 0 0"))
        self.assertFalse(verify_peak_table_cleared("0 0 1.5 2.3 4.5"))

    def test_verify_read_task_from_config(self):
        cfg_path = os.path.join(
            os.path.dirname(__file__), "deploy", "screen_regions.gc1.json",
        )
        cfg = load_config(cfg_path)
        # config 에 정의된 task_id 하나 사용 (있으면)
        tasks = cfg.get("read_tasks") or {}
        if not tasks:
            self.skipTest("no read_tasks in config")
        tid = next(iter(tasks))
        task = tasks[tid]
        if task.get("expect_contains"):
            needle = task["expect_contains"][0]
            v = verify_read_task(cfg, tid, f"dummy {needle} text")
            self.assertTrue(v.passed, v.detail)


if __name__ == "__main__":
    unittest.main()
