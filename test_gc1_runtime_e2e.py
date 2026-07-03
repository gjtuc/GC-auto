# -*- coding: utf-8 -*-
"""
T63 — gc1_runtime E2E dry-run: P0→P9 전 phase·atom ``status=ok`` 시뮬레이션.

``AUTOCHRO_DRY_RUN=1`` + mock deps — pywinauto·Tesseract·실장비 불필요.
실행 검증: ``python -m unittest test_gc1_runtime_e2e -v``
또는 보조 스크립트: ``python scripts/run_gc1_runtime_e2e.py`` (T80, py_compile + unittest)

경로:
  1) ``layer4_job.run_export_phases`` (런타임 직접)
  2) ``gc_autochro.run_autochro_export`` + ``GC1_USE_RUNTIME=1`` (위임 스택)
"""
from __future__ import annotations

import json
import os
import tempfile
import unittest
from unittest import mock

from gc1_runtime.layer1_state import AtomStatus, JobPaths, StateStore
from gc1_runtime.layer4_atoms_p8_p9 import P0_P9_ATOM_IDS, P89Deps
from gc1_runtime.layer4_job import ExportJobContext, run_autochro_export, run_export_phases

# 설계 §JOB-JSON 필수 루트 필드 (T14)
_JOB_JSON_ROOT_KEYS = frozenset({
    "job_id",
    "started_at",
    "data_name",
    "pdf_path_planned",
    "prep_enabled",
    "phase_current",
    "resume_from",
    "force",
    "atoms",
})


