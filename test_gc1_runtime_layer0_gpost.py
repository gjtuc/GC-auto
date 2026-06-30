# -*- coding: utf-8 -*-
"""
T91 — ``layer0_gpost`` PART6 G-POST retry 검증.

정적: plan 로드·validate_gpost_plans
실행: run_gpost_eye_verify 루프 · L4 P3.06 gpost retry chain

실행:
  python -m unittest test_gc1_runtime_layer0_gpost -v
"""
from __future__ import annotations

import json
import os
import tempfile
import unittest

from gc1_runtime.layer0_gpost import (
    DEFAULT_RETRY_POLICY_PATH,
    GPostRetryPlan,
    load_gpost_plans,
    run_gpost_eye_verify,
    validate_gpost_plans,
)


class TestGPostStatic(unittest.TestCase):
    def test_load_default_policy_has_three_tasks(self):
        plans = load_gpost_plans(DEFAULT_RETRY_POLICY_PATH)
        self.assertIn("verify_peak_table_cleared", plans)
        self.assertIn("verify_peak_table_has_data", plans)
        self.assertIn("verify_active_tab_analysis", plans)
        self.assertEqual(plans["verify_peak_table_has_data"].extra_wait_sec, 2.0)

    def test_validate_builtin_tasks(self):
        plans = load_gpost_plans(DEFAULT_RETRY_POLICY_PATH)
        errors = validate_gpost_plans(plans)
        self.assertEqual(errors, [])

    def test_missing_task_in_json(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "policy.json")
            with open(path, "w", encoding="utf-8") as fh:
                json.dump({"g_post_retry": []}, fh)
            plans = load_gpost_plans(path)
            # fallback to builtin
            self.assertIn("verify_peak_table_cleared", plans)


class TestGPostExecution(unittest.TestCase):
    def test_pass_without_retry(self):
        result = run_gpost_eye_verify(
            task_id="verify_peak_table_cleared",
            evaluate=lambda: (True, {"n": 1}),
            retry_fn=lambda: self.fail("should not retry"),
            sleep_fn=lambda _s: None,
        )
        self.assertTrue(result.passed)
        self.assertFalse(result.retried)

    def test_retry_then_pass(self):
        state = {"calls": 0}

        def evaluate() -> tuple[bool, dict]:
            state["calls"] += 1
            return (state["calls"] >= 2, {"calls": state["calls"]})

        retried = {"v": False}

        def retry() -> None:
            retried["v"] = True

        slept: list[float] = []

        result = run_gpost_eye_verify(
            task_id="verify_peak_table_has_data",
            evaluate=evaluate,
            retry_fn=retry,
            sleep_fn=lambda s: slept.append(s),
            plan=GPostRetryPlan(
                task_id="verify_peak_table_has_data",
                retry_atom_id="Ω.A.L4.P4.07",
                extra_wait_sec=2.0,
            ),
        )
        self.assertTrue(result.passed)
        self.assertTrue(result.retried)
        self.assertTrue(retried["v"])
        self.assertEqual(slept, [2.0])

    def test_retry_still_fail(self):
        result = run_gpost_eye_verify(
            task_id="verify_peak_table_cleared",
            evaluate=lambda: (False, {}),
            retry_fn=lambda: None,
            sleep_fn=lambda _s: None,
            plan=GPostRetryPlan(
                task_id="verify_peak_table_cleared",
                retry_atom_id="Ω.A.L4.P3.04",
                fail_code="E_VERIFY_PEAK",
            ),
        )
        self.assertFalse(result.passed)
        self.assertTrue(result.retried)
        self.assertEqual(result.fail_code, "E_VERIFY_PEAK")


if __name__ == "__main__":
    unittest.main()
