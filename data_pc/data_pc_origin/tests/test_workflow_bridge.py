# -*- coding: utf-8
import json
import tempfile
import unittest
from pathlib import Path

from data_pc_origin.o8_fixtures import OPJU_FX, fx_job_op_full
from data_pc_origin.o9_facade import update_from_dataframe
from data_pc_origin.p0_types import WorkflowMode
from data_pc_origin.p6_catalyst_adapter import load_catalyst_module
from data_pc_origin.workflow_bridge import (
    build_workflow_options,
    run_workflow_bridged,
)

_FIXTURE = Path(__file__).resolve().parent / "fixtures" / "catalyst_mock_module.py"


class TestWorkflowBridge(unittest.TestCase):
    def setUp(self) -> None:
        self._log: list[str] = []
        self._mod = load_catalyst_module(_FIXTURE)

    def _printer(self, msg: str) -> None:
        self._log.append(msg)

    def _origin(self, payload):
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

    def test_build_options(self) -> None:
        opts = build_workflow_options(opju_path=OPJU_FX)
        self.assertEqual(opts.opju_path, OPJU_FX)

    def test_write_workflow_bridge_smoke_artifact(self) -> None:
        fd, xlsx = tempfile.mkstemp(suffix=".xlsx")
        fd2, opju = tempfile.mkstemp(suffix=".opju")
        import os

        os.close(fd)
        os.close(fd2)
        try:
            calc_ok = run_workflow_bridged(
                xlsx,
                auto_archive=False,
                catalyst_module=self._mod,
                origin_runner=self._origin,
                printer=self._printer,
            )
            opju_ok = run_workflow_bridged(
                xlsx,
                opju_path=opju,
                skip_origin=True,
                catalyst_module=self._mod,
                origin_runner=self._origin,
                printer=self._printer,
            )
            out = {
                "hook": "run_workflow_bridged",
                "calc_only_ok": calc_ok,
                "opju_skip_ok": opju_ok,
                "log_has_stage2": any("[2단계]" in line for line in self._log),
                "mode_opju": WorkflowMode.OPJU_ONLY.value,
            }
            path = Path(__file__).resolve().parents[1] / "workflow_bridge_smoke.json"
            path.write_text(json.dumps(out, indent=2, ensure_ascii=False), encoding="utf-8")
            self.assertTrue(out["calc_only_ok"])
            self.assertTrue(out["opju_skip_ok"])
            self.assertTrue(out["log_has_stage2"])
        finally:
            Path(xlsx).unlink(missing_ok=True)
            Path(opju).unlink(missing_ok=True)


if __name__ == "__main__":
    unittest.main()
