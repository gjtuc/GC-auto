# -*- coding: utf-8 -*-
"""T10 — GC1_RUNTIME_DESIGN.md §Ω-1~4 + §B leaf 표 검증 (실행 검증)."""
from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DESIGN = ROOT / "deploy" / "GC1_RUNTIME_DESIGN.md"

REQUIRED = (
    "§Ω-1",
    "§Ω-2",
    "§Ω-3",
    "§Ω-4",
    "§B-IDENT",
    "§B-HOST",
    "§B-CFG",
    "§B-CFG-LEAF",
    "§B-STATE",
    "§B-CLK",
    "R/C 경계",
    "Ω.A.B.IDENT.01",
    "Ω.A.B.CLK.04",
)


def main() -> int:
    text = DESIGN.read_text(encoding="utf-8")
    missing = [s for s in REQUIRED if s not in text]
    cfg_leaves = len(re.findall(r"Ω\.A\.B\.CFG\.\d+[abcd]", text))
    ident_leaves = len(re.findall(r"Ω\.A\.B\.IDENT\.\d+", text))
    clk_leaves = len(re.findall(r"Ω\.A\.B\.CLK\.\d+", text))

    print(f"file={DESIGN}")
    print(f"cfg_leaf_ids={cfg_leaves} (expect 76)")
    print(f"ident_leaf_ids={ident_leaves} (expect 8)")
    print(f"clk_leaf_ids={clk_leaves} (expect 4)")

    if missing:
        print("MISSING sections:", ", ".join(missing))
        return 1
    if cfg_leaves != 76:
        print("FAIL: CFG leaf count")
        return 1
    if ident_leaves < 8 or clk_leaves < 4:
        print("FAIL: IDENT/CLK leaf count")
        return 1
    print("T10 verify OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
