# -*- coding: utf-8 -*-
"""
002F 롤오버 + 시퀀스 연결 검증 — PASS/FAIL 출력.

Chem32 실데이터에서 001F0199→002F0201 연결, 갭 2사이클(구 001F-only 정규식 11사이클 오류) 확인.

사용: python scripts/verify_002f_connection.py
"""
from __future__ import annotations

import io
import os
import re
import sys
import zipfile

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from gc_chem32 import (  # noqa: E402
    CHEM32_INJECTION_RE,
    _injection_analysis_timestamp,
    collect_reported_injections,
    detect_analysis_gaps,
    estimate_missing_cycles_floor,
    find_chem32_injection_folders,
    find_report_txt,
    median_injection_interval_sec,
    parse_report_injection_datetime,
)

SAMPLE = r"E:\Chem32_extracted\1\DATA\20260620 DRE(1.5) 600C Ni5_Ce5_Al2O3"
DEPLOY_ZIP = os.path.join(ROOT, "deploy", "GC3_chem32-gc-automation.zip")
OLD_RE = re.compile(r"^001F(\d+)\.D$", re.IGNORECASE)


def check(name: str, cond: bool, detail: str = "") -> bool:
    status = "PASS" if cond else "FAIL"
    suffix = f" — {detail}" if detail else ""
    print(f"[{status}] {name}{suffix}")
    return cond


def main() -> int:
    results: list[bool] = []

    results.append(check("repo regex matches 002F0201", bool(CHEM32_INJECTION_RE.match("002F0201.D"))))

    if os.path.isfile(DEPLOY_ZIP):
        with zipfile.ZipFile(DEPLOY_ZIP) as zf:
            txt = zf.read("gc_chem32.py").decode("utf-8", errors="replace")
        has_new = r"^(\d{3})F(\d+)\.D$" in txt
        has_old_only = r"^001F(\d+)\.D$" in txt and r"(\d{3})F" not in txt
        results.append(check("deploy zip has 002F regex", has_new and not has_old_only, DEPLOY_ZIP))
    else:
        results.append(check("deploy zip exists", False, DEPLOY_ZIP))

    if not os.path.isdir(SAMPLE):
        print("SKIP real-data checks — sample folder missing:", SAMPLE)
        return 0 if all(results) else 1

    seq = os.path.join(SAMPLE, "20260608 REACTION 2026-06-20 16-14-24")
    folders = [os.path.basename(p) for p in find_chem32_injection_folders(seq)]
    count_002 = sum(1 for f in folders if f.upper().startswith("002F"))
    results.append(
        check(
            "find_chem32_injection_folders includes 002F",
            count_002 >= 9,
            f"{count_002} x 002F*",
        )
    )

    old_visible = [f for f in folders if OLD_RE.match(f)]
    new_visible = [f for f in folders if CHEM32_INJECTION_RE.match(f)]
    results.append(
        check(
            "old 001F-only regex misses 002F",
            count_002 > 0 and count_002 == len(new_visible) - len(old_visible),
            f"old={len(old_visible)} new={len(new_visible)}",
        )
    )

    inj = collect_reported_injections(SAMPLE)
    labels = [os.path.basename(p) for p, _ in inj]
    seqs = [os.path.basename(s) for _, s in inj]

    def find_idx(folder_name: str, seq_contains: str | None = None) -> int | None:
        for i, (p, s) in enumerate(inj):
            if os.path.basename(p) == folder_name:
                if seq_contains is None or seq_contains in s:
                    return i
        return None

    i199 = find_idx("001F0199.D")
    i201 = find_idx("002F0201.D")
    i209 = find_idx("002F0209.D")
    i101_new = find_idx("001F0101.D", "2026-06-25 11-11-28")

    results.append(
        check(
            "001F0199 immediately before 002F0201",
            i199 is not None and i201 == i199 + 1,
            f"#{i199 + 1 if i199 is not None else '?'} -> #{i201 + 1 if i201 is not None else '?'}",
        )
    )
    results.append(
        check(
            "001F0199 and 002F0201 same REACTION folder",
            i199 is not None and i201 is not None and seqs[i199] == seqs[i201],
            seqs[i199][:48] if i199 is not None else "",
        )
    )
    results.append(
        check(
            "002F0209 before new-seq 001F0101",
            i209 is not None and i101_new is not None and i101_new == i209 + 1,
            f"#{i209 + 1 if i209 is not None else '?'} -> #{i101_new + 1 if i101_new is not None else '?'}",
        )
    )

    gaps, _interval = detect_analysis_gaps(SAMPLE)
    gap = None
    for g in gaps:
        if g.after_injection_index == 107 and g.before_injection_index == 108:
            gap = g
            break
    if gap is None and gaps:
        gap = gaps[0]

    if gap:
        hrs = gap.gap_sec / 3600
        after_lab = labels[gap.after_injection_index]
        before_lab = labels[gap.before_injection_index]
        results.append(check("gap is ~3h not ~12h", 2.0 <= hrs <= 5.0, f"{hrs:.2f}h"))
        results.append(check("gap missing_cycles is 2 not 11", gap.missing_cycles == 2, f"missing={gap.missing_cycles}"))
        results.append(check("gap after is 002F0209 not 001F0199", "002F0209" in after_lab, after_lab))
        results.append(
            check(
                "gap before is new-seq 001F0101",
                before_lab == "001F0101.D" and "2026-06-25" in inj[gap.before_injection_index][1],
                before_lab,
            )
        )
    else:
        results.append(check("gap detected at 108->109", False, f"gaps={len(gaps)}"))

    old_inj = [(p, s) for p, s in inj if OLD_RE.match(os.path.basename(p))]
    old_interval = median_injection_interval_sec(old_inj)
    old_gaps: list[tuple[str, str, int, float]] = []
    for pos in range(1, len(old_inj)):
        t0 = _injection_analysis_timestamp(old_inj[pos - 1][0])
        t1 = _injection_analysis_timestamp(old_inj[pos][0])
        if t0 and t1:
            gs = t1 - t0
            m, _ = estimate_missing_cycles_floor(gs, old_interval or 1)
            if m >= 2:
                old_gaps.append(
                    (os.path.basename(old_inj[pos - 1][0]), os.path.basename(old_inj[pos][0]), m, gs / 3600)
                )
    results.append(
        check(
            "OLD regex reproduces false ~11-cycle gap",
            any(m >= 10 for *_, m, _h in old_gaps),
            str(old_gaps[-1] if old_gaps else "none"),
        )
    )

    print("\n=== INJECTION CHAIN (rollover + new seq) ===")
    start = max(0, (i199 or 98) - 1)
    end = min(len(inj), (i101_new or 109) + 2)
    for i in range(start, end):
        p, s = inj[i]
        rep = find_report_txt(p)
        dt = parse_report_injection_datetime(rep) if rep else None
        when = dt.strftime("%Y-%m-%d %H:%M:%S") if dt else "?"
        mark = ""
        if i == i199:
            mark = "  <- rollover"
        if i == i101_new:
            mark = "  <- new REACTION seq"
        print(f"  #{i + 1:3d} {os.path.basename(p):12s} {when}{mark}")

    passed = sum(results)
    total = len(results)
    print(f"\n=== SUMMARY {passed}/{total} checks passed ===")
    return 0 if passed == total else 1


if __name__ == "__main__":
    raise SystemExit(main())
