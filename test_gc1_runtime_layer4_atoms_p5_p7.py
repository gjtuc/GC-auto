# -*- coding: utf-8 -*-
"""T53 — gc1_runtime.layer4_atoms_p5_p7 P5~P7 dry-run."""
from __future__ import annotations

import json
import os
import tempfile
import unittest

from gc1_runtime.layer0_ctl import ListViewGeom, TreeGeom
from gc1_runtime.layer1_state import AtomStatus, JobPaths, StateStore
from gc1_runtime.layer4_atoms_p4 import run_p0_p4_dry
from gc1_runtime.layer4_atoms_p5_p7 import (
    P57Deps,
    P5_ATOM_IDS,
    P5_P7_ATOM_IDS,
    P6_ATOM_IDS,
    P7_ATOM_IDS,
    poll_quantify_progress_done,
    run_p0_p7_dry,
    run_p5_p7_dry,
    top_menu_has_item,
)


def _make_p57_deps(folder: str) -> P57Deps:
    tick = {"t": 4000.0}

    def clock() -> float:
        return tick["t"]

    def sleep(sec: float) -> None:
        tick["t"] += sec

    hand = __import__("gc1_runtime.layer3_hand", fromlist=["HandActuator"]).HandActuator(
        send_keys_fn=lambda _k, **__: None,
    )
    mtd_path = os.path.join(folder, "20260630 분석방법.MTD")
    with open(mtd_path, "w", encoding="utf-8") as fh:
        fh.write("mtd")
    return P57Deps(
        dry_run=True,
        pdf_output_dir=folder,
        mtd_dir=folder,
        data_name="20260630_DRE-01",
        on_analysis_tab=True,
        listview_geoms=[
            ListViewGeom(top=100, bottom=280, left=20, right=420, item_count=8),
            ListViewGeom(top=400, bottom=600, left=20, right=420, item_count=5),
        ],
        tree_lines=["20260630_DRE-01", "YL6500 GC"],
        tree_geom=TreeGeom(top=120, bottom=520, left=10, right=250),
        hand=hand,
        clock=clock,
        sleep=sleep,
        peak_table_text="0 0 0 0 0",
        peak_table_after_mtd="0.12 3.45 5.6",
        peak_table_after_p6="0 0 0 0 0",
        peak_table_after_quantify="0.12 3.45 5.6",
        progress_visible=lambda: False,
        load_menu_items=["분석방법 불러오기"],
    )


class TestPureHelpers(unittest.TestCase):
    def test_top_menu_has_item(self):
        items = [{"text": "시료목록(T)", "menu_items": {"menu_items": [{"text": "초기화+정량"}]}}]
        self.assertTrue(top_menu_has_item(items, "시료목록", "초기화+정량"))

    def test_poll_quantify_progress(self):
        tick = {"t": 0.0}

        def clock() -> float:
            return tick["t"]

        def sleep(sec: float) -> None:
            tick["t"] += sec

        done, polls = poll_quantify_progress_done(
            is_progress_visible=lambda: False,
            clock=clock,
            sleep=sleep,
            max_wait_sec=30.0,
            initial_sleep_sec=0.0,
        )
        self.assertTrue(done)
        self.assertGreaterEqual(polls, 1)


class TestP57DryRun(unittest.TestCase):
    def setUp(self) -> None:
        self._tmpdir = tempfile.TemporaryDirectory()
        self.store = StateStore(JobPaths(self._tmpdir.name))
        self.deps = _make_p57_deps(self._tmpdir.name)

    def tearDown(self) -> None:
        self._tmpdir.cleanup()

    def test_p5_p7_after_p0_p4(self):
        run_p0_p4_dry(self.store, self.deps)
        p5, p6, p7 = run_p5_p7_dry(self.store, self.deps)
        self.assertTrue(p5.ok and p6.ok and p7.ok)
        state = self.store.load()
        self.assertEqual(state.phase_current, "P8")
        for aid in P5_P7_ATOM_IDS:
            self.assertEqual(state.atoms[aid].status, AtomStatus.OK, msg=aid)

    def test_full_p0_p7_chain(self):
        outcomes = run_p0_p7_dry(self.store, self.deps)
        self.assertEqual(len(outcomes), 8)
        self.assertTrue(all(o.ok for o in outcomes))

    def test_quantify_menu_and_ctrl_a(self):
        run_p0_p7_dry(self.store, self.deps)
        ops = [r.op for r in self.deps.hand.log]
        self.assertIn("menu_select", ops)
        self.assertIn("send_keys", ops)
        self.assertTrue(self.deps.quantify_menu_selected)

    def test_p7_05_fails_without_peak_data(self):
        self.deps.peak_table_after_quantify = "0 0 0 0 0"
        run_p0_p4_dry(self.store, self.deps)
        _, _, p7 = run_p5_p7_dry(self.store, self.deps)
        self.assertFalse(p7.ok)
        rec = self.store.load().atoms["Ω.A.L4.P7.05"]
        self.assertEqual(rec.status, AtomStatus.FAIL)

    def test_job_json_p7_atoms(self):
        run_p0_p7_dry(self.store, self.deps)
        with open(self.store.paths.job_json, encoding="utf-8") as fh:
            raw = json.load(fh)
        self.assertEqual(raw["atoms"]["Ω.A.L4.P7.02"]["status"], "ok")


class TestAtomRegistry(unittest.TestCase):
    def test_counts(self):
        self.assertEqual(len(P5_ATOM_IDS), 5)
        self.assertEqual(len(P6_ATOM_IDS), 6)
        self.assertEqual(len(P7_ATOM_IDS), 5)


if __name__ == "__main__":
    unittest.main()
