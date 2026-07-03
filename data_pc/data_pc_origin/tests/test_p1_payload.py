# -*- coding: utf-8 -*-
import json
import unittest
from pathlib import Path

from data_pc_origin.p0_types import Stage2Artifacts, WorkflowMode
from data_pc_origin.p1_payload import (
    assemble_stage2_metadata,
    build_payload_from_stage2,
    payload_mapping_col_count,
    skipped_mapping_columns,
)


class _FakeDf:
    columns = [
        "C2H6 Conversion (%)",
        "CO2 Conversion (%)",
        "H2 Yield (%)",
        "CO Yield (%)",
        "CH4 (%)",
        "C2H4 (%)",
    ]

    def __len__(self) -> int:
        return 108


class TestP1Payload(unittest.TestCase):
    def test_dre_partial_mapping(self) -> None:
        df = _FakeDf()
        self.assertEqual(payload_mapping_col_count(df), 6)
        self.assertEqual(len(skipped_mapping_columns(df)), 2)

    def test_build_payload_opju_only(self) -> None:
        art = Stage2Artifacts(_FakeDf(), r"G:\calc.xlsx")
        meta = assemble_stage2_metadata(
            sample_name="20260620 DRE",
            identity_key=("20260620", "dre"),
            saved_excel=r"G:\calc.xlsx",
        )
        p = build_payload_from_stage2(
            art,
            meta,
            opju_path=r"G:\t.opju",
            mode=WorkflowMode.OPJU_ONLY,
        )
        self.assertFalse(p.save_in_place)

    def test_write_p1_smoke_artifact(self) -> None:
        df = _FakeDf()
        out = {
            "mapping_cols": payload_mapping_col_count(df),
            "skipped": skipped_mapping_columns(df),
        }
        path = Path(__file__).resolve().parents[1] / "p1_payload_smoke.json"
        path.write_text(json.dumps(out, indent=2, ensure_ascii=False), encoding="utf-8")
        self.assertEqual(out["mapping_cols"], 6)
        self.assertIn("CH4 Conversion (%)", out["skipped"])


if __name__ == "__main__":
    unittest.main()
