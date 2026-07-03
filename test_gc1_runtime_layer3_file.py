# -*- coding: utf-8 -*-
"""T42 — gc1_runtime.layer3_file L0-PDF·Hancom·dialog FS·PAR.00 wrapper."""
from __future__ import annotations

import os
import tempfile
import unittest
from unittest.mock import MagicMock, patch

from gc1_runtime.layer3_file import (
    ExportFileRecord,
    FileActuator,
    PDF_MAGIC,
    close_all_hancom_windows,
    confirm_overwrite_if_present,
    file_glob_pdfs_sorted,
    file_makedirs,
    file_unlink,
    find_dialog_by_title_re,
    find_filename_edit,
    hancom_close_button_enabled,
    hancom_is_complete,
    hancom_progress_text,
    pdf_header_is_valid,
    pdf_is_locked,
    pdf_is_readable,
    pdf_page_count,
    pdf_path_isfile,
    pdf_path_mtime,
    pdf_read_prefix,
    pdf_stem_from_path,
    set_filename_in_dialog,
    wait_and_close_hancom_pdf,
    wait_for_pdf_file_ready,
)


class TestL0PdfLeaves(unittest.TestCase):
    def setUp(self) -> None:
        self._tmpdir = tempfile.TemporaryDirectory()
        self.folder = self._tmpdir.name

    def tearDown(self) -> None:
        self._tmpdir.cleanup()

    def test_isfile_mtime_read_prefix(self) -> None:
        path = os.path.join(self.folder, "sample.pdf")
        with open(path, "wb") as handle:
            handle.write(PDF_MAGIC + b"1.4\n%EOF")
        self.assertTrue(pdf_path_isfile(path))
        self.assertFalse(pdf_path_isfile(os.path.join(self.folder, "missing.pdf")))
        mtime = pdf_path_mtime(path)
        self.assertIsNotNone(mtime)
        prefix = pdf_read_prefix(path)
        self.assertIsNotNone(prefix)
        self.assertTrue(pdf_header_is_valid(prefix or b""))

    def test_header_is_valid(self) -> None:
        self.assertTrue(pdf_header_is_valid(b"%PDF-1.4"))
        self.assertFalse(pdf_header_is_valid(b"NOTPDF"))
        self.assertFalse(pdf_header_is_valid(b"%PD"))

    def test_is_locked_open_ok(self) -> None:
        path = os.path.join(self.folder, "open.pdf")
        with open(path, "wb") as handle:
            handle.write(b"x")
        self.assertFalse(pdf_is_locked(path))

    def test_page_count_and_readable_with_fitz(self) -> None:
        try:
            import fitz
        except ImportError:
            self.skipTest("pymupdf not installed")
        path = os.path.join(self.folder, "real.pdf")
        doc = fitz.open()
        doc.new_page()
        doc.save(path)
        doc.close()
        self.assertEqual(pdf_page_count(path), 1)
        self.assertTrue(pdf_is_readable(path))

    def test_readable_rejects_invalid_header(self) -> None:
        path = os.path.join(self.folder, "bad.pdf")
        with open(path, "wb") as handle:
            handle.write(b"not a pdf")
        self.assertFalse(pdf_is_readable(path))


class TestFsLeaves(unittest.TestCase):
    def setUp(self) -> None:
        self._tmpdir = tempfile.TemporaryDirectory()
        self.folder = self._tmpdir.name

    def tearDown(self) -> None:
        self._tmpdir.cleanup()

    def test_makedirs_and_stem(self) -> None:
        pdf_path = os.path.join(self.folder, "sub", "out.pdf")
        directory = file_makedirs(pdf_path)
        self.assertTrue(os.path.isdir(directory))
        self.assertEqual(pdf_stem_from_path(pdf_path), "out")
        self.assertEqual(pdf_stem_from_path("/x/NOEXT"), "NOEXT")

    def test_unlink(self) -> None:
        path = os.path.join(self.folder, "del.pdf")
        open(path, "wb").close()
        self.assertTrue(file_unlink(path))
        self.assertFalse(os.path.isfile(path))

    def test_glob_sorted(self) -> None:
        older = os.path.join(self.folder, "a.pdf")
        newer = os.path.join(self.folder, "b.pdf")
        for p in (older, newer):
            with open(p, "wb") as handle:
                handle.write(PDF_MAGIC)
        os.utime(older, (1, 1))
        os.utime(newer, (2, 2))
        found = file_glob_pdfs_sorted(self.folder)
        self.assertEqual(found[0], newer)


