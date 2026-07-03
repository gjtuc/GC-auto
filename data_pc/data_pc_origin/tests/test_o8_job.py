# -*- coding: utf-8 -*-
import json
import unittest
from pathlib import Path

from data_pc_origin.o8_context import build_context
from data_pc_origin.o8_fixtures import OPJU_FX, SAMPLE_JOB, fx_job_df_full, fx_job_op_full
from data_pc_origin.o8_job import run_sample_job


class TestO8Job(unittest.TestCase):
    def test_full_job(self) -> None:
        op, _ = fx_job_op_full()
        ctx = build_context(OPJU_FX, fx_job_df_full(), SAMPLE_JOB)
        res = run_sample_job(ctx, op=op, skip_gate=True)
        self.assertEqual(res.updated_count, 8)
        self.assertTrue(res.ok)

    def test_write_job_artifact(self) -> None:
        op, sheets = fx_job_op_full()
        ctx = build_context(OPJU_FX, fx_job_df_full(), SAMPLE_JOB)
        res = run_sample_job(ctx, op=op, skip_gate=True)
        write_cols = {w[0] for s in sheets for w in s.writes}
        out = {
            "updated": res.updated_count,
            "row_count": res.row_count,
            "col_idx": res.col_idx,
            "unique_write_cols": sorted(write_cols),
            "exit_called": len(op.exit_calls),
            "saved": op.save_calls,
        }
        p = Path(__file__).resolve().parent.parent / "o8_job_smoke.json"
        p.write_text(json.dumps(out, indent=2), encoding="utf-8")
        self.assertEqual(out["updated"], 8)
        self.assertEqual(len(out["unique_write_cols"]), 1)
        self.assertEqual(out["exit_called"], 1)


if __name__ == "__main__":
    unittest.main()
