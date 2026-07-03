# -*- coding: utf-8 -*-
"""Inspect GC3 xlsx gap row vs injection timeline."""
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

import pandas as pd
from gc_console import setup_console_encoding

setup_console_encoding()


def inspect_xlsx(path: str) -> None:
    print(f"\n=== {path} ===")
    for sheet in ("FID", "TCD"):
        df = pd.read_excel(path, sheet_name=sheet, header=None)
        blocks = []
        cur = None
        for i, row in df.iterrows():
            v0 = str(row.iloc[0]).strip() if pd.notna(row.iloc[0]) else ""
            if v0 == "#":
                if cur:
                    blocks.append(cur)
                cur = {"start_row": i + 1, "type": "header", "peaks": []}
            elif v0 == "중단":
                if cur:
                    blocks.append(cur)
                blocks.append(
                    {"start_row": i + 1, "type": "gap", "row": [str(x) for x in row]}
                )
                cur = None
            elif cur and cur.get("type") == "header" and v0.isdigit():
                sym = row.iloc[6] if len(row) > 6 else ""
                cur["peaks"].append({"rt": row.iloc[1], "sym": sym})
                if len(cur["peaks"]) == 1:
                    cur["first_sym"] = sym
        if cur:
            blocks.append(cur)

        data_blocks = [b for b in blocks if b.get("type") == "header" and b.get("peaks")]
        gaps = [b for b in blocks if b.get("type") == "gap"]
        print(f"{sheet}: {len(data_blocks)} injection blocks, {len(gaps)} gap row(s)")
        for g in gaps:
            r = g["row"]
            print(f"  gap @ row {g['start_row']}: Time={r[1]!r} Area={r[2]!r}")
            print(f"    Width={r[4]!r} Area%={r[5]!r} Symmetry={r[6]!r}")

        for bi, b in enumerate(data_blocks):
            sym = str(b.get("first_sym", ""))
            if any(
                x in sym
                for x in (
                    "2026-06-24 23",
                    "2026-06-25 00",
                    "2026-06-25 08",
                    "2026-06-25 11",
                )
            ):
                print(f"  block #{bi + 1} row {b['start_row']} sym={sym}")


if __name__ == "__main__":
    xlsx = sys.argv[1] if len(sys.argv) > 1 else r"E:\20260620 DRE(1.5) 600C Ni5_Ce5_Al2O3 (1).xlsx"
    inspect_xlsx(xlsx)
