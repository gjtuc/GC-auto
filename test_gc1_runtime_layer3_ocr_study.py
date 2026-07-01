# -*- coding: utf-8 -*-
"""성숙도·마우스 가드·스터디 세션 단위 테스트."""
from __future__ import annotations

import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from gc1_runtime.layer3_ocr_maturity import (
    MATURITY_RATE,
    MIN_ATTEMPTS,
    append_observation,
    discard_contaminated_run_learning,
    invalidate_run_learning_on_contamination,
    is_skill_mature,
    load_maturity,
    record_outcome,
    skill_key,
    snapshot_learning_state,
)
from gc1_runtime.layer3_user_mouse_guard import UserMouseGuard


class TestMaturity(unittest.TestCase):
    def test_mature_at_threshold(self):
        with tempfile.TemporaryDirectory() as tmp:
            learn = Path(tmp) / "learn"
            learn.mkdir()
            with mock.patch("gc1_runtime.layer3_ocr_maturity.learnings_dir", return_value=learn):
                key = skill_key("P3.menu", "context_menu_popup", "초기화")
                for _ in range(MIN_ATTEMPTS):
                    record_outcome(key, success=True, method="ocr_click")
                self.assertTrue(is_skill_mature(key))

    def test_demote_on_failure(self):
        with tempfile.TemporaryDirectory() as tmp:
            learn = Path(tmp) / "learn"
            learn.mkdir()
            with mock.patch("gc1_runtime.layer3_ocr_maturity.learnings_dir", return_value=learn):
                key = skill_key("P4", "left_analysis_tree", "불러오기")
                for _ in range(MIN_ATTEMPTS):
                    record_outcome(key, success=True)
                self.assertTrue(is_skill_mature(key))
                record_outcome(key, success=False)
                self.assertFalse(is_skill_mature(key))


class TestMouseGuard(unittest.TestCase):
    def test_vibration_does_not_pause(self):
        g = UserMouseGuard()
        g._last = (100, 100)
        g._last = (100, 100)
        # simulate small jitter
        for i in range(5):
            g._last = (100 + i * 3, 100)
            dx = 3
            g._moves.append((__import__("time").time(), dx))
        self.assertFalse(g.paused)

    def test_swipe_pauses(self):
        g = UserMouseGuard()
        g._last = (0, 0)
        g._trigger("test")
        self.assertTrue(g.paused)


class TestContaminatedRunDiscard(unittest.TestCase):
    def test_invalidate_restores_maturity_snapshot(self):
        with tempfile.TemporaryDirectory() as tmp:
            learn = Path(tmp) / "learn"
            learn.mkdir()
            run_id = "20260701_test"
            current = {
                "run_id": run_id,
                "started": "2026-07-01T00:00:00+00:00",
                "pipeline": True,
            }
            (learn / "current_run.json").write_text(
                json.dumps(current), encoding="utf-8"
            )
            with mock.patch("gc1_runtime.layer3_ocr_maturity.learnings_dir", return_value=learn), mock.patch(
                "gc1_runtime.layer3_ocr_learn.learnings_dir", return_value=learn
            ), mock.patch(
                "gc1_runtime.layer3_ocr_learn._current_run_path",
                return_value=learn / "current_run.json",
            ):
                key = skill_key("P3.menu", "context_menu_popup", "초기화")
                for _ in range(5):
                    record_outcome(key, success=True)
                snapshot_learning_state(run_id)
                record_outcome(key, success=True)
                self.assertEqual(load_maturity()["skills"][key]["attempts"], 6)
                append_observation(
                    run_id,
                    step_id="P3.menu",
                    region_id="context_menu_popup",
                    action="초기화",
                    success=True,
                )
                obs = learn / "runs" / run_id / "observations.jsonl"
                self.assertTrue(obs.is_file())

                info = invalidate_run_learning_on_contamination(reason="single_swipe")
                self.assertTrue(info["maturity_restored"])
                self.assertEqual(load_maturity()["skills"][key]["attempts"], 5)
                self.assertFalse(obs.is_file())

    def test_discard_deletes_case_study_files(self):
        with tempfile.TemporaryDirectory() as tmp:
            learn = Path(tmp) / "learn"
            case = Path(tmp) / "case"
            learn.mkdir()
            case.mkdir()
            run_id = "20260701_case"
            fail_path = case / "fail_P4_test.json"
            fail_path.write_text("{}", encoding="utf-8")
            run_data = {
                "run_id": run_id,
                "started": "2026-07-01T00:00:00+00:00",
                "fail_reports": [str(fail_path)],
            }
            with mock.patch("gc1_runtime.layer3_ocr_maturity.learnings_dir", return_value=learn), mock.patch(
                "gc1_runtime.layer3_ocr_learn.learnings_dir", return_value=learn
            ), mock.patch("gc1_runtime.layer3_ocr_learn.case_study_dir", return_value=case):
                snapshot_learning_state(run_id)
                info = discard_contaminated_run_learning(
                    run_id,
                    run_data=run_data,
                    reason="window_swipe",
                )
                self.assertTrue(info["discarded"])
                self.assertEqual(info["case_study_deleted"], 1)
                self.assertFalse(fail_path.is_file())


if __name__ == "__main__":
    unittest.main()
