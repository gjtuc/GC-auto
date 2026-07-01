# -*- coding: utf-8 -*-
"""GC1 PDF 주입별 H2/CO 분류 및 trim 요약 (진단용)."""
from __future__ import annotations

import glob
import os
import sys

from gc_console import setup_console_encoding

setup_console_encoding()

from gc_gc1 import (  # noqa: E402
    _collect_gc1_cycles_from_pages,
    _merge_peak_continuation_pages,
    classify_gc1_injections,
    get_compound_area,
    parse_gc1_pdf_path,
    parse_pdf_page,
    resolve_gc1_pdf_dir,
)
from gc_profiles import resolve_profile


def _fmt_area(value) -> str:
    if value is None:
        return "-"
    return f"{float(value):.1f}"


def _default_pdf() -> str:
    profile = resolve_profile()
    pdf_dir = resolve_gc1_pdf_dir(
        type("Cfg", (), {"sequence_folder": None, "excel_output_dir": profile.excel_output_dir})()
    )
    pdfs = sorted(glob.glob(os.path.join(pdf_dir, "*.pdf")), key=os.path.getmtime, reverse=True)
    return pdfs[0] if pdfs else ""


def main() -> None:
    pdf_path = sys.argv[1] if len(sys.argv) > 1 else _default_pdf()
    if not pdf_path or not os.path.isfile(pdf_path):
        print(f"[오류] PDF 없음: {pdf_path or '(경로 미지정)'}")
        raise SystemExit(1)

    import fitz

    doc = fitz.open(pdf_path)
    pages = [parse_pdf_page(doc.load_page(i).get_text("text")) for i in range(doc.page_count)]
    doc.close()
    pages = _merge_peak_continuation_pages(pages)

    fid_raw, tcd_raw, _ = _collect_gc1_cycles_from_pages(pages)
    analyses = classify_gc1_injections(fid_raw, tcd_raw)
    report = parse_gc1_pdf_path(pdf_path)

    print(f"PDF: {pdf_path}")
    print(f"Total injections: {len(analyses)}")
    print()
    print(f"{'#':>3} {'H2 area':>12} {'CO area':>12} {'CO2 area':>12} {'classification':>16}")
    print("-" * 62)
    for item in analyses[:15]:
        co2 = get_compound_area(
            tcd_raw[item.injection - 1] if item.injection <= len(tcd_raw) else [],
            "CO2",
        )
        print(
            f"{item.injection:3d} {_fmt_area(item.h2_area):>12} "
            f"{_fmt_area(item.co_area):>12} {_fmt_area(co2):>12} "
            f"{item.classification:>16}"
        )
    if len(analyses) > 15:
        print(f"... ({len(analyses) - 15} more injections)")

    kept = max(len(report.fid_cycles), len(report.tcd_cycles))
    print()
    print("=== Trim summary ===")
    print(f"Total:           {report.total_injections}")
    print(f"Last incomplete: {report.skipped_last_incomplete_count}")
    print(f"Pre-reduction:   {report.skipped_pre_reduction_count}")
    print(f"Reduction:       {report.skipped_reduction_count}")
    print(f"Transition:      {report.skipped_transition_count}")
    print(f"First reaction:  {report.skipped_first_reaction_count}")
    print(f"Kept for Excel:  {kept}")


if __name__ == "__main__":
    main()
