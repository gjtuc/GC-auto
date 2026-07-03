# -*- coding: utf-8 -*-
import json
import unittest
from pathlib import Path

from data_pc_origin.p0_routing import resolve_workflow_mode
from data_pc_origin.p0_types import (
    Stage2Artifacts,
    WorkflowMode,
    WorkflowOptions,
    build_origin_payload,
)


class _FakeDf:
    columns = ["H2 Yield (%)", "CO2 Conversion (%)"]

    def __len__(self) -> int:
        return 108


class TestP0Workflow(unittest.TestCase):
    def test_resolve_opju_only(self) -> None:
        self.assertEqual(
            resolve_workflow_mode(WorkflowOptions(opju_path=r"G:\t.opju")),
            WorkflowMode.OPJU_ONLY,
        )

    def test_build_payload_save_as(self) -> None:
        art = Stage2Artifacts(_FakeDf(), r"G:\calc.xlsx")
        p = build_origin_payload(
            art,
            opju_path=r"G:\t.opju",
            sample_name="20260620 DRE",
            identity_key=("20260620", "dre"),
            mode=WorkflowMode.OPJU_ONLY,
        )
        self.assertFalse(p.save_in_place)

    def test_write_p0_smoke_artifact(self) -> None:
        out = {
            "mode_opju": resolve_workflow_mode(WorkflowOptions(opju_path="x.opju")).value,
            "mode_full": resolve_workflow_mode(WorkflowOptions()).value,
        }
        path = Path(__file__).resolve().parents[1] / "p0_workflow_smoke.json"
        path.write_text(json.dumps(out, indent=2), encoding="utf-8")
        self.assertEqual(out["mode_opju"], "opju_only")


if __name__ == "__main__":
    unittest.main()
