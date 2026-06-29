# -*- coding: utf-8 -*-
import json
import unittest
from pathlib import Path

from data_pc_origin.o8_fixtures import OPJU_FX, SAMPLE_JOB, fx_job_df_full, fx_job_op_full
from data_pc_origin.o9_facade import (
    LOG_PREFIX,
    facade_signature_param_names,
    origin_log,
    update_from_dataframe,
)


class TestO9Facade(unittest.TestCase):
    def test_signature_matches_catalyst(self) -> None:
        names = facade_signature_param_names()
        self.assertEqual(names[0], "opju_path")
        self.assertEqual(names[1], "df_data")
        self.assertEqual(names[2], "sample_name")

    def test_facade_full_mock(self) -> None:
        op, _ = fx_job_op_full()
        res = update_from_dataframe(
            OPJU_FX,
            fx_job_df_full(),
            SAMPLE_JOB,
            op=op,
            skip_gate=True,
            printer=lambda _m: None,
            log_fn=lambda _m: None,
        )
        self.assertTrue(res.ok)
        self.assertEqual(res.sheets_updated, 8)

    def test_write_facade_artifact(self) -> None:
        logs: list[str] = []
        printed: list[str] = []
        op, sheets = fx_job_op_full()
        res = update_from_dataframe(
            OPJU_FX,
            fx_job_df_full(),
            SAMPLE_JOB,
            op=op,
            skip_gate=True,
            printer=printed.append,
            log_fn=logs.append,
        )
        h2 = next(s for s in sheets if s.name == "H2yield")
        out = {
            "signature": list(facade_signature_param_names()),
            "sheets_updated": res.sheets_updated,
            "row_count": res.row_count,
            "ok": res.ok,
            "log_prefix_ok": all(l.startswith(LOG_PREFIX) for l in logs),
            "stage4_ok": any("[4단계]" in p for p in printed),
            "gap_99": h2.writes[0][1][99] if h2.writes else None,
            "gap_100": h2.writes[0][1][100] if h2.writes else None,
        }
        p = Path(__file__).resolve().parent.parent / "o9_facade_smoke.json"
        p.write_text(json.dumps(out, indent=2), encoding="utf-8")
        self.assertTrue(out["log_prefix_ok"])
        self.assertTrue(out["stage4_ok"])
        self.assertEqual(out["gap_99"], "")


if __name__ == "__main__":
    unittest.main()
