# -*- coding: utf-8 -*-
"""T50 — gc1_runtime.layer4_atoms_p0_p1 dry-run·StateStore·EARLY_OK."""
from __future__ import annotations

import json
import os
import tempfile
import time
import unittest

from gc1_runtime.layer0_ctl import ListViewGeom
from gc1_runtime.layer1_state import AtomStatus, JobPaths, JobState, StateStore
from gc1_runtime.layer4_atoms_p0_p1 import (
    P0_ATOM_IDS,
    P0_P1_ATOM_IDS,
    P1_ATOM_IDS,
    P0P1Deps,
    plan_pdf_path,
    run_p0_p1_dry,
    sync_double_click_coords,
)


class TestSyncCoords(unittest.TestCase):
    def test_double_click_coords_match_autochro(self):
        rel_x, rel_y = sync_double_click_coords(400, 200)
        self.assertEqual(rel_x, 248)
        self.assertEqual(rel_y, 33)


class TestPlanPdfPath(unittest.TestCase):
    def test_plan_pdf_path_stem(self):
        with tempfile.TemporaryDirectory() as folder:
            path = plan_pdf_path(folder, "20260630_DRE-01")
            self.assertTrue(path.lower().endswith(".pdf"))
            self.assertIn("20260630", os.path.basename(path))
            self.assertEqual(os.path.dirname(path), os.path.normpath(folder))


class TestDryRunP0P1(unittest.TestCase):
    def setUp(self) -> None:
        self._tmpdir = tempfile.TemporaryDirectory()
        self.store = StateStore(JobPaths(self._tmpdir.name))
        tick = {"t": 1000.0}

        def clock() -> float:
            return tick["t"]

        def sleep(sec: float) -> None:
            tick["t"] += sec

        self.deps = P0P1Deps(
            dry_run=True,
            force=False,
            pdf_output_dir=self._tmpdir.name,
            data_name="20260630_DRE-01",
            listview_geoms=[
                ListViewGeom(top=400, bottom=600, left=20, right=420, item_count=5),
            ],
            clock=clock,
            sleep=sleep,
        )

    def tearDown(self) -> None:
        self._tmpdir.cleanup()

    def test_full_dry_run_all_atoms_ok(self):
        p0, p1 = run_p0_p1_dry(self.store, self.deps)
        self.assertTrue(p0.ok)
        self.assertFalse(p0.early_exit)
        self.assertTrue(p1.ok)
        self.assertFalse(p1.skipped)

        state = self.store.load()
        self.assertEqual(state.phase_current, "P2")
        self.assertTrue(state.job_id)
        self.assertEqual(state.data_name, "20260630_DRE-01")
        self.assertTrue(state.pdf_path_planned)

        for aid in P0_P1_ATOM_IDS:
            rec = state.atoms.get(aid)
            self.assertIsNotNone(rec, msg=aid)
            if aid == "Ω.A.L4.P1.11":
                self.assertEqual(rec.status, AtomStatus.PENDING)
                continue
            self.assertEqual(
                rec.status,
                AtomStatus.OK,
                msg=f"{aid} status={rec.status} fail={rec.fail_code}",
            )
            self.assertIsNotNone(rec.started_at)
            self.assertIsNotNone(rec.ended_at)
            self.assertGreaterEqual(rec.attempt, 1)

    def test_p1_hand_actions_recorded(self):
        run_p0_p1_dry(self.store, self.deps)
        ops = [r.op for r in self.deps.hand.log]
        self.assertIn("tabs.select", ops)
        self.assertIn("double_click", ops)

    def test_job_json_persisted(self):
        run_p0_p1_dry(self.store, self.deps)
        path = self.store.paths.job_json
        self.assertTrue(os.path.isfile(path))
        with open(path, encoding="utf-8") as fh:
            raw = json.load(fh)
        self.assertIn("atoms", raw)
        self.assertEqual(raw["atoms"]["Ω.A.L4.P0.03"]["status"], "ok")

    def test_early_ok_skips_p1(self):
        pdf_path = plan_pdf_path(self._tmpdir.name, "20260630_DRE-01")
        with open(pdf_path, "wb") as handle:
            handle.write(b"%PDF-1.4\n")
        os.utime(pdf_path, (time.time(), time.time()))

        p0, p1 = run_p0_p1_dry(self.store, self.deps)
        self.assertTrue(p0.ok)
        self.assertTrue(p0.early_exit)
        self.assertTrue(p1.skipped)

        state = self.store.load()
        p005 = state.atoms.get("Ω.A.L4.P0.05")
        self.assertIsNotNone(p005)
        self.assertEqual(p005.fail_code, "EARLY_OK")
        p101 = state.atoms.get("Ω.A.L4.P1.01")
        if p101 is not None:
            self.assertEqual(p101.status, AtomStatus.PENDING)


class TestAtomRegistry(unittest.TestCase):
    def test_atom_id_lists(self):
        self.assertEqual(len(P0_ATOM_IDS), 6)
        self.assertEqual(len(P1_ATOM_IDS), 11)
        self.assertEqual(len(P0_P1_ATOM_IDS), 17)


if __name__ == "__main__":
    unittest.main()
