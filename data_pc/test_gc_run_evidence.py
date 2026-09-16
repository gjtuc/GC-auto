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

    def test_origin_step_keeps_sheet_and_traceback(self):
        ev.begin_run("origin")
        try:
            raise OSError("opju save locked")
        except OSError as exc:
            ev.origin_step(
                "save",
                False,
                sample="20260909 DRME.xlsx",
                opju=r"G:\연구소\a.opju",
                detail="저장 실패",
                sheet="H2 yield",
                col_idx=4,
                exc=exc,
            )
        lines = ev.origin_jsonl_path().read_text(encoding="utf-8").strip().splitlines()
        event = json.loads(lines[-1])
        self.assertEqual(event["step"], "save")
        self.assertFalse(event["ok"])
        self.assertEqual(event["sheet"], "H2 yield")
        self.assertEqual(event["col_idx"], 4)
        self.assertIn("opju save locked", event["traceback"])
        ev.close_run(False)


if __name__ == "__main__":
    unittest.main()
