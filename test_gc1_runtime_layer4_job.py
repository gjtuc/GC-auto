# -*- coding: utf-8 -*-
"""T55 — gc1_runtime.layer4_job export 진입·resume·prep."""
from __future__ import annotations

import os
import tempfile
import unittest
from unittest import mock

from gc1_runtime.layer1_state import AtomStatus, JobPaths, JobState, StateStore
from gc1_runtime.layer4_atoms_p2_p3 import P3_ATOM_IDS
from gc1_runtime.layer4_atoms_p5_p7 import P6_ATOM_IDS, P7_ATOM_IDS
from gc1_runtime.layer4_atoms_p8_p9 import P0_P9_ATOM_IDS
from gc1_runtime.layer4_job import (
    ExportJobContext,
    apply_no_prep_skips,
    apply_resume_from,
    ensure_job_state,
    run_autochro_export,
    run_export_phases,
)


def _make_deps(folder: str):
    from gc1_runtime.layer0_ctl import ListViewGeom, TreeGeom
    from gc1_runtime.layer3_hand import HandActuator
    from gc1_runtime.layer4_atoms_p8_p9 import P89Deps

    tick = {"t": 5000.0}
    mtd_path = os.path.join(folder, "20260630 분석방법.MTD")
    with open(mtd_path, "w", encoding="utf-8") as fh:
        fh.write("mtd")

    def clock() -> float:
        return tick["t"]

    def sleep(sec: float) -> None:
        tick["t"] += sec

    hand = HandActuator(send_keys_fn=lambda k, **__: None)
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
        save_dialog_visible=lambda: True,
        print_wait_sec=5,
        write_pdf_on_save=True,
    )


class TestResumeAndPrep(unittest.TestCase):
    def setUp(self) -> None:
        self._tmpdir = tempfile.TemporaryDirectory()
        self.store = StateStore(JobPaths(self._tmpdir.name))

    def tearDown(self) -> None:
        self._tmpdir.cleanup()

    def test_resume_from_p4_03_marks_prior_ok(self):
        state = ensure_job_state(self.store, prep_enabled=True, force=False)
        state.resume_from = "Ω.A.L4.P4.03"
        self.store.save(state)
        apply_resume_from(self.store, self.store.load())
        state = self.store.load()
        idx = P0_P9_ATOM_IDS.index("Ω.A.L4.P4.03")
        for aid in P0_P9_ATOM_IDS[:idx]:
            rec = state.atoms[aid]
            self.assertEqual(rec.status, AtomStatus.OK, msg=aid)
            self.assertEqual(rec.probe_snapshot.get("skipped_reason"), "resume")

    def test_no_prep_skips_p3_p6_and_p7_01(self):
        state = ensure_job_state(self.store, prep_enabled=False, force=False)
        apply_no_prep_skips(self.store, state)
        state = self.store.load()
        for aid in P3_ATOM_IDS + P6_ATOM_IDS:
            self.assertEqual(state.atoms[aid].status, AtomStatus.OK, msg=aid)
            self.assertEqual(state.atoms[aid].probe_snapshot.get("skipped_reason"), "prep_disabled")
        self.assertEqual(state.atoms["Ω.A.L4.P7.01"].probe_snapshot.get("skipped_reason"), "prep_disabled")


class TestRunExportPhases(unittest.TestCase):
    def setUp(self) -> None:
        self._tmpdir = tempfile.TemporaryDirectory()
        self.store = StateStore(JobPaths(self._tmpdir.name))
        self.deps = _make_deps(self._tmpdir.name)

    def tearDown(self) -> None:
        self._tmpdir.cleanup()

    def test_full_phases_done(self):
        ensure_job_state(
            self.store,
            prep_enabled=True,
            force=False,
            data_name=self.deps.data_name,
            pdf_path_planned=os.path.join(self._tmpdir.name, "20260630_DRE-01.pdf"),
        )
        result = run_export_phases(self.store, self.deps)
        self.assertTrue(result.ok, msg=result.message)
        state = self.store.load()
        self.assertEqual(state.phase_current, "DONE")
        self.assertTrue(os.path.isfile(state.pdf_path_planned))

    def test_no_prep_completes(self):
        state = ensure_job_state(self.store, prep_enabled=False, force=False, data_name=self.deps.data_name)
        state.prep_enabled = False
        self.store.save(state)
        result = run_export_phases(self.store, self.deps)
        self.assertTrue(result.ok, msg=result.message)
        state = self.store.load()
        for aid in P3_ATOM_IDS:
            self.assertEqual(state.atoms[aid].probe_snapshot.get("skipped_reason"), "prep_disabled")
        # P7.02+ 는 실행됨
        self.assertEqual(state.atoms["Ω.A.L4.P7.02"].status, AtomStatus.OK)


class TestRunAutochroExportEntry(unittest.TestCase):
    def setUp(self) -> None:
        self._tmpdir = tempfile.TemporaryDirectory()
        self.send_state = os.path.join(self._tmpdir.name, "send_state.json")
        with open(self.send_state, "w", encoding="utf-8") as fh:
            fh.write("{}")

    def tearDown(self) -> None:
        self._tmpdir.cleanup()

    @mock.patch("gc_autochro.resolve_crm_path", return_value="")
    @mock.patch.dict(
        os.environ,
        {
            "AUTOCHRO_ENABLED": "1",
            "AUTOCHRO_DRY_RUN": "1",
            "AUTOCHRO_CRM_PATH": "",
            "AUTOCHRO_DATA_NAME": "",
            "GC1_PDF_DIR": "",
        },
        clear=False,
    )
    def test_entry_fails_without_crm_path(self, _mock_crm):
        ok, pdf, msg = run_autochro_export(self._tmpdir.name, self.send_state, force=False)
        self.assertFalse(ok)
        self.assertIn("미설정", msg)

    @mock.patch.dict(
        os.environ,
        {
            "AUTOCHRO_ENABLED": "1",
            "AUTOCHRO_DRY_RUN": "1",
            "AUTOCHRO_DATA_NAME": "20260630_DRE-01",
            "GC1_PDF_DIR": "",
            "GC1_AUTOCHRO_PREP_STEPS": "1",
        },
        clear=False,
    )
    def test_dry_run_force_with_injected_deps(self):
        folder = os.path.join(self._tmpdir.name, "pdf_out")
        os.makedirs(folder, exist_ok=True)
        crm = os.path.join(self._tmpdir.name, "20260630_DRE-01.CRM")
        with open(crm, "w", encoding="utf-8") as fh:
            fh.write("crm")

        env = os.environ.copy()
        env["AUTOCHRO_CRM_PATH"] = crm
        env["GC1_PDF_DIR"] = folder

        deps = _make_deps(folder)
        ctx = ExportJobContext(
            excel_output_dir=folder,
            send_state_path=self.send_state,
            force=True,
            deps=deps,
            log_fn=lambda _m: None,
        )
        with mock.patch.dict(os.environ, env, clear=False):
            ok, pdf, msg = run_autochro_export(folder, self.send_state, force=True, job_ctx=ctx)
        self.assertTrue(ok, msg=msg)
        self.assertIsNotNone(pdf)
        self.assertTrue(os.path.isfile(pdf or ""))

    @mock.patch.dict(
        os.environ,
        {
            "AUTOCHRO_ENABLED": "0",
        },
        clear=False,
    )
    def test_disabled_without_force(self):
        ok, pdf, msg = run_autochro_export(self._tmpdir.name, self.send_state, force=False)
        self.assertFalse(ok)
        self.assertEqual(msg, "AUTOCHRO_ENABLED=0")


if __name__ == "__main__":
    unittest.main()
