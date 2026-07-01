# -*- coding: utf-8 -*-
"""T32 — gc1_runtime.layer0_data (DN/MTD) — test_gc_autochro_prep 이전·확장."""
from __future__ import annotations

import os
import tempfile
import unittest

from gc1_runtime.layer0_data import (
    analysis_tree_has_control_overlap,
    analysis_tree_line_has_control_ghost,
    analysis_tree_matching_lines,
    analysis_tree_needs_paint_refresh,
    build_analysis_method_mtd_path,
    extract_date8_from_data_name,
    extract_mtd_date_prefix,
    is_valid_data_name,
    parse_data_name_from_tree_lines,
    parse_data_name_from_window_title,
    rank_tree_line_for_data_name,
    resolve_analysis_method_mtd_path,
    resolve_data_name,
    tree_label_matches_data_name,
)


class TestTreeLabelMatches(unittest.TestCase):
    def test_tree_matches_suffix(self):
        name = "20260629 dre(3) ni-ce-la"
        self.assertTrue(tree_label_matches_data_name(name, name))
        self.assertTrue(
            tree_label_matches_data_name("20260629 dre(3) ni-ce-la - 상온-1", name),
        )
        self.assertFalse(tree_label_matches_data_name("20260624 dre(3) ni-ce", name))

    def test_rank_rejects_wrong_date(self):
        target = "20260630dre(5)ni(환원)-ce"
        self.assertGreater(
            rank_tree_line_for_data_name("20260630dre(5)ni(환원)-ce", target),
            rank_tree_line_for_data_name("20260629 dre(3) ni-ce-la", target),
        )
        self.assertEqual(
            rank_tree_line_for_data_name("20260629 dre(3) ni-ce-la", target),
            -1.0,
        )

    def test_extract_date8(self):
        self.assertEqual(
            extract_date8_from_data_name("20260630dre(5)ni(환원)-ce"),
            "20260630",
        )

    def test_tree_overlap_detection(self):
        target = "20260630dre(5)ni(환원)-ce"
        lines = [
            "20260630dre(5)ni(환원)-ce",
            "20260630dre(5)ni(환원)-ce",
            "YL6500 GC 0",
        ]
        self.assertTrue(analysis_tree_has_control_overlap(lines, target))
        self.assertEqual(len(analysis_tree_matching_lines(lines, target)), 2)
        ok_lines = ["20260630dre(5)ni(환원)-ce", "YL6500 GC 0"]
        self.assertFalse(analysis_tree_has_control_overlap(ok_lines, target))

    def test_control_ghost_one_line(self):
        target = "20260630dre(5)ni(환원)-ce"
        ghost = "| 제어목록 | @ 20260630016(5)01(환원)-6"
        self.assertTrue(analysis_tree_line_has_control_ghost(ghost))
        self.assertTrue(
            analysis_tree_needs_paint_refresh([ghost], target, ocr_text=ghost)
        )
        self.assertFalse(
            analysis_tree_needs_paint_refresh(
                ["20260630dre(5)ni(환원)-ce"], target
            )
        )

    def test_multi_folder_ocr_not_ghost(self):
        """20260629·20260630 폴더가 같이 보여도 잔상 아님 (이전 날짜 substring 오탐 방지)."""
        target = "20260630dre(5)ni(환원)-ce"
        ocr = (
            "~ 분석목록 & 20260629 dre(3) ni-ce-la "
            "20260630dre(5)ni(환원)-ce 적분정보"
        )
        self.assertFalse(
            analysis_tree_needs_paint_refresh([], target, ocr_text=ocr)
        )
        ocr_dup_substr = "20260630016(5)01 20260630dre(5)ni"
        self.assertFalse(
            analysis_tree_needs_paint_refresh([], target, ocr_text=ocr_dup_substr)
        )

    def test_tab_label_bleed_not_ghost(self):
        """W32 탭 라벨만 섞인 '제어목록' — 잔상 아님."""
        target = "20260630dre(5)ni(환원)-ce"
        w32_lines = ["제어목록", "20260630dre(5)ni(환원)-ce", "YL6500 GC 0"]
        self.assertFalse(analysis_tree_needs_paint_refresh(w32_lines, target))
        self.assertFalse(analysis_tree_line_has_control_ghost("제어목록"))
        real = "| 제어목록 | @ 20260630016(5)01(환원)-6"
        self.assertTrue(analysis_tree_line_has_control_ghost(real))


class TestMtdPath(unittest.TestCase):
    def test_extract_date_8digit(self):
        self.assertEqual(
            extract_mtd_date_prefix("20260629 dre(3) ni-ce-la"),
            "20260629",
        )

    def test_extract_date_6digit_expands(self):
        self.assertEqual(extract_mtd_date_prefix("260629 test"), "20260629")

    def test_resolve_mtd_path_8digit(self):
        with tempfile.TemporaryDirectory() as tmp:
            mtd = os.path.join(tmp, "20260629 분석방법.MTD")
            with open(mtd, "w", encoding="utf-8") as fh:
                fh.write("x")
            path = resolve_analysis_method_mtd_path(
                "20260629 dre(3) ni-ce-la",
                mtd_dir=tmp,
            )
            self.assertEqual(path, mtd)

    def test_build_path_without_exist_check(self):
        with tempfile.TemporaryDirectory() as tmp:
            built = build_analysis_method_mtd_path("20260629 x", tmp)
            self.assertTrue(built.endswith("20260629 분석방법.MTD"))

    def test_missing_mtd_raises(self):
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(FileNotFoundError):
                resolve_analysis_method_mtd_path("20260629 x", mtd_dir=tmp)


class TestDataNameDn(unittest.TestCase):
    def test_title_parse(self):
        got = parse_data_name_from_window_title(
            "20260629 dre(3) ni-ce-la - Autochro-3000",
        )
        self.assertEqual(got, "20260629 dre(3) ni-ce-la")

    def test_title_invalid_returns_empty(self):
        self.assertEqual(parse_data_name_from_window_title("Autochro only"), "")

    def test_tree_marker_above(self):
        lines = [
            "20260629 dre(3) ni-ce-la",
            "YL6500 GC 0",
        ]
        self.assertEqual(
            parse_data_name_from_tree_lines(lines),
            "20260629 dre(3) ni-ce-la",
        )

    def test_tree_selected_fallback(self):
        got = parse_data_name_from_tree_lines(
            ["other"],
            selected=["20260630 foo.bar"],
        )
        self.assertEqual(got, "20260630 foo")

    def test_is_valid_data_name(self):
        self.assertTrue(is_valid_data_name("20260629 dre"))
        self.assertFalse(is_valid_data_name("dre only"))

    def test_resolve_data_name_chain(self):
        name = resolve_data_name(
            window_title="20260629 x - Autochro",
            env_fallback="",
        )
        self.assertEqual(name, "20260629 x")

    def test_resolve_data_name_fallback_env(self):
        name = resolve_data_name(env_fallback="20260629 from env")
        self.assertEqual(name, "20260629 from env")

    def test_resolve_data_name_raises(self):
        with self.assertRaises(ValueError):
            resolve_data_name()


if __name__ == "__main__":
    unittest.main()
