"""gc_autochro PDF 잠금·창 제목 매칭 단위 테스트 — python -m unittest test_gc_autochro_pdf"""
import os
import tempfile
import unittest
import unittest.mock

from gc_autochro import (
    _header_text_matches_column,
    _is_pdf_blocker_dialog,
    _neutral_list_coords,
    _neutral_x_frac_from_env,
    _required_selection_count,
    _window_title_matches_pdf,
    is_pdf_file_locked,
)


class TestGcAutochroPdf(unittest.TestCase):
    def test_is_pdf_blocker_acrobat_not_found(self):
        self.assertTrue(
            _is_pdf_blocker_dialog(
                "Acrobat Reader",
                "이 문서를 여는 과정에서 오류가 발생했습니다. 이 파일은 찾을 수 없습니다.",
            )
        )

    def test_is_pdf_blocker_ignores_unrelated(self):
        self.assertFalse(_is_pdf_blocker_dialog("메모장", "hello"))

    def test_header_matches_collection_time(self):
        self.assertTrue(_header_text_matches_column("수집 일시", ("수집 일시",)))

    def test_required_selection_count_for_large_list(self):
        self.assertEqual(_required_selection_count(200), 199)

    def test_neutral_x_frac_default_not_sample_amount_column(self):
        with unittest.mock.patch.dict(os.environ, {}, clear=True):
            self.assertLessEqual(_neutral_x_frac_from_env(), 0.72)

    def test_neutral_x_frac_clamps_high_values(self):
        with unittest.mock.patch.dict(os.environ, {"AUTOCHRO_LIST_NEUTRAL_X_FRAC": "0.90"}):
            self.assertEqual(_neutral_x_frac_from_env(), 0.72)

    def test_neutral_list_coords_targets_collection_datetime_column(self):
        class _Rect:
            def width(self):
                return 1000

            def height(self):
                return 200

        class _List:
            def rectangle(self):
                return _Rect()

        rel_x, rel_y = _neutral_list_coords(_List())
        self.assertLess(rel_x, 720)  # 0.72*1000 — 시료량 열(우측) 회피
        self.assertGreaterEqual(rel_x, 450)  # 0.45*1000
        self.assertGreaterEqual(rel_y, 28)

    def test_window_title_matches_basename(self):
        path = r"C:\out\260616 dre@(3) ni-ce.pdf"
        self.assertTrue(_window_title_matches_pdf("260616 dre@(3) ni-ce.pdf - 한컴 PDF", path))

    def test_window_title_matches_stem(self):
        path = r"C:\out\260616 dre@(3) ni-ce.pdf"
        self.assertTrue(_window_title_matches_pdf("260616 dre@(3) ni-ce", path))

    def test_window_title_no_match(self):
        path = r"C:\out\260616 dre@(3) ni-ce.pdf"
        self.assertFalse(_window_title_matches_pdf("한컴 PDF", path))

    def test_is_pdf_file_locked_missing(self):
        self.assertFalse(is_pdf_file_locked(r"C:\no\such\file.pdf"))

    def test_is_pdf_file_locked_unlocked(self):
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
            tmp.write(b"%PDF-1.4\n")
            path = tmp.name
        try:
            self.assertFalse(is_pdf_file_locked(path))
        finally:
            os.unlink(path)


if __name__ == "__main__":
    unittest.main()
