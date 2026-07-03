# -*- coding: utf-8 -*-
"""Report 수 vs 엑셀 주입 수 차이 — 단계별 탈락 원인 감사."""
from __future__ import annotations

import io
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from gc_console import setup_console_encoding

setup_console_encoding()

from gc_chem32 import (
    _filter_complete_injection_pairs,
    build_detector_cycles,
    collect_reported_injections,
    find_chem32_injection_folders,
    find_report_txt,
    find_sequence_folders,
    parse_injection_reports,
    build_merged_injection_cycles,
    insert_analysis_gap_markers,
    detect_analysis_gaps,
)


def find_sample(data_root: str) -> str:
    for dirpath, dirnames, _ in os.walk(data_root):
        for name in dirnames:
            if "Ni5_Ce5" in name or "Ni5_Ce5" in name.upper():
                return os.path.join(dirpath, name)
    raise FileNotFoundError(f"sample not under {data_root}")


def main() -> int:
    data_root = sys.argv[1] if len(sys.argv) > 1 else os.path.join(
        os.path.expanduser("~"), "Desktop", "DATA_extract"
    )
    sample = find_sample(data_root)
    print(f"[시료] {sample}\n")

    all_folders = []
    for seq in find_sequence_folders(sample):
        all_folders.extend(find_chem32_injection_folders(seq))
    with_report = [p for p in all_folders if find_report_txt(p)]
    print(f"1) 주입 폴더 총 {len(all_folders)}개, Report.TXT {len(with_report)}개")

    collected = collect_reported_injections(sample)
    print(f"2) collect_reported_injections {len(collected)}개")

    incomplete = []
    complete = []
    for path, seq in collected:
        rep = parse_injection_reports(path)
        fid_n = len(rep.get("FID", []))
        tcd_n = len(rep.get("TCD", []))
        label = os.path.basename(path)
        if fid_n and tcd_n:
            complete.append((path, seq, fid_n, tcd_n))
        else:
            incomplete.append((label, fid_n, tcd_n))

    complete_pairs, skip_inc = _filter_complete_injection_pairs(collected)
    print(f"3) FID+TCD 완료 쌍 {len(complete_pairs)}개, 미완료 제외 {skip_inc}개")
    if incomplete:
        print("   [미완료 목록]")
        for label, f, t in incomplete:
            print(f"     {label:14s} FID={f} TCD={t}")

    tcd_cycles, matched_paths, tcd_skip = build_detector_cycles(complete_pairs, "TCD")
    print(f"4) TCD sliding 통과 {len(matched_paths)}개, 제외 {tcd_skip}개")

  # sliding 실패 상세
    from itertools import groupby
    from gc_chem32 import _build_detector_cycles_chunk, describe_cycle_mismatch, cycles_match

    sliding_fail = []
    for seq_path, group in groupby(complete_pairs, key=lambda x: x[1]):
        chunk = list(group)
        tcd_c, paths_c, sk = _build_detector_cycles_chunk(chunk, "TCD")
        matched_set = set(paths_c)
        for path, _ in chunk:
            if path not in matched_set:
                rep = parse_injection_reports(path)
                sliding_fail.append((os.path.basename(path), len(rep.get("TCD", []))))

    if sliding_fail:
        print(f"   [TCD sliding 탈락 {len(sliding_fail)}개] (상세는 validate --audit)")
        for label, n in sliding_fail[:20]:
            print(f"     {label} ({n} peaks)")
        if len(sliding_fail) > 20:
            print(f"     ... 외 {len(sliding_fail)-20}개")

    fid, tcd, labels, skipped, paths = build_merged_injection_cycles(sample)
    gaps, _ = detect_analysis_gaps(sample)
    all_inj = collect_reported_injections(sample)
    fid2, tcd2 = insert_analysis_gap_markers(fid, tcd, paths, gaps, all_inj)

    print(f"5) build_merged 최종 FID/TCD {len(fid2)}개 (갭행 포함), skipped 합계 {skipped}")
    print(f"   갭 마커 {len(gaps)}구간, missing_cycles={sum(g.missing_cycles for g in gaps)}")
    print(f"\n=== 요약 ===")
    print(f"   Report {len(with_report)} → 완료쌍 {len(complete_pairs)} → TCD통과 {len(paths)} → 엑셀블록 {len(fid2)}")
    lost_report_to_complete = len(with_report) - len(complete_pairs)
    lost_complete_to_match = len(complete_pairs) - len(paths)
    print(f"   손실: 미완료 {lost_report_to_complete}, sliding {lost_complete_to_match}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
