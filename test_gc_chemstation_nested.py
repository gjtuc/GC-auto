# -*- coding: utf-8 -*-
"""flat·중첩 ChemStation 시퀀스 레이아웃 인식 테스트."""
from __future__ import annotations

import os
import tempfile
import time
import unittest

from gc_chemstation import (
    find_injection_folders,
    find_sequence_folder,
    get_latest_injection_acam_mtime,
    get_latest_sequence_folder,
    resolve_sequence_work_folder,
)


def _touch_acam(injection_dir: str, *, mtime: float | None = None) -> str:
    os.makedirs(injection_dir, exist_ok=True)
    acam = os.path.join(injection_dir, "sequence.acam_")
    with open(acam, "wb") as handle:
        handle.write(b"<ACAML/>")
    if mtime is not None:
        os.utime(acam, (mtime, mtime))
    return acam


class TestNestedSequenceLayout(unittest.TestCase):
    def test_flat_layout_unchanged(self):
        with tempfile.TemporaryDirectory() as data:
            seq = os.path.join(data, "20251221 sequence 2026-07-01 10-00-07")
            inj = os.path.join(seq, "F-2026-07-01-10-00-07-sample.D")
            _touch_acam(inj)

            self.assertEqual(resolve_sequence_work_folder(seq), seq)
            self.assertEqual(find_injection_folders(seq), [inj])
            self.assertIsNotNone(get_latest_injection_acam_mtime(seq))
            self.assertEqual(get_latest_sequence_folder(data), seq)

    def test_nested_wrapper_resolves_to_inner_sequence(self):
        with tempfile.TemporaryDirectory() as data:
            wrapper = os.path.join(data, "20260710DRM(5)700CNi5-Al2O3")
            inner = os.path.join(wrapper, "20251221 sequence 2026-07-10 00-10-03")
            inj = os.path.join(inner, "F-2026-07-10-08-39-24-sample.D")
            _touch_acam(inj)

            self.assertEqual(resolve_sequence_work_folder(wrapper), inner)
            self.assertEqual(find_injection_folders(wrapper), [inj])
            self.assertEqual(find_injection_folders(inner), [inj])
            self.assertEqual(get_latest_sequence_folder(data), inner)

            found = find_sequence_folder(data, sequence_folder=wrapper)
            self.assertEqual(found, inner)

            found_date = find_sequence_folder(data, sequence_date="20260710")
            self.assertEqual(found_date, inner)

    def test_latest_prefers_newer_acam_across_flat_and_nested(self):
        with tempfile.TemporaryDirectory() as data:
            old_seq = os.path.join(data, "20251221 sequence 2026-07-01 10-00-07")
            old_inj = os.path.join(old_seq, "F-2026-07-01-10-00-07-old.D")
            _touch_acam(old_inj, mtime=time.time() - 86400)

            wrapper = os.path.join(data, "20260710DRM(5)700CNi5-Al2O3")
            inner = os.path.join(wrapper, "20251221 sequence 2026-07-10 00-10-03")
            new_inj = os.path.join(inner, "F-2026-07-10-09-26-45-new.D")
            _touch_acam(new_inj, mtime=time.time())

            # wrapper 폴더 mtime 이 더 오래돼도 acam 이 최신이면 nested 선택
            os.utime(wrapper, (time.time() - 3600, time.time() - 3600))
            self.assertEqual(get_latest_sequence_folder(data), inner)

    def test_has_new_data_sees_nested_acam(self):
        from gc_state import has_new_data_since_last_run, save_send_state

        with tempfile.TemporaryDirectory() as tmp:
            data = os.path.join(tmp, "Data")
            os.makedirs(data)
            wrapper = os.path.join(data, "20260710DRM(5)700CNi5-Al2O3")
            inner = os.path.join(wrapper, "20251221 sequence 2026-07-10 00-10-03")
            inj = os.path.join(inner, "F-2026-07-10-08-39-24-sample.D")
            acam = _touch_acam(inj, mtime=time.time())

            state_path = os.path.join(tmp, ".gc_send_state.json")
            save_send_state(
                state_path,
                {
                    "last_processed_acam_mtime": os.path.getmtime(acam) - 100,
                    "last_sequence_folder": os.path.join(data, "old"),
                },
            )
            self.assertTrue(
                has_new_data_since_last_run(state_path, wrapper, data, "8860")
            )
            self.assertTrue(
                has_new_data_since_last_run(state_path, inner, data, "8860")
            )


if __name__ == "__main__":
    unittest.main()
