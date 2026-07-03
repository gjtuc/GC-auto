# -*- coding: utf-8 -*-
"""
T92 — ``fallback_channel`` 파싱·L4 atom shell 재시도 연동.

정적: parse_fallback_channel
실행: apply_atom_fallback · P2.04 retry with ^a fallback

실행:
  python -m unittest test_gc1_runtime_layer4_atom_fallback -v
"""
from __future__ import annotations

import tempfile
import unittest

from gc1_runtime.layer0_ctl import ListViewGeom
from gc1_runtime.layer0_fallback import parse_fallback_channel
from gc1_runtime.layer1_state import AtomStatus, JobPaths, JobState, StateStore
from gc1_runtime.layer2_gates import GateEvaluator
from gc1_runtime.layer4_atom_fallback import apply_atom_fallback
from gc1_runtime.layer4_atoms_p0_p1 import AtomContext, P0P1Deps, run_atom_shell
from gc1_runtime.layer4_atoms_p2_p3 import P2P3Deps, P2_P3_ATOM_SPECS


class TestFallbackParseStatic(unittest.TestCase):
    def test_known_channels(self):
        self.assertEqual(parse_fallback_channel("H re-click neutral"), "h_reclick_neutral")
        self.assertEqual(parse_fallback_channel("H resend ^a"), "h_resend_ctrl_a")
        self.assertEqual(parse_fallback_channel("E eye click 초기화"), "e_eye_menu_init")
        self.assertEqual(parse_fallback_channel("F send_keys path"), "f_send_keys_open")
        self.assertEqual(parse_fallback_channel("send_keys ENTER"), "send_keys_enter")
        self.assertEqual(parse_fallback_channel("%s"), "send_keys_alt_s")
        self.assertIsNone(parse_fallback_channel(None))


class TestFallbackExecution(unittest.TestCase):
    def setUp(self) -> None:
        self._tmpdir = tempfile.TemporaryDirectory()
        self.sent: list[str] = []
        tick = {"t": 0.0}

        def sleep(sec: float) -> None:
            tick["t"] += sec

        hand = __import__("gc1_runtime.layer3_hand", fromlist=["HandActuator"]).HandActuator(
            send_keys_fn=lambda k, **__: self.sent.append(k),
        )
        self.deps = P2P3Deps(
            dry_run=True,
            pdf_output_dir=self._tmpdir.name,
            data_name="20260630_DRE-01",
            on_analysis_tab=True,
            listview_geoms=[
                ListViewGeom(top=100, bottom=280, left=20, right=420, item_count=8),
            ],
            hand=hand,
            clock=lambda: tick["t"],
            sleep=sleep,
            menu_popup_items=["초기화"],
        )
        self.store = StateStore(JobPaths(self._tmpdir.name))
        self.ctx = AtomContext(
            state=self.store.load(),
            store=self.store,
            gates=GateEvaluator(),
            deps=self.deps,
        )

    def tearDown(self) -> None:
        self._tmpdir.cleanup()

    def test_apply_h_resend_ctrl_a(self):
        snap = apply_atom_fallback(self.ctx, "H resend ^a", atom_id="Ω.A.L4.P2.04")
        self.assertEqual(snap["fallback_kind"], "h_resend_ctrl_a")
        self.assertIn("^a", self.sent)
        self.assertTrue(self.deps.ctrl_a_sent)

    def test_p204_shell_retry_uses_fallback(self):
        """post 1차 실패 → fallback ^a → 2차 성공."""
        post_calls = {"n": 0}

        def act() -> dict:
            return {"keys": "^a"}

        def post(_snap: dict) -> tuple[bool, ...]:
            post_calls["n"] += 1
            if post_calls["n"] == 1:
                return (False,)
            return (True,)

        outcome = run_atom_shell(
            self.ctx,
            P2_P3_ATOM_SPECS["Ω.A.L4.P2.04"],
            pre_probes=(True,),
            act=act,
            post_probes=post,
        )
        self.assertTrue(outcome.ok)
        state = self.store.load()
        rec = state.atoms["Ω.A.L4.P2.04"]
        self.assertEqual(rec.status, AtomStatus.OK)
        self.assertIn("^a", self.sent)
        self.assertIn("fallback_kind", rec.probe_snapshot)


if __name__ == "__main__":
    unittest.main()
