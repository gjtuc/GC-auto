# -*- coding: utf-8 -*-
"""
T62 — P3/P4/P6/P7 peak TASK + ``GC1_RUNTIME_VERIFY_EYE=1`` 게이트.

실행: python -m unittest test_gc1_runtime_layer4_eye_gate -v
"""
from __future__ import annotations

import os
import tempfile
import unittest
from unittest import mock

from gc1_runtime.layer1_state import AtomStatus, JobPaths, JobState, StateStore
from gc1_runtime.layer3_eye import (
    EyeActuator,
    evaluate_peak_table_task,
    peak_table_plain_text,
)
from gc1_runtime.layer4_atoms_p2_p3 import P2P3Deps, run_p0_p3_dry
from gc1_runtime.layer4_atoms_p4 import P4Deps, run_p0_p4_dry
from gc1_runtime.layer4_atoms_p5_p7 import P57Deps, run_p0_p7_dry


def _cfg_path() -> str:
    return os.path.join(os.path.dirname(__file__), "deploy", "screen_regions.gc1.json")


class TestPeakTablePlainText(unittest.TestCase):
    def test_verify_eye_off_uses_fallback(self):
        text = peak_table_plain_text(
            verify_eye=False,
            dry_run=True,
            task_id="verify_peak_table_cleared",
            fallback_text="mock fallback",
        )
        self.assertEqual(text, "mock fallback")

    def test_verify_eye_on_uses_provider(self):
        text = peak_table_plain_text(
            verify_eye=True,
            dry_run=True,
            task_id="verify_peak_table_has_data",
            fallback_text="ignored",
            text_provider=lambda tid: f"provider:{tid}",
        )
        self.assertEqual(text, "provider:verify_peak_table_has_data")


class TestEvaluatePeakTableTask(unittest.TestCase):
    def test_cleared_task_pass(self):
        v = evaluate_peak_table_task(
            verify_eye=True,
            dry_run=True,
            task_id="verify_peak_table_cleared",
            fallback_text="0 0 0 0 0",
        )
        self.assertTrue(v.passed)

    def test_has_data_task_fail_on_empty(self):
        v = evaluate_peak_table_task(
            verify_eye=True,
            dry_run=True,
            task_id="verify_peak_table_has_data",
            fallback_text="no numbers here",
        )
        self.assertFalse(v.passed)


class TestP306EyeGateInChain(unittest.TestCase):
    """실행 검증 — verify_eye + provider 가 P3.06 atom 결과에 반영."""

    def setUp(self) -> None:
        self._tmpdir = tempfile.TemporaryDirectory()
        self.store = StateStore(JobPaths(self._tmpdir.name))

    def tearDown(self) -> None:
        self._tmpdir.cleanup()

    def _base_p2p3_deps(self, **kwargs) -> P2P3Deps:
        from gc1_runtime.layer0_ctl import ListViewGeom
        from gc1_runtime.layer3_hand import HandActuator

        tick = {"t": 5000.0}

        def clock() -> float:
            return tick["t"]

        def sleep(sec: float) -> None:
            tick["t"] += sec

        defaults: dict = dict(
            dry_run=True,
            pdf_output_dir=self._tmpdir.name,
            data_name="20260630_DRE-01",
            on_control_tab=True,
            listview_geoms=[
                ListViewGeom(top=100, bottom=280, left=20, right=420, item_count=8),
                ListViewGeom(top=400, bottom=600, left=20, right=420, item_count=5),
            ],
            hand=HandActuator(send_keys_fn=lambda k, **__: None),
            clock=clock,
            sleep=sleep,
            peak_table_text="0 0 0 0 0",
            menu_popup_items=["초기화", "초기화+정량"],
        )
        defaults.update(kwargs)
        return P2P3Deps(**defaults)

    def test_p3_06_ok_with_verify_eye_provider(self):
        deps = self._base_p2p3_deps(
            verify_eye=True,
            eye=EyeActuator(__import__("gc1_runtime.layer3_eye", fromlist=["load_config"]).load_config(_cfg_path())),
            peak_table_text="BAD 9.9 8.8",
            peak_table_text_provider=lambda _tid: "0 0 0 0 0",
        )
        run_p0_p3_dry(self.store, deps)
        state = self.store.load()
        self.assertEqual(state.atoms["Ω.A.L4.P3.06"].status, AtomStatus.OK)

    def test_p3_06_fail_when_provider_not_cleared(self):
        deps = self._base_p2p3_deps(
            verify_eye=True,
            eye=EyeActuator(__import__("gc1_runtime.layer3_eye", fromlist=["load_config"]).load_config(_cfg_path())),
            peak_table_text="0 0 0 0 0",
            peak_table_text_provider=lambda _tid: "1.2 3.4 5.6",
        )
        outcomes = run_p0_p3_dry(self.store, deps)
        self.assertFalse(outcomes[-1].ok)
        state = self.store.load()
        self.assertEqual(state.atoms["Ω.A.L4.P3.06"].status, AtomStatus.FAIL)

    def test_p3_06_gpost_retry_recovers(self):
        """G-POST — 1차 fail 후 provider 재시도 시 OK (T91)."""
        calls = {"n": 0}

        def provider(_tid: str) -> str:
            calls["n"] += 1
            if calls["n"] == 1:
                return "9.9 8.8 7.7"
            return "0 0 0 0 0"

        deps = self._base_p2p3_deps(
            verify_eye=True,
            eye=EyeActuator(__import__("gc1_runtime.layer3_eye", fromlist=["load_config"]).load_config(_cfg_path())),
            peak_table_text="BAD",
            peak_table_text_provider=provider,
        )
        run_p0_p3_dry(self.store, deps)
        state = self.store.load()
        self.assertEqual(state.atoms["Ω.A.L4.P3.06"].status, AtomStatus.OK)
        snap = state.atoms["Ω.A.L4.P3.06"].probe_snapshot
        self.assertTrue(snap.get("gpost_retried"))
        self.assertGreaterEqual(calls["n"], 2)


class TestP408P705EyeGate(unittest.TestCase):
    def setUp(self) -> None:
        self._tmpdir = tempfile.TemporaryDirectory()
        self.store = StateStore(JobPaths(self._tmpdir.name))

    def tearDown(self) -> None:
        self._tmpdir.cleanup()

    @mock.patch.dict(os.environ, {"GC1_RUNTIME_VERIFY_EYE": "0"}, clear=False)
    def test_p4_p7_default_mock_still_ok(self):
        """회귀 — verify_eye=0 이면 기존 mock 문자열 경로."""
        from test_gc1_runtime_layer4_atoms_p8_p9 import _make_p89_deps

        deps = _make_p89_deps(self._tmpdir.name)
        run_p0_p7_dry(self.store, deps)
        state = self.store.load()
        self.assertEqual(state.atoms["Ω.A.L4.P4.08"].status, AtomStatus.OK)
        self.assertEqual(state.atoms["Ω.A.L4.P7.05"].status, AtomStatus.OK)


if __name__ == "__main__":
    unittest.main()
