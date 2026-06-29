# -*- coding: utf-8
import json
import unittest
from pathlib import Path

from data_pc_origin.o8_fixtures import OPJU_FX, fx_job_op_full
from data_pc_origin.o9_facade import update_from_dataframe
from data_pc_origin.p0_types import WorkflowOptions
from data_pc_origin.p6_catalyst_adapter import (
    CatalystLoadError,
    load_catalyst_module,
    run_workflow_with_catalyst,
)
from data_pc_origin.tests._helpers import WORKFLOW_TEST_ENV

_FIXTURE = Path(__file__).resolve().parent / "fixtures" / "catalyst_mock_module.py"


class TestP6CatalystAdapter(unittest.TestCase):
    def test_load_fixture(self) -> None:
        mod = load_catalyst_module(_FIXTURE)
        self.assertTrue(hasattr(mod, "process_excel"))

    def test_missing_script(self) -> None:
        with self.assertRaises(CatalystLoadError):
            load_catalyst_module(Path(r"G:\nope.py"))

    def test_write_p6_smoke_artifact(self) -> None:
        mod = load_catalyst_module(_FIXTURE)

        def origin(payload):
            op, _ = fx_job_op_full()
            return update_from_dataframe(
                payload.opju_path,
                payload.df,
                payload.sample_name,
                save_in_place=payload.save_in_place,
                identity_key=payload.identity_key,
                op=op,
                skip_gate=True,
                printer=lambda _m: None,
                log_fn=lambda _m: None,
            )

        res = run_workflow_with_catalyst(
            r"G:\in.xlsx",
            WorkflowOptions(),
            module=mod,
            origin_runner=origin,
            explicit_skip=False,
            environ=WORKFLOW_TEST_ENV,
        )
        out = {
            "fixture_loaded": True,
            "full_archive_ok": res.ok,
            "sheets_updated": (
                res.stage4.origin.sheets_updated
                if res.stage4 and res.stage4.origin
                else 0
            ),
            "catalyst_script": "tests/fixtures/catalyst_mock_module.py",
        }
        path = Path(__file__).resolve().parents[1] / "p6_adapter_smoke.json"
        path.write_text(json.dumps(out, indent=2, ensure_ascii=False), encoding="utf-8")
        self.assertTrue(out["full_archive_ok"])
        self.assertEqual(out["sheets_updated"], 8)


if __name__ == "__main__":
    unittest.main()
