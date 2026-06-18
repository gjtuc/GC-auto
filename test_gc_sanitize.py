"""GC sanitize 단위 테스트 — python -m unittest test_gc_sanitize"""
import os
import tempfile
import unittest

from gc_sanitize import (
    InvalidSampleNameError,
    InvalidSequenceFolderError,
    build_safe_output_filename,
    sanitize_sample_name,
    validate_sequence_folder,
)


class TestGcSanitize(unittest.TestCase):
    def test_valid_sample_name(self):
        self.assertEqual(sanitize_sample_name(' DRME 600C Ni '), 'DRME 600C Ni')

    def test_rejects_traversal(self):
        with self.assertRaises(InvalidSampleNameError):
            sanitize_sample_name(r'foo\..\..\evil')
        with self.assertRaises(InvalidSampleNameError):
            sanitize_sample_name('..\\secret')

    def test_sequence_folder_under_data_path(self):
        with tempfile.TemporaryDirectory() as tmp:
            data = os.path.join(tmp, 'Data')
            seq = os.path.join(data, 'SEQ-001')
            os.makedirs(seq)
            out = validate_sequence_folder(seq, data)
            self.assertEqual(out, os.path.normpath(seq))
            outside = os.path.join(tmp, 'outside')
            os.makedirs(outside)
            with self.assertRaises(InvalidSequenceFolderError):
                validate_sequence_folder(outside, data)

    def test_output_stays_under_kch(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = build_safe_output_filename(tmp, 'Ni10-Al2O3', '20260617')
            self.assertEqual(
                os.path.normpath(path),
                os.path.normpath(os.path.join(tmp, '20260617 Ni10-Al2O3.xlsx')),
            )
            with self.assertRaises(InvalidSampleNameError):
                build_safe_output_filename(tmp, r'foo\..\..\evil', '20260617')


if __name__ == '__main__':
    unittest.main()
