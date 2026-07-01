# -*- coding: utf-8 -*-
"""T52 — gc1_runtime.layer4_atoms_p4 P4 MTD load dry-run."""
from __future__ import annotations

import json
import os
import tempfile
import unittest

from gc1_runtime.layer0_ctl import ListViewGeom, TreeGeom
from gc1_runtime.layer1_state import AtomStatus, JobPaths, StateStore
from gc1_runtime.layer4_atoms_p2_p3 import run_p0_p3_dry
from gc1_runtime.layer4_atoms_p4 import (
    P4Deps,
    P4_ATOM_IDS,
    choose_tree_line_for_data_name,
    run_p0_p4_dry,
    run_p4_dry,
    tree_right_click_coords,
)


def _make_p4_deps(folder: str, *, mtd: bool = True) -> P4Deps:
    tick = {"t": 3000.0}

    def clock() -> float:
        return tick["t"]

    def sleep(sec: float) -> None:
        tick["t"] += sec

    hand = __import__("gc1_runtime.layer3_hand", fromlist=["HandActuator"]).HandActuator(
        send_keys_fn=lambda _k, **__: None,
    )
    if mtd:
        mtd_path = os.path.join(folder, "20260630 분석방법.MTD")
        with open(mtd_path, "w", encoding="utf-8") as fh:
            fh.write("mtd")
    return P4Deps(
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
        load_menu_items=["분석방법 불러오기"],
    )


class TestTreePure(unittest.TestCase):
    def test_choose_tree_line(self):
        lines = ["20260630_DRE-01.1", "YL6500 GC"]
        chosen = choose_tree_line_for_data_name(lines, "20260630_DRE-01")
        self.assertEqual(chosen, "20260630_DRE-01")

    def test_right_click_coords(self):
        rel_x, rel_y = tree_right_click_coords(240, 400)
        self.assertEqual(rel_x, 80)
        self.assertEqual(rel_y, 28)


class TestP4DryRun(unittest.TestCase):
    def setUp(self) -> None:
        self._tmpdir = tempfile.TemporaryDirectory()
        self.store = StateStore(JobPaths(self._tmpdir.name))
        self.deps = _make_p4_deps(self._tmpdir.name)

    def tearDown(self) -> None:
        self._tmpdir.cleanup()

    def test_p4_after_p0_p3(self):
        run_p0_p3_dry(self.store, self.deps)
        p4 = run_p4_dry(self.store, self.deps)
        self.assertTrue(p4.ok)
        state = self.store.load()
        self.assertEqual(state.phase_current, "P5")
        for aid in P4_ATOM_IDS:
            self.assertEqual(state.atoms[aid].status, AtomStatus.OK, msg=aid)

    def test_full_p0_p4_chain(self):
        outcomes = run_p0_p4_dry(self.store, self.deps)
        self.assertEqual(len(outcomes), 5)
        self.assertTrue(all(o.ok for o in outcomes))

    def test_mtd_dialog_and_tree_logged(self):
        run_p0_p4_dry(self.store, self.deps)
        ops = [r.op for r in self.deps.hand.log]
        self.assertIn("tree.select", ops)
        self.assertIn("file_dialog", ops)
        self.assertTrue(self.deps.mtd_dialog_ok)

    def test_p4_01_fails_without_mtd(self):
        with tempfile.TemporaryDirectory() as empty_dir:
            store = StateStore(JobPaths(empty_dir))
            deps = _make_p4_deps(empty_dir, mtd=False)
            run_p0_p3_dry(store, deps)
            p4 = run_p4_dry(store, deps)
            self.assertFalse(p4.ok)
            rec = store.load().atoms["Ω.A.L4.P4.01"]
            self.assertEqual(rec.status, AtomStatus.FAIL)
            self.assertEqual(rec.fail_code, "E_MTD_MISSING")

    def test_job_json_p4_atoms(self):
        run_p0_p4_dry(self.store, self.deps)
        with open(self.store.paths.job_json, encoding="utf-8") as fh:
            raw = json.load(fh)
        self.assertEqual(raw["atoms"]["Ω.A.L4.P4.01"]["status"], "ok")
        self.assertIn("mtd_path", raw["atoms"]["Ω.A.L4.P4.01"]["probe_snapshot"])


class TestAtomRegistry(unittest.TestCase):
    def test_p4_count(self):
        self.assertEqual(len(P4_ATOM_IDS), 8)


if __name__ == "__main__":
    unittest.main()
