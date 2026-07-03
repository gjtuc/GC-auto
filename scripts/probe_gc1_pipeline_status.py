# -*- coding: utf-8 -*-
"""probe_gc1_pipeline_status.py — GC1 파이프라인 상태 진단 (T94)

실장비 Autochro·메일 없이 **PDF parse + reaction gate** 만 실행.
환원 단계에서 force 전에 "데이터 없음이 정상인지" 확인할 때 사용.

Usage (repo 루트, GC1 장비 PC):
  python scripts/probe_gc1_pipeline_status.py
  python scripts/probe_gc1_pipeline_status.py --pdf "C:\\path\\report.pdf"
  python scripts/probe_gc1_pipeline_status.py --pretty

Exit:
  0 = has_reaction_data (엑셀 가능)
  2 = reduction_stage | trim_empty | no_peaks (진단용, 크래시 아님)
  1 = PDF 없음·파싱 예외
"""
from __future__ import annotations

import argparse
import json
import os
import sys

_REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _REPO not in sys.path:
    sys.path.insert(0, _REPO)

from gc1_reaction_gate import Gc1ReactionAvailability, classify_gc1_report  # noqa: E402
from gc1_runtime.layer0_ident import read_ident_snapshot  # noqa: E402
from gc_config import AppConfig  # noqa: E402
from gc_gc1 import find_active_pdf, parse_gc1_pdf_path  # noqa: E402
from gc_profiles import resolve_profile  # noqa: E402


def _exit_for_availability(avail: Gc1ReactionAvailability) -> int:
    if avail is Gc1ReactionAvailability.HAS_REACTION_DATA:
        return 0
    return 2


def main() -> int:
    parser = argparse.ArgumentParser(description="GC1 pipeline status (PDF + reaction gate)")
    parser.add_argument("--pdf", help="PDF path (default: active PDF in excel_output_dir)")
    parser.add_argument("--pretty", action="store_true", help="indented JSON")
    parser.add_argument("--skip-ready-wait", action="store_true", help="do not wait for PDF lock")
    args = parser.parse_args()

    ident = read_ident_snapshot()
    payload: dict = {"ident": ident.to_dict()}

    pdf_path = args.pdf
    if not pdf_path:
        profile = resolve_profile(_REPO)
        config = AppConfig(
            excel_output_dir=profile.excel_output_dir,
            chemstation_mode=profile.chemstation_mode,
        )
        pdf_path = find_active_pdf(config)

    if not pdf_path or not os.path.isfile(pdf_path):
        payload["error"] = "PDF not found"
        payload["hint"] = "Autochro export or place *.pdf in excel_output_dir"
        print(json.dumps(payload, ensure_ascii=False, indent=2 if args.pretty else None))
        return 2

    payload["pdf_path"] = pdf_path
    try:
        report = parse_gc1_pdf_path(
            pdf_path,
            quiet=True,
            skip_ready_wait=args.skip_ready_wait,
        )
    except Exception as exc:
        payload["error"] = f"parse failed: {exc}"
        print(json.dumps(payload, ensure_ascii=False, indent=2 if args.pretty else None))
        return 1

    gate = classify_gc1_report(report)
    payload["reaction_gate"] = gate.to_dict()
    print(json.dumps(payload, ensure_ascii=False, indent=2 if args.pretty else None))
    return _exit_for_availability(gate.availability)


if __name__ == "__main__":
    raise SystemExit(main())
