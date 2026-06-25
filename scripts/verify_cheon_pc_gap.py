# -*- coding: utf-8 -*-
"""차헌 PC가 GC3 갭 행(중단)을 올바르게 파싱하는지 E2E 검증."""
from __future__ import annotations

import importlib.util
import os
import sys
import tempfile

import pandas as pd

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)
DATA_PC = os.path.join(ROOT, "data_pc")
if DATA_PC not in sys.path:
    sys.path.insert(0, DATA_PC)

from gc_console import setup_console_encoding

setup_console_encoding()

from gc_chem32 import (  # noqa: E402
    build_merged_injection_cycles,
    collect_reported_injections,
    detect_analysis_gaps,
    insert_analysis_gap_markers,
)
from gc_gap_contract import parse_gap_missing_cycles  # noqa: E402
from gc_kch import write_chem32_excel  # noqa: E402

SAMPLE = r"E:\Chem32_extracted\1\DATA\20260620 DRE(1.5) 600C Ni5_Ce5_Al2O3"
OLD_XLSX = r"C:\Users\User\Downloads\20260620 DRE(1.5) 600C Ni5_Ce5_Al2O3 (4).xlsx"


def _load_calc():
    path = os.path.join(DATA_PC, "촉매 반응 계산.py")
    spec = importlib.util.spec_from_file_location("catalyst_calc", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _read_sheet(xlsx: str, sheet: str) -> pd.DataFrame:
    df = pd.read_excel(xlsx, sheet_name=sheet, header=None)
    df.columns = ["#", "Time", "Area", "Height", "Width", "Area%", "Symmetry"]
    return df


def _find_gap_rows(df: pd.DataFrame) -> list[tuple[int, pd.Series]]:
    found = []
    for i, row in df.iterrows():
        if parse_gap_missing_cycles(row) is not None:
            found.append((int(i), row))
    return found


def check(name: str, cond: bool, detail: str = "") -> bool:
    status = "PASS" if cond else "FAIL"
    print(f"[{status}] {name}" + (f" — {detail}" if detail else ""))
    return cond


def verify_xlsx(calc, xlsx: str, *, expect_gap: bool, expect_missing: int | None) -> list[bool]:
    results: list[bool] = []
    print(f"\n=== 파일: {xlsx} ===")
    if not os.path.isfile(xlsx):
        results.append(check("파일 존재", False))
        return results

    for sheet in ("FID", "TCD"):
        df = _read_sheet(xlsx, sheet)
        gap_rows = _find_gap_rows(df)
        results.append(
            check(
                f"{sheet} 갭 행 존재",
                (len(gap_rows) > 0) if expect_gap else (len(gap_rows) == 0),
                f"{len(gap_rows)}개",
            )
        )
        if expect_gap and gap_rows:
            row = gap_rows[0][1]
            n_time = parse_gap_missing_cycles(row)
            results.append(
                check(
                    f"{sheet} parse_gap_missing_cycles(Time)",
                    n_time == expect_missing,
                    f"N={n_time}",
                )
            )
            results.append(
                check(
                    f"{sheet} Symmetry GC_GAP:N=",
                    f"GC_GAP:N={expect_missing}" in str(row.get("Symmetry", "")),
                    str(row.get("Symmetry", "")),
                )
            )
            area = str(row.get("Area", ""))
            results.append(
                check(
                    f"{sheet} Area 사람 읽기(공백·폴더)",
                    "공백" in area and "→" in area,
                    area[:80],
                )
            )

        df_p, warnings, gap_cycles = calc.parse_gc_sheet(
            df, sheet, "GC3", calc.GC3_TIME_TCD if sheet == "TCD" else calc.GC3_TIME_FID
        )
        if expect_gap and expect_missing is not None:
            results.append(
                check(
                    f"{sheet} gap_cycles 개수",
                    len(gap_cycles) == expect_missing,
                    f"{sorted(gap_cycles)}",
                )
            )
            results.append(
                check(
                    f"{sheet} 경고에 분석 공백",
                    any("분석 공백" in w for w in warnings),
                    warnings[0] if warnings else "(없음)",
                )
            )
            if gap_cycles:
                for cyc in gap_cycles:
                    if cyc in df_p.index:
                        h2 = df_p.loc[cyc, "H2 Area"] if "H2 Area" in df_p.columns else None
                        results.append(
                            check(
                                f"{sheet} Cycle {cyc} H2 NaN(갭 슬롯)",
                                pd.isna(h2) or h2 == 0,
                                str(h2),
                            )
                        )
        else:
            results.append(check(f"{sheet} gap_cycles 없음", len(gap_cycles) == 0, str(gap_cycles)))

    if expect_gap:
        df_t = _read_sheet(xlsx, "TCD")
        df_f = _read_sheet(xlsx, "FID")
        _, _, gap_t = calc.parse_gc_sheet(df_t, "TCD", "GC3", calc.GC3_TIME_TCD)
        _, _, gap_f = calc.parse_gc_sheet(df_f, "FID", "GC3", calc.GC3_TIME_FID)
        results.append(
            check(
                "FID/TCD gap_cycles 일치",
                gap_t == gap_f,
                f"TCD={sorted(gap_t)} FID={sorted(gap_f)}",
            )
        )
        # Cycle 번호 연속: 갭 직전·직후 실측
        df_p_t, _, _ = calc.parse_gc_sheet(df_t, "TCD", "GC3", calc.GC3_TIME_TCD)
        if gap_t:
            start_gap = min(gap_t)
            before = start_gap - 1
            after = max(gap_t) + 1
            if before in df_p_t.index and after in df_p_t.index:
                results.append(
                    check(
                        "갭 전후 실측 Cycle 존재",
                        df_p_t.loc[before, "H2 Area"] > 0 and df_p_t.loc[after, "H2 Area"] > 0,
                        f"before={before} after={after}",
                    )
                )
    return results


def main() -> int:
    calc = _load_calc()
    all_results: list[bool] = []

    # 1) 구 (4).xlsx — 갭 행 없음 (버그 시대)
    if os.path.isfile(OLD_XLSX):
        all_results.extend(verify_xlsx(calc, OLD_XLSX, expect_gap=False, expect_missing=None))
    else:
        print(f"\n[SKIP] 구 xlsx 없음: {OLD_XLSX}")

    # 2) 실데이터로 새 xlsx 생성 → 차헌 PC 파싱
    if not os.path.isdir(SAMPLE):
        print(f"\n[SKIP] Chem32 실데이터 없음: {SAMPLE}")
    else:
        fid, tcd, _, _, paths = build_merged_injection_cycles(SAMPLE)
        gaps, _ = detect_analysis_gaps(SAMPLE)
        all_inj = collect_reported_injections(SAMPLE)
        fid, tcd = insert_analysis_gap_markers(fid, tcd, paths, gaps, all_inj)
        missing = gaps[0].missing_cycles if gaps else None

        tmp = os.path.join(tempfile.gettempdir(), "gc3_gap_cheon_pc_verify.xlsx")
        write_chem32_excel(tmp, fid, tcd)
        print(f"\n[생성] {tmp} (주입 {len(fid)}개, 갭 N={missing})")
        all_results.extend(
            verify_xlsx(calc, tmp, expect_gap=True, expect_missing=missing)
        )

    passed = sum(all_results)
    total = len(all_results)
    print(f"\n=== 차헌 PC 갭 계약 검증 {passed}/{total} ===")
    return 0 if passed == total else 1


if __name__ == "__main__":
    raise SystemExit(main())
