# -*- coding: utf-8 -*-
"""
T61 — ``GC1_USE_RUNTIME`` 위임: 기본 0=legacy, 1=layer4_job.

실행: python -m unittest test_gc_autochro_runtime -v
"""
from __future__ import annotations

import os
import tempfile
import unittest
from unittest import mock

import gc_autochro


class TestGc1UseRuntimeSwitch(unittest.TestCase):
    def test_default_is_legacy_path(self):
        self.assertFalse(gc_autochro._gc1_use_runtime())

    @mock.patch.dict(os.environ, {"GC1_USE_RUNTIME": "1"}, clear=False)
    def test_env_enables_runtime(self):
        self.assertTrue(gc_autochro._gc1_use_runtime())

    @mock.patch("gc1_runtime.layer4_job.run_autochro_export")
    @mock.patch.dict(os.environ, {"GC1_USE_RUNTIME": "1", "AUTOCHRO_ENABLED": "1"}, clear=False)
    def test_runtime_flag_delegates_to_layer4_job(self, mock_runtime):
        mock_runtime.return_value = (True, "/tmp/x.pdf", "ok")
        ok, pdf, msg = gc_autochro.run_autochro_export("/out", "/state.json", force=True)
        self.assertTrue(ok)
        self.assertEqual(pdf, "/tmp/x.pdf")
        mock_runtime.assert_called_once()
        call_kw = mock_runtime.call_args.kwargs
        self.assertTrue(call_kw["force"])
        self.assertIsNotNone(call_kw.get("job_ctx"))

    @mock.patch("gc1_runtime.layer4_job.run_autochro_export")
    def test_legacy_dry_run_does_not_delegate(self, mock_runtime):
        with mock.patch.dict(
            os.environ,
            {"GC1_USE_RUNTIME": "0", "AUTOCHRO_ENABLED": "1", "AUTOCHRO_DRY_RUN": "1"},
            clear=False,
        ):
            with mock.patch("gc_autochro.resolve_crm_path", return_value="/x/a.CRM"):
                ok, pdf, msg = gc_autochro.run_autochro_export("/out", "/state.json", force=True)
        self.assertTrue(ok)
        self.assertEqual(msg, "dry-run")
        mock_runtime.assert_not_called()

    @mock.patch.dict(
        os.environ,
        {
            "GC1_USE_RUNTIME": "1",
            "AUTOCHRO_ENABLED": "1",
            "AUTOCHRO_DRY_RUN": "1",
            "AUTOCHRO_DATA_NAME": "20260629 dre(3) ni-ce-la",
        },
        clear=False,
    )
    def test_runtime_dry_run_end_to_end(self):
        """실행 검증 — gc_autochro → layer4_job → phase dry-run (pywinauto 불필요)."""
        folder = tempfile.mkdtemp()
        self.addCleanup(lambda: __import__("shutil").rmtree(folder, ignore_errors=True))
        crm = os.path.join(folder, "20260629 dre(3) ni-ce-la.CRM")
        with open(crm, "w", encoding="utf-8") as fh:
            fh.write("crm")
        send_state = os.path.join(folder, "send.json")
        with open(send_state, "w", encoding="utf-8") as fh:
            fh.write("{}")
        pdf_dir = os.path.join(folder, "pdf")
        os.makedirs(pdf_dir, exist_ok=True)
        env = {
            "AUTOCHRO_CRM_PATH": crm,
            "GC1_PDF_DIR": pdf_dir,
        }
        with mock.patch.dict(os.environ, env, clear=False):
            ok, pdf, msg = gc_autochro.run_autochro_export(pdf_dir, send_state, force=True)
        self.assertTrue(ok, msg=msg)
        self.assertIsNotNone(pdf)
        self.assertTrue(os.path.isfile(pdf or ""))


if __name__ == "__main__":
    unittest.main()
