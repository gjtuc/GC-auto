# -*- coding: utf-8 -*-
"""T12 — PART1 L2 + ERR design verification."""
from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MAIN = ROOT / "deploy" / "GC1_RUNTIME_DESIGN.md"
PART = ROOT / "deploy" / "GC1_RUNTIME_DESIGN_PART1_L2.md"

REQUIRED = (
    "§L2-G-EX",
    "§L2-G-ATOM",
    "§ERR",
    "E_P2_FOCUS",
    "E_PIPELINE_BUSY",
    "Ω.A.L2.GEX.07",
)


def main() -> int:
    if not PART.is_file():
        print(f"MISSING {PART}")
        return 1
    text = PART.read_text(encoding="utf-8")
    main_text = MAIN.read_text(encoding="utf-8") if MAIN.is_file() else ""
    missing = [s for s in REQUIRED if s not in text]
    err_codes = len(re.findall(r"^\| E_[A-Z0-9_]+ \|", text, re.MULTILINE))
    print(f"part={PART}")
    print(f"err_codes={err_codes} (expect >= 27)")
    print(f"main_links={'PART1_L2' in main_text}")
    if missing or err_codes < 27 or "PART1_L2" not in main_text:
        if missing:
            print("MISSING:", missing)
        return 1
    print("T12 verify OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
