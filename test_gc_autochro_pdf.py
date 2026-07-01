"""gc_autochro PDF 파일명 단위 테스트 — python -m unittest test_gc_autochro_pdf"""
import os
import tempfile
import unittest
import unittest.mock

from gc_autochro import (
    build_export_pdf_path,
    format_data_name_for_pdf_filename,
    load_autochro_config,
    parse_data_name_from_crm_path,
)


class TestParseDataNameFromCrmPath(unittest.TestCase):
    def test_full_documents_path(self):
        path = r"C:\Users\User\Documents\20260630dre(5)ni(환원)-ce.CRM"
        self.assertEqual(
            parse_data_name_from_crm_path(path),
            "20260630dre(5)ni(환원)-ce",
        )

    def test_basename_only(self):
        self.assertEqual(
            parse_data_name_from_crm_path("20260629 dre(3) ni-ce-la.CRM"),
            "20260629 dre(3) ni-ce-la",
        )

    def test_lowercase_extension(self):
        self.assertEqual(
            parse_data_name_from_crm_path(r"C:\Users\User\Documents\foo.crm"),
            "foo",
        )


class TestGcAutochroPdfFilename(unittest.TestCase):
    def test_pdf_filename_keeps_ui_title_verbatim(self):
        raw = "20260629 dre(3) ni-ce-la"
        self.assertEqual(format_data_name_for_pdf_filename(raw), raw)

    def test_pdf_filename_keeps_compact_tree_name(self):
        raw = "260616dre(3)ni-ce"
        self.assertEqual(format_data_name_for_pdf_filename(raw), raw)

    def test_pdf_filename_strips_crm_extension(self):
        self.assertEqual(
            format_data_name_for_pdf_filename("20260629 dre(3) ni-ce-la.CRM"),
            "20260629 dre(3) ni-ce-la",
        )

    def test_build_export_pdf_path_uses_verbatim_title(self):
        with tempfile.TemporaryDirectory() as tmp:
            with unittest.mock.patch.dict(
                os.environ,
                {"AUTOCHRO_CRM_PATH": os.path.join(tmp, "dummy.CRM")},
                clear=False,
            ):
                os.makedirs(tmp, exist_ok=True)
                with open(os.path.join(tmp, "dummy.CRM"), "w", encoding="utf-8") as fh:
                    fh.write("x")
                cfg = load_autochro_config(tmp)
                path = build_export_pdf_path(
                    cfg,
                    data_name_raw="20260629 dre(3) ni-ce-la",
                )
            self.assertEqual(
                os.path.basename(path),
                "20260629 dre(3) ni-ce-la.pdf",
            )


if __name__ == "__main__":
    unittest.main()