class TestDialogLeaves(unittest.TestCase):
    def test_find_filename_edit_prefers_pdf_text(self) -> None:
        edit_pdf = MagicMock()
        edit_pdf.window_text.return_value = "report.pdf"
        edit_other = MagicMock()
        edit_other.window_text.return_value = ""
        dlg = MagicMock()
        dlg.descendants.return_value = [edit_other, edit_pdf]
        picked = find_filename_edit(dlg)
        self.assertIs(picked, edit_pdf)

    def test_set_filename_uses_edit_text(self) -> None:
        edit = MagicMock()
        dlg = MagicMock()
        dlg.descendants.return_value = [edit]
        set_filename_in_dialog(dlg, "stem123", sleep=lambda _s: None)
        edit.set_edit_text.assert_called_once_with("stem123")

    def test_find_dialog_by_title_re(self) -> None:
        win = MagicMock(name="dlg")
        handles = iter([[99], []])

        def find_windows(**_kw):
            return next(handles)

        def connect(h: int):
            self.assertEqual(h, 99)
            return win

        tick = {"t": 0.0}

        def clock() -> float:
            return tick["t"]

        def sleep(sec: float) -> None:
            tick["t"] += sec

        found = find_dialog_by_title_re(
            r"Save",
            find_windows=find_windows,
            connect_window=connect,
            timeout=1.0,
            clock=clock,
            sleep=sleep,
        )
        self.assertIs(found, win)

    def test_confirm_overwrite_clicks_yes(self) -> None:
        btn = MagicMock()
        btn.exists.return_value = True
        dlg = MagicMock()
        dlg.child_window.return_value = btn
        logs: list[str] = []

        def find_windows(**_kw):
            return [1]

        def connect(_h: int):
            return dlg

        ok = confirm_overwrite_if_present(
            find_windows=find_windows,
            connect_window=connect,
            timeout=0.1,
            clock=lambda: 0.0,
            sleep=lambda _s: None,
            log_fn=logs.append,
        )
        self.assertTrue(ok)
        btn.click_input.assert_called_once()
        self.assertTrue(logs)


class TestHancomLeaves(unittest.TestCase):
    def test_progress_text_from_static(self) -> None:
        static = MagicMock()
        static.window_text.return_value = "3 / 10 페이지를 생성"
        win = MagicMock()
        win.descendants.side_effect = lambda class_name=None: (
            [static] if class_name == "Static" else []
        )
        self.assertEqual(hancom_progress_text(win), "3 / 10 페이지를 생성")

    def test_is_complete(self) -> None:
        static = MagicMock()
        static.window_text.return_value = "성공적으로 변환을 완료하였습니다"
        win = MagicMock()
        win.descendants.return_value = [static]
        self.assertTrue(hancom_is_complete(win))

    def test_close_button_enabled(self) -> None:
        btn = MagicMock()
        btn.exists.return_value = True
        btn.is_enabled.return_value = True
        win = MagicMock()
        win.child_window.return_value = btn
        self.assertTrue(hancom_close_button_enabled(win))

    def test_close_all_hancom_windows(self) -> None:
        btn = MagicMock()
        btn.exists.return_value = True
        btn.is_enabled.return_value = True
        win = MagicMock()
        win.child_window.return_value = btn
        static = MagicMock()
        static.window_text.return_value = "변환을 완료"
        win.descendants.return_value = [static]
        n = close_all_hancom_windows([win], sleep=lambda _s: None)
        self.assertEqual(n, 1)
        btn.click_input.assert_called()

    def test_wait_and_close_hancom_loop(self) -> None:
        btn = MagicMock()
        btn.exists.return_value = True
        btn.is_enabled.return_value = True
        win = MagicMock()
        win.child_window.return_value = btn
        static = MagicMock()
        static.window_text.return_value = "성공적으로 변환을 완료"
        win.descendants.return_value = [static]
        phase = {"n": 0}

        def get_windows():
            phase["n"] += 1
            return [win] if phase["n"] == 1 else []

        result = wait_and_close_hancom_pdf(
            hancom_wait_sec=5.0,
            get_hancom_windows=get_windows,
            clock=lambda: 0.0,
            sleep=lambda _s: None,
        )
        self.assertTrue(result.all_closed)
        self.assertFalse(result.timed_out)
        self.assertGreaterEqual(result.windows_seen, 1)


class TestWaitForPdfWrapper(unittest.TestCase):
    def test_delegates_to_gc_gc1(self) -> None:
        with patch("gc_gc1.wait_for_pdf_file_ready", return_value=True) as mock_wait:
            ok = wait_for_pdf_file_ready("/tmp/x.pdf", max_wait_sec=10.0)
        self.assertTrue(ok)
        mock_wait.assert_called_once()
        _, kwargs = mock_wait.call_args
        self.assertEqual(kwargs["max_wait_sec"], 10.0)

    def test_default_max_wait_from_config(self) -> None:
        with patch("gc_gc1.wait_for_pdf_file_ready", return_value=False) as mock_wait:
            wait_for_pdf_file_ready("/tmp/y.pdf")
        _, kwargs = mock_wait.call_args
        self.assertEqual(kwargs["max_wait_sec"], 90.0)


class TestFileActuator(unittest.TestCase):
    def test_record_export_and_makedirs(self) -> None:
        with tempfile.TemporaryDirectory() as folder:
            pdf_path = os.path.join(folder, "nested", "out.pdf")
            act = FileActuator()
            act.ensure_pdf_directory(pdf_path)
            rec = act.record_export(pdf_path, dir_created=True)
            self.assertIsInstance(rec, ExportFileRecord)
            self.assertEqual(rec.filename_stem, "out")
            self.assertTrue(os.path.isdir(os.path.dirname(pdf_path)))
            ops = [r.op for r in act.log]
            self.assertIn("makedirs", ops)
            self.assertIn("record_export", ops)

    def test_find_save_and_fill(self) -> None:
        dlg = MagicMock()
        edit = MagicMock()
        dlg.descendants.return_value = [edit]
        act = FileActuator(
            find_windows=lambda **_kw: [7],
            connect_window=lambda h: dlg,
            clock=lambda: 0.0,
            sleep=lambda _s: None,
        )
        found = act.find_save_dialog(timeout=0.1)
        self.assertIs(found, dlg)
        stem = act.fill_save_filename(dlg, r"C:\data\test.pdf")
        self.assertEqual(stem, "test")


if __name__ == "__main__":
    unittest.main()
