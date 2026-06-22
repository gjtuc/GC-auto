# -*- coding: utf-8 -*-
import os
import tempfile
import unittest

from gc_state import (
    mark_gc1_pdf_attempt_failed,
    mark_sequence_processed,
    should_retry_gc1_pdf,
)


class TestGcWatchGc1Retry(unittest.TestCase):
    def test_failed_pdf_not_retried_until_mtime_changes(self):
        with tempfile.TemporaryDirectory() as tmp:
            pdf = os.path.join(tmp, "sample.pdf")
            with open(pdf, "wb") as handle:
                handle.write(b"%PDF-1.4\n")
            state_path = os.path.join(tmp, ".gc_send_state.json")

            self.assertTrue(should_retry_gc1_pdf(state_path, pdf))

            mark_gc1_pdf_attempt_failed(state_path, pdf, "parse failed")
            self.assertFalse(should_retry_gc1_pdf(state_path, pdf))

            mark_sequence_processed(state_path, pdf, os.path.getmtime(pdf), "ok")
            self.assertFalse(should_retry_gc1_pdf(state_path, pdf))

            os.utime(pdf, None)
            self.assertTrue(should_retry_gc1_pdf(state_path, pdf))


if __name__ == "__main__":
    unittest.main()
