# -*- coding: utf-8 -*-
"""Generate SCR.H leaf table for GC1_RUNTIME_DESIGN_PART1_L0.md"""
from pathlib import Path

regions = [
    "autochro_window",
    "bottom_tabs",
    "left_analysis_tree",
    "top_sample_table",
    "bottom_peak_table",
    "bottom_peak_table_fine",
    "chromatogram_center",
]
stages = ["full", "panel", "fine"]
steps = [
    ("G", "01", "FS.load config"),
    ("G", "02", "PURE parent chain"),
    ("G", "03", "PURE abs box"),
    ("G", "04", "CMP min size"),
    ("C", "01", "PROC mss.grab"),
    ("C", "02", "PURE ImageGrab fallback"),
    ("C", "03", "PURE rgb"),
    ("Z", "01", "CMP scale<=1 skip"),
    ("Z", "02", "PURE nw nh"),
    ("Z", "03", "PURE LANCZOS resize"),
    ("P", "01", "PURE grayscale"),
    ("P", "02", "PURE contrast 1.35"),
    ("O", "01", "FS tesseract"),
    ("O", "02", "PROC to_string"),
    ("O", "03", "PROC to_data"),
    ("O", "04a", "PURE strip"),
    ("O", "04b", "CMP empty skip"),
    ("O", "04c", "CMP conf<0"),
    ("O", "04d", "CMP conf<25"),
    ("O", "04e", "PURE token"),
]

lines = [
    "| leaf ID | region | stage | step | op |",
    "|---------|--------|-------|------|-----|",
]
count = 0
for ri, region in enumerate(regions, 1):
    for si, stage in enumerate(stages, 1):
        for letter, num, op in steps:
            leaf_id = f"Ω.A.L0.SCR.H.{ri:02d}{si}{letter}{num}"
            lines.append(f"| {leaf_id} | {region} | {stage} | {letter}{num} | {op} |")
            count += 1

out = Path(__file__).resolve().parents[1] / "deploy" / "_scr_h_table_snippet.md"
out.write_text("\n".join(lines) + "\n", encoding="utf-8")
print(f"wrote {count} rows to {out}")
