# -*- coding: utf-8 -*-
"""T14 — PART2 L4 P5~P9 + job JSON example verification."""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MAIN = ROOT / "deploy" / "GC1_RUNTIME_DESIGN.md"
PART = ROOT / "deploy" / "GC1_RUNTIME_DESIGN_PART2_L4_P5_P9.md"
JSON_EX = ROOT / "deploy" / "gc_autochro_job.example.json"

EXPECTED_ATOMS = 36
REQUIRED_JSON_KEYS = ("job_id", "atoms", "phase_current", "resume_from")


def main() -> int:
    if not PART.is_file() or not JSON_EX.is_file():
        print("MISSING part or json example")
        return 1
    text = PART.read_text(encoding="utf-8")
    main_text = MAIN.read_text(encoding="utf-8") if MAIN.is_file() else ""
    atoms = re.findall(r"^### (Ω\.A\.L4\.P[5-9]\.\d+)", text, re.MULTILINE)
    try:
        job = json.loads(JSON_EX.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        print("invalid json example")
        return 1
    missing_keys = [k for k in REQUIRED_JSON_KEYS if k not in job]
    has_l6 = "§L6 cross-ref" in text and "PART3_L6" in text
    linked = "PART2_L4_P5_P9" in main_text and "gc_autochro_job.example.json" in main_text
    print(f"part={PART}")
    print(f"atom_headers={len(atoms)} (expect {EXPECTED_ATOMS})")
    print(f"json_keys_ok={not missing_keys}")
    print(f"l6_crossref={has_l6}")
    print(f"main_links={linked}")
    if len(atoms) != EXPECTED_ATOMS or missing_keys or not has_l6 or not linked:
        if missing_keys:
            print("missing:", missing_keys)
        return 1
    print("T14 verify OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
