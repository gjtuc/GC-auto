# -*- coding: utf-8 -*-
"""T13 — PART2 L4 P0~P4 full 7-field registry verification."""
from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MAIN = ROOT / "deploy" / "GC1_RUNTIME_DESIGN.md"
PART = ROOT / "deploy" / "GC1_RUNTIME_DESIGN_PART2_L4_P0_P4.md"

EXPECTED_ATOMS = 36


def main() -> int:
    if not PART.is_file():
        print(f"MISSING {PART}")
        return 1
    text = PART.read_text(encoding="utf-8")
    main_text = MAIN.read_text(encoding="utf-8") if MAIN.is_file() else ""
    atoms = re.findall(r"^### (Ω\.A\.L4\.P[0-4]\.\d+)", text, re.MULTILINE)
    registry_rows = len(re.findall(r"^\| Ω\.A\.L4\.P[0-4]\.", text, re.MULTILINE))
    has_pre = text.count("pre_probe") >= EXPECTED_ATOMS
    has_post = text.count("post_probe") >= EXPECTED_ATOMS
    linked = "PART2_L4_P0_P4" in main_text
    print(f"part={PART}")
    print(f"atom_headers={len(atoms)} (expect {EXPECTED_ATOMS})")
    print(f"registry_rows={registry_rows}")
    print(f"main_links={linked}")
    if len(atoms) != EXPECTED_ATOMS or not has_pre or not has_post or not linked:
        return 1
    print("T13 verify OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
