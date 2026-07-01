# -*- coding: utf-8 -*-
"""T54 — gc1_runtime.layer4_atoms_p8_p9 P8 print + P9 save dry-run."""
from __future__ import annotations

import json
import os
import tempfile
import unittest

from gc1_runtime.layer0_ctl import ListViewGeom, TreeGeom
from gc1_runtime.layer1_state import AtomStatus, JobPaths, StateStore
from gc1_runtime.layer4_atoms_p5_p7 import run_p0_p7_dry
from gc1_runtime.layer4_atoms_p8_p9 import (
    P89Deps,
    P8_ATOM_IDS,
    P8_P9_ATOM_IDS,
    P9_ATOM_IDS,
    poll_save_dialog,
    run_p0_p9_dry,
    run_p8_p9_dry,
    write_minimal_pdf,
)


def _make_p89_deps(folder: str) -> P89Deps:
    tick = {"t": 5000.0}
    save_visible = {"v": True}

    def clock() -> float:
        return tick["t"]

    def sleep(sec: float) -> None:
        tick["t"] += sec

    hand = __import__("gc1_runtime.layer3_hand", fromlist=["HandActuator"]).HandActuator(
        send_keys_fn=lambda k, **__: None,
    )
    mtd_path = os.path.join(folder, "20260630 분석방법.MTD")
    with open(mtd_path, "w", encoding="utf-8") as fh:
        fh.write("mtd")
    return P89Deps(
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
        save_dialog_visible=lambda: save_visible["v"],
        print_wait_sec=5,
        write_pdf_on_save=True,
    )


class TestPollSaveDialog(unittest.TestCase):
    def test_finds_dialog(self):
        tick = {"t": 0.0}

        def clock() -> float:
            return tick["t"]

        def sleep(sec: float) -> None:
            tick["t"] += sec

        found, timed_out = poll_save_dialog(
            is_visible=lambda: True,
            clock=clock,
            sleep=sleep,
            max_wait_sec=10.0,
        )
        self.assertTrue(found)
        self.assertFalse(timed_out)


class TestP89DryRun(unittest.TestCase):
    def setUp(self) -> None:
        self._tmpdir = tempfile.TemporaryDirectory()
        self.store = StateStore(JobPaths(self._tmpdir.name))
        self.deps = _make_p89_deps(self._tmpdir.name)

    def tearDown(self) -> None:
        self._tmpdir.cleanup()

    def test_p8_p9_after_p0_p7(self):
        run_p0_p7_dry(self.store, self.deps)
        p8, p9 = run_p8_p9_dry(self.store, self.deps)
        self.assertTrue(p8.ok and p9.ok)
        state = self.store.load()
        self.assertEqual(state.phase_current, "DONE")
        for aid in P8_P9_ATOM_IDS:
            if aid == "Ω.A.L4.P9.12":
                rec = state.atoms.get(aid)
                if rec and rec.status == AtomStatus.PENDING:
                    continue
            self.assertEqual(state.atoms[aid].status, AtomStatus.OK, msg=aid)

    def test_full_p0_p9_chain(self):
        outcomes = run_p0_p9_dry(self.store, self.deps)
        self.assertEqual(len(outcomes), 10)
        self.assertTrue(all(o.ok for o in outcomes))

    def test_pdf_file_created(self):
        run_p0_p9_dry(self.store, self.deps)
        state = self.store.load()
        self.assertTrue(os.path.isfile(state.pdf_path_planned))

    def test_print_and_save_logged(self):
        run_p0_p9_dry(self.store, self.deps)
        ops = [r.op for r in self.deps.hand.log]
        self.assertIn("print_confirm", ops)
        self.assertTrue(self.deps.export_recorded)

    def test_job_json_p9_14(self):
        run_p0_p9_dry(self.store, self.deps)
        with open(self.store.paths.job_json, encoding="utf-8") as fh:
            raw = json.load(fh)
        self.assertEqual(raw["atoms"]["Ω.A.L4.P9.14"]["status"], "ok")
        self.assertIn("export_pdf", raw["atoms"]["Ω.A.L4.P9.14"]["probe_snapshot"])


class TestWriteMinimalPdf(unittest.TestCase):
    def test_writes_readable_pdf(self):
        with tempfile.TemporaryDirectory() as folder:
            path = os.path.join(folder, "out.pdf")
            write_minimal_pdf(path)
            self.assertTrue(os.path.isfile(path))
            from gc1_runtime.layer3_file import pdf_is_readable

            self.assertTrue(pdf_is_readable(path))


class TestAtomRegistry(unittest.TestCase):
    def test_counts(self):
        self.assertEqual(len(P8_ATOM_IDS), 6)
        self.assertEqual(len(P9_ATOM_IDS), 14)


if __name__ == "__main__":
    unittest.main()
