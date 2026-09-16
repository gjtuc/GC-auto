# -*- coding: utf-8 -*-
"""gc_run_evidence — 실행 기록이 파일로 남는지."""

import json
import os
import tempfile
import unittest

import gc_run_evidence as ev


class EvidenceTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        os.environ["DATA_PC_EVIDENCE_DIR"] = self.tmp.name
        ev._RUN_ID = None
        ev._WARN_COUNT = 0
        ev._FAIL_COUNT = 0

    def tearDown(self):
        os.environ.pop("DATA_PC_EVIDENCE_DIR", None)
        ev._RUN_ID = None
        self.tmp.cleanup()

    def test_stage_exception_and_warning_survive_close(self):
        ev.begin_run("test")
        ev.warn("yield", "수율 > 전환율", sample="20260909 DRE.xlsx")
        try:
            raise RuntimeError("origin save failed")
        except RuntimeError as exc:
            ev.record("origin", False, sample="20260909 DRE.xlsx", exc=exc)
        ev.record("receive", False, detail="NAVER_APP_PASSWORD=secret")
        ev.close_run(False, detail="done")

        lines = (ev.jsonl_path()).read_text(encoding="utf-8").strip().splitlines()
        events = [json.loads(line) for line in lines]
        self.assertEqual(events[0]["event"], "run_start")
        warn = next(e for e in events if e["event"] == "warn")
        self.assertIn("수율", warn["detail"])
        fail = next(e for e in events if e.get("stage") == "origin")
        self.assertEqual(fail["exc_type"], "RuntimeError")
        self.assertIn("origin save failed", fail["traceback"])
        redacted = next(e for e in events if e.get("stage") == "receive")
        self.assertEqual(redacted["detail"], "[redacted]")
        self.assertTrue(ev.latest_path().is_file())
        self.assertIsNone(ev.current_run_id())


if __name__ == "__main__":
    unittest.main()
