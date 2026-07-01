# -*- coding: utf-8 -*-
"""T11 — GC1_RUNTIME_DESIGN PART1 L0 leaf 검증."""
from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MAIN = ROOT / "deploy" / "GC1_RUNTIME_DESIGN.md"
PART = ROOT / "deploy" / "GC1_RUNTIME_DESIGN_PART1_L0.md"

REQUIRED_PART = (
    "§L0-WIFI",
    "§L0-WIN",
    "§L0-LV",
    "§L0-TR",
    "§L0-TAB",
    "§L0-DN",
    "§L0-MTD",
    "§L0-PDF",
    "§L0-SCR-H",
    "§L0-TASK",
    "§L0-FOCUS",
    "Ω.A.L0.SCR.H.",
    "TASK.verify_peak_table_has_data",
)


def main() -> int:
    if not PART.is_file():
        print(f"MISSING {PART}")
        return 1
    text = PART.read_text(encoding="utf-8")
    main_text = MAIN.read_text(encoding="utf-8") if MAIN.is_file() else ""
    missing = [s for s in REQUIRED_PART if s not in text]
    scr_h = len(re.findall(r"Ω\.A\.L0\.SCR\.H\.", text))
    print(f"part={PART}")
    print(f"scr_h_leaf_rows={scr_h} (expect >= 420)")
    print(f"main_links_PART1={'PART1_L0' in main_text}")

    if missing:
        print("MISSING:", ", ".join(missing))
        return 1
    if scr_h < 420:
        print("FAIL: SCR.H count")
        return 1
    if "PART1_L0" not in main_text:
        print("FAIL: main doc missing PART1 link")
        return 1
    print("T11 verify OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
