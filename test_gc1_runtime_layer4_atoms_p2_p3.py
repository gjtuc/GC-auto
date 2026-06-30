# -*- coding: utf-8 -*-
"""T51 — gc1_runtime.layer4_atoms_p2_p3 P2 select_all + P3 initialize dry-run."""
from __future__ import annotations

import json
import os
import tempfile
import unittest

from gc1_runtime.layer0_ctl import ListViewGeom
from gc1_runtime.layer1_state import AtomStatus, JobPaths, StateStore
from gc1_runtime.layer4_atoms_p0_p1 import run_p0_p1_dry
from gc1_runtime.layer4_atoms_p2_p3 import (
    P2P3Deps,
    P2_ATOM_IDS,
    P2_P3_ATOM_IDS,
    P3_ATOM_IDS,
    neutral_list_coords,
    run_p0_p3_dry,
    run_p2_p3_dry,
)


def _make_deps(folder: str) -> P2P3Deps:
    tick = {"t": 2000.0}
    sent: list[str] = []

    def clock() -> float:
        return tick["t"]

    def sleep(sec: float) -> None:
        tick["t"] += sec

    def fake_send(keys: str, **_) -> None:
        sent.append(keys)

    hand = __import__("gc1_runtime.layer3_hand", fromlist=["HandActuator"]).HandActuator(
        send_keys_fn=fake_send,
    )
    return P2P3Deps(
        dry_run=True,
        pdf_output_dir=folder,
        data_name="20260630_DRE-01",
        on_analysis_tab=True,
        listview_geoms=[
            ListViewGeom(top=100, bottom=280, left=20, right=420, item_count=8),
            ListViewGeom(top=400, bottom=600, left=20, right=420, item_count=5),
        ],
        hand=hand,
        clock=clock,
        sleep=sleep,
        peak_table_text="0 0 0 0 0",
        menu_popup_items=["초기화", "초기화+정량"],
    )


class TestNeutralCoords(unittest.TestCase):
    def test_matches_autochro_formula(self):
        rel_x, rel_y = neutral_list_coords(400, 200, x_frac=0.78)
        self.assertEqual(rel_x, 312)
        self.assertEqual(rel_y, 20)


class TestP2P3DryRun(unittest.TestCase):
    def setUp(self) -> None:
        self._tmpdir = tempfile.TemporaryDirectory()
        self.store = StateStore(JobPaths(self._tmpdir.name))
        self.deps = _make_deps(self._tmpdir.name)

    def tearDown(self) -> None:
        self._tmpdir.cleanup()

    def test_p2_p3_after_p0_p1(self):
        p0, p1 = run_p0_p1_dry(self.store, self.deps)
        self.assertTrue(p0.ok and p1.ok)
        p2, p3 = run_p2_p3_dry(self.store, self.deps)
        self.assertTrue(p2.ok and p3.ok)

        state = self.store.load()
        self.assertEqual(state.phase_current, "P4")
        for aid in P2_P3_ATOM_IDS:
            rec = state.atoms[aid]
            self.assertEqual(rec.status, AtomStatus.OK, msg=aid)
            self.assertIsNotNone(rec.ended_at)

    def test_full_p0_p3_chain(self):
        outcomes = run_p0_p3_dry(self.store, self.deps)
        self.assertEqual(len(outcomes), 4)
        self.assertTrue(all(o.ok for o in outcomes))
        state = self.store.load()
        self.assertEqual(state.phase_current, "P4")

    def test_ctrl_a_and_menu_recorded(self):
        run_p0_p3_dry(self.store, self.deps)
        ops = [r.op for r in self.deps.hand.log]
        self.assertIn("send_keys", ops)
        self.assertTrue(self.deps.ctrl_a_sent)
        self.assertTrue(self.deps.context_menu_clicked)

    def test_p3_06_fails_when_peak_not_cleared(self):
        self.deps.peak_table_text = "1.5 2.3 4.5 5.6"
        run_p0_p1_dry(self.store, self.deps)
        p2, p3 = run_p2_p3_dry(self.store, self.deps)
        self.assertTrue(p2.ok)
        self.assertFalse(p3.ok)
        rec = self.store.load().atoms["Ω.A.L4.P3.06"]
        self.assertEqual(rec.status, AtomStatus.FAIL)
        self.assertEqual(rec.fail_code, "E_VERIFY_PEAK")

    def test_job_json_has_p2_atoms(self):
        run_p0_p3_dry(self.store, self.deps)
        path = self.store.paths.job_json
        with open(path, encoding="utf-8") as fh:
            raw = json.load(fh)
        self.assertEqual(raw["atoms"]["Ω.A.L4.P2.04"]["status"], "ok")
        self.assertEqual(raw["atoms"]["Ω.A.L4.P3.04"]["status"], "ok")


class TestAtomRegistry(unittest.TestCase):
    def test_counts(self):
        self.assertEqual(len(P2_ATOM_IDS), 5)
        self.assertEqual(len(P3_ATOM_IDS), 6)


if __name__ == "__main__":
    unittest.main()
