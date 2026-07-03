# -*- coding: utf-8 -*-
"""G: .opju 감사 — Comments 열·데이터 행 수 vs G: xlsx."""

from __future__ import annotations

import os
import sys

import pandas as pd

SCRIPT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if SCRIPT_DIR not in sys.path:
    sys.path.insert(0, SCRIPT_DIR)

from data_pc_origin.o5_iterate import iter_pages_w
from data_pc_origin.o6_scan import iter_col_comments
from data_pc_origin.o5_text import compose_search_text
from data_pc_origin.o0_keys import normalize_origin_key

OPJUS = [
    (
        "630",
        r"G:\연구소\실험\실험데이터\촉매 반응\DRE 반응(C2H6)\20260630 DRE(1.5)@600 Ni5-Al2O3\20260630 DRE(1.5)@600 Ni5-Al2O3.opju",
        r"G:\연구소\실험\실험데이터\촉매 반응\DRE 반응(C2H6)\20260630 DRE(1.5)@600 Ni5-Al2O3\20260630 DRE(1.5)@600 Ni5-Al2O3.xlsx",
    ),
    (
        "701",
        r"G:\연구소\실험\실험데이터\촉매 반응\DRE 반응(C2H6)\20260701 DRE(1.5%)@600C Ni5-Ce5La0.25-Al2O3 (citric acid)\20260701 DRE(1.5%)@600C Ni5-Ce5La0.25-Al2O3 (citric acid).opju",
        r"G:\연구소\실험\실험데이터\촉매 반응\DRE 반응(C2H6)\20260701 DRE(1.5%)@600C Ni5-Ce5La0.25-Al2O3 (citric acid)\20260701 DRE(1.5%)@600C Ni5-Ce5La0.25-Al2O3 (citric acid).xlsx",
    ),
]

TARGET_SHEETS = ("h2 yield", "co2 conversion", "c2h6 conversion")


def count_col(wks, col):
    try:
        vals = list(wks.to_list(col))
    except Exception:
        return -1
    return sum(
        1
        for v in vals
        if v not in (None, "")
        and not (isinstance(v, str) and not str(v).strip())
    )


def _audit_opju(label: str, opju_path: str, xlsx_path: str, op) -> None:
    print(f"\n{'='*72}\n[{label}] {os.path.basename(opju_path)}\n{'='*72}")
    if not os.path.isfile(opju_path):
        print("  MISSING opju")
        return
    if not op.open(opju_path):
        print("  Origin open FAILED (Origin GUI 사용 중이면 닫고 재시도)")
        return

    xlsx_cycles = None
    co2_vals = None
    if os.path.isfile(xlsx_path):
        df = pd.read_excel(xlsx_path, index_col=0)
        xlsx_cycles = len(df)
        if "CO2 Area" in df.columns:
            co2_vals = df["CO2 Area"].head(3).tolist()
        print(f"  G: xlsx 사이클={xlsx_cycles}  CO2 Area 앞3={co2_vals}")

    found_any = False
    for book in iter_pages_w(op):
        for wks in book:
            text = normalize_origin_key(compose_search_text(book, wks))
            if not any(k in text for k in TARGET_SHEETS):
                continue
            found_any = True
            sheet_label = compose_search_text(book, wks)[:60]
            print(f"\n  시트: {sheet_label}")
            for col_idx, comment in iter_col_comments(wks):
                if not comment.strip():
                    continue
                c = comment.replace("\n", " ")[:90]
                if not any(
                    tok in c
                    for tok in (
                        "20260630",
                        "20260701",
                        "Ni5-Al2O3",
                        "Ce5La0.25",
                        "Ni5-Ce5La",
                    )
                ):
                    continue
                nrows = count_col(wks, col_idx)
                flag = ""
                if xlsx_cycles and nrows not in (xlsx_cycles, 0):
                    if "20260630" in c and label == "630":
                        flag = f"  <-- xlsx({xlsx_cycles})와 불일치"
                    elif "20260701" in c and "Ce5La" in c and label == "701":
                        flag = f"  <-- xlsx({xlsx_cycles})와 불일치"
                    elif "peer" or True:
                        flag = f"  (peer/타시료 열)"
                print(f"    col{col_idx:2d} rows={nrows:3d}  {c}{flag}")

    if not found_any:
        print("  대상 시트(H2 yield 등) 없음")


def main() -> int:
    try:
        import originpro as op
    except ImportError:
        print("originpro 없음")
        return 1

    for label, opju, xlsx in OPJUS:
        _audit_opju(label, opju, xlsx, op)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
