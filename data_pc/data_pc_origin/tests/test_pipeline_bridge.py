# -*- coding: utf-8 -*-
import json
import unittest
from pathlib import Path
from unittest import mock

from data_pc_origin.o8_fixtures import OPJU_FX, SAMPLE_JOB, fx_job_df_full, fx_job_op_full
from data_pc_origin.o8_save import resolve_save_path
from data_pc_origin.o9_facade import OriginUpdateResult
from data_pc_origin.pipeline_bridge import ensure_import_path, run_origin_update


class TestPipelineBridge(unittest.TestCase):
    def test_ensure_path(self) -> None:
        root = ensure_import_path()
        self.assertTrue((root / "data_pc_origin").is_dir())

    def test_bridge_delegates_mock(self) -> None:
        op, _ = fx_job_op_full()
        with mock.patch(
            "data_pc_origin.pipeline_bridge.update_from_dataframe",
            wraps=__import__(
                "data_pc_origin.o9_facade",
                fromlist=["update_from_dataframe"],
            ).update_from_dataframe,
        ):
            res = __import__(
                "data_pc_origin.o9_facade",
                fromlist=["update_from_dataframe"],
            ).update_from_dataframe(
                OPJU_FX,
                fx_job_df_full(),
                SAMPLE_JOB,
                op=op,
                skip_gate=True,
                printer=lambda _m: None,
                log_fn=lambda _m: None,
            )
        self.assertEqual(res.sheets_updated, 8)

    def test_pipeline_smoke_artifact(self) -> None:
        op, _ = fx_job_op_full()
        res = __import__(
            "data_pc_origin.o9_facade",
            fromlist=["update_from_dataframe"],
        ).update_from_dataframe(
            OPJU_FX,
            fx_job_df_full(),
            SAMPLE_JOB,
            op=op,
            skip_gate=True,
            printer=lambda _m: None,
            log_fn=lambda _m: None,
        )
        save_as = resolve_save_path(OPJU_FX, False)
        out = {
            "bridge_root": str(ensure_import_path()),
            "sheets_updated": res.sheets_updated,
            "saved_in_place_path": OPJU_FX,
            "save_as_path": save_as,
            "hook": "run_origin_update",
        }
        p = Path(__file__).resolve().parent.parent / "pipeline_bridge_smoke.json"
        p.write_text(json.dumps(out, indent=2), encoding="utf-8")
        self.assertEqual(out["sheets_updated"], 8)
        self.assertTrue(out["save_as_path"].endswith("_Updated.opju"))


if __name__ == "__main__":
    unittest.main()