def _make_e2e_deps(folder: str) -> P89Deps:
    """전 phase dry-run mock — MTD·ListView·Hancom save dialog 포함."""
    from gc1_runtime.layer0_ctl import ListViewGeom, TreeGeom
    from gc1_runtime.layer3_hand import HandActuator

    tick = {"t": 5000.0}

    def clock() -> float:
        return tick["t"]

    def sleep(sec: float) -> None:
        tick["t"] += sec

    mtd_path = os.path.join(folder, "20260630 분석방법.MTD")
    with open(mtd_path, "w", encoding="utf-8") as fh:
        fh.write("mtd")

    hand = HandActuator(send_keys_fn=lambda _k, **__: None)
    return P89Deps(
        dry_run=True,
        pdf_output_dir=folder,
        mtd_dir=folder,
        data_name="20260630_DRE-01",
        on_control_tab=True,
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


def assert_e2e_atoms_ok(
    state,
    *,
    verify_eye: bool = False,
) -> None:
    """
    E2E atom 검증 — 선택적 atom 은 설계대로 pending 허용.

    - P1.11: ``verify_eye=0`` 이면 STW 생략 → pending
    - P9.12: P9.11 성공 시 fallback 미실행 → pending
    """
    for aid in P0_P9_ATOM_IDS:
        rec = state.atoms.get(aid)
        if rec is None:
            # P9.12 — P9.11 성공 시 atom shell 미기록 (fallback 불필요)
            if aid == "Ω.A.L4.P9.12":
                p911 = state.atoms.get("Ω.A.L4.P9.11")
                if p911 and p911.status == AtomStatus.OK:
                    continue
            # P1.11 — verify_eye=0 이면 STW 없음
            if aid == "Ω.A.L4.P1.11" and not verify_eye:
                continue
            raise AssertionError(f"missing atom record: {aid}")
        if aid == "Ω.A.L4.P1.11" and not verify_eye:
            if rec.status in (AtomStatus.PENDING, AtomStatus.OK):
                continue
        if aid == "Ω.A.L4.P9.12":
            p911 = state.atoms.get("Ω.A.L4.P9.11")
            if p911 and p911.status == AtomStatus.OK and rec.status == AtomStatus.PENDING:
                continue
        if rec.status != AtomStatus.OK:
            raise AssertionError(f"{aid} status={rec.status.value}, expected ok")


class TestRuntimeE2EJobPhases(unittest.TestCase):
    """실행 검증 1 — ``run_export_phases`` 직접."""

    def setUp(self) -> None:
        self._tmpdir = tempfile.TemporaryDirectory()
        self.folder = self._tmpdir.name
        self.store = StateStore(JobPaths(self.folder))
        self.deps = _make_e2e_deps(self.folder)

    def tearDown(self) -> None:
        self._tmpdir.cleanup()

    def test_all_phases_ok_and_done(self):
        result = run_export_phases(self.store, self.deps, log_fn=lambda _m: None)
        self.assertTrue(result.ok, msg=result.message)
        self.assertEqual(len(result.outcomes), 10)
        self.assertTrue(all(o.ok for o in result.outcomes))

        state = self.store.load()
        self.assertEqual(state.phase_current, "DONE")
        assert_e2e_atoms_ok(state)

    def test_pdf_and_job_json_written(self):
        run_export_phases(self.store, self.deps, log_fn=lambda _m: None)
        state = self.store.load()
        self.assertTrue(os.path.isfile(state.pdf_path_planned))
        self.assertTrue(os.path.isfile(self.store.paths.job_json))

        with open(self.store.paths.job_json, encoding="utf-8") as fh:
            raw = json.load(fh)
        self.assertTrue(_JOB_JSON_ROOT_KEYS.issubset(raw.keys()))
        self.assertEqual(raw["phase_current"], "DONE")
        self.assertEqual(raw["atoms"]["Ω.A.L4.P9.14"]["status"], "ok")

    @mock.patch.dict(os.environ, {"GC1_AUTOCHRO_PREP_STEPS": "0"}, clear=False)
    def test_no_prep_still_completes(self):
        """prep=0 — P3~P6 skip, P7~P9 완료."""
        result = run_export_phases(self.store, self.deps, log_fn=lambda _m: None)
        self.assertTrue(result.ok, msg=result.message)
        state = self.store.load()
        self.assertEqual(state.phase_current, "DONE")
        assert_e2e_atoms_ok(state)


class TestRuntimeE2EAutochroStack(unittest.TestCase):
    """실행 검증 2 — ``gc_autochro`` → ``layer4_job`` 위임 스택."""

    def setUp(self) -> None:
        self._tmpdir = tempfile.TemporaryDirectory()
        self.send_state = os.path.join(self._tmpdir.name, "send_state.json")
        with open(self.send_state, "w", encoding="utf-8") as fh:
            fh.write("{}")

    def tearDown(self) -> None:
        self._tmpdir.cleanup()

    @mock.patch.dict(
        os.environ,
        {
            "GC1_USE_RUNTIME": "1",
            "AUTOCHRO_ENABLED": "1",
            "AUTOCHRO_DRY_RUN": "1",
            "GC1_AUTOCHRO_PREP_STEPS": "1",
            "GC1_RUNTIME_VERIFY_EYE": "0",
        },
        clear=False,
    )
    def test_autochro_runtime_dry_run_all_atoms_ok(self):
        folder = os.path.join(self._tmpdir.name, "pdf_out")
        os.makedirs(folder, exist_ok=True)
        crm = os.path.join(self._tmpdir.name, "20260629 dre(3) ni-ce-la.CRM")
        with open(crm, "w", encoding="utf-8") as fh:
            fh.write("crm")

        deps = _make_e2e_deps(folder)
        ctx = ExportJobContext(
            excel_output_dir=folder,
            send_state_path=self.send_state,
            force=True,
            deps=deps,
            log_fn=lambda _m: None,
        )
        env = {
            "AUTOCHRO_CRM_PATH": crm,
            "GC1_PDF_DIR": folder,
        }
        with mock.patch.dict(os.environ, env, clear=False):
            ok, pdf, msg = run_autochro_export(folder, self.send_state, force=True, job_ctx=ctx)

        self.assertTrue(ok, msg=msg)
        self.assertIsNotNone(pdf)
        self.assertTrue(os.path.isfile(pdf or ""))

        store = StateStore(JobPaths(folder))
        state = store.load()
        self.assertEqual(state.phase_current, "DONE")
        assert_e2e_atoms_ok(state)

    @mock.patch.dict(
        os.environ,
        {
            "GC1_USE_RUNTIME": "1",
            "AUTOCHRO_ENABLED": "1",
            "AUTOCHRO_DRY_RUN": "1",
        },
        clear=False,
    )
    def test_gc_autochro_entry_delegates_e2e(self):
        """``gc_autochro.run_autochro_export`` 진입 — 동일 E2E."""
        import gc_autochro

        folder = os.path.join(self._tmpdir.name, "pdf_out2")
        os.makedirs(folder, exist_ok=True)
        crm = os.path.join(self._tmpdir.name, "20260629 dre(3) ni-ce-la.CRM")
        with open(crm, "w", encoding="utf-8") as fh:
            fh.write("crm")
        deps = _make_e2e_deps(folder)
        env = {
            "AUTOCHRO_CRM_PATH": crm,
            "GC1_PDF_DIR": folder,
        }
        with mock.patch.dict(os.environ, env, clear=False):
            ok, pdf, _msg = gc_autochro.run_autochro_export(
                folder,
                self.send_state,
                force=True,
            )
        # gc_autochro 위임은 job_ctx 없이 minimal dry deps — phase 는 통과해야 함
        self.assertTrue(ok)
        store = StateStore(JobPaths(folder))
        state = store.load()
        self.assertEqual(state.phase_current, "DONE")


class TestRuntimeE2EAtomCount(unittest.TestCase):
    """정적 검증 — P0~P9 atom ID 레지스트리 개수 (설계 회귀)."""

    def test_p0_p9_registry_non_empty(self):
        self.assertGreater(len(P0_P9_ATOM_IDS), 50)
        self.assertEqual(len(P0_P9_ATOM_IDS), len(set(P0_P9_ATOM_IDS)))


if __name__ == "__main__":
    unittest.main()
