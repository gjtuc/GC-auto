# -*- coding: utf-8
"""Updated opju — 지정 열·행에 테스트 값 1개씩 패치 (데이터 접근 유연성 데모).

관찰 (2026-06 live, Ni5 _Updated.opju · col 83):
  · 읽기: ``wks.cell(row, col)`` — 1-based 행.
  · 한 행 쓰기: ``from_list(col, [v], comments=…, start=row)`` — ``start`` = cell 행과 동일(1-based).
  · ``LT_execute`` 단일 셀 대입은 이 PC에서 불안정(크래시/미반영); ``from_list`` 사용.
  · 열 전체 live 쓰기(O7) 후 갭·마지막 행: 99–100 빈칸, 108행 ``--``, 실데이터는 ~107행까지인 경우 있음.
  · 109·111처럼 중간 행을 비운 채 ``start`` 만 찍으면, Origin ``SetData`` 가
    사이 빈 행(예: 110)을 이전 데이터 행(예: 101) 값으로 채울 수 있음 — 의도한 패치가 아니라 COM 쪽 부작용.
  · 일상 파이프라인(열 통째 1회 ``from_list``)과는 별개; 희소 행 패치 시에만 신경 쓰면 됨.
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from data_pc_origin.o3_session import OriginSession
from data_pc_origin.o5_iterate import iter_worksheets
from data_pc_origin.o5_text import wks_name
from data_pc_origin.o6_scan import iter_col_comments

DEFAULT_OPJU = (
    r"G:\연구소\실험\실험데이터\촉매 반응\DRE 반응(C2H6)"
    r"\20260626 DRE(1.5) 600C Ni5_Ce5_Al2O3_test"
    r"\20260626 DRE(1.5) 600C Ni5_Ce5_Al2O3_test_Updated.opju"
)
SAMPLE_MARK = "20260620"
DEFAULT_ROW_109 = (12345, 23451, 34512, 45123, 51234, 65432)
DEFAULT_ROW_111 = (1111, 2222, 3333, 4444, 5555, 6666)


@dataclass(frozen=True)
class PatchTarget:
    book: str
    sheet: str
    col: int
    comment: str


def find_patch_targets(op: Any, *, sample_mark: str = SAMPLE_MARK) -> List[PatchTarget]:
    """20260620 Comments 열이 있는 워크시트만 — 북/시트 순서대로."""
    targets: List[PatchTarget] = []
    for book, wks in iter_worksheets(op):
        for col, comment in iter_col_comments(wks):
            if sample_mark not in comment:
                continue
            targets.append(
                PatchTarget(
                    book=getattr(book, "name", ""),
                    sheet=wks_name(wks),
                    col=col,
                    comment=comment,
                )
            )
            break
    return targets


def write_single_row(wks: Any, col: int, row: int, value: float | int) -> None:
    """한 행만 기록 — ``from_list(..., start=row)`` (Origin 1-based row = start).

    행을 건너뛰고 여러 번 호출하면(예: 109·111만 기록) 그 사이 행이 Origin이
    알아서 채워질 수 있음 — 위 모듈 docstring 관찰 참고.
    """
    comment = wks.get_label(col, "C") or ""
    wks.from_list(col, [value], comments=comment, start=row)


def patch_row(
    opju_path: str,
    *,
    values: Tuple[int, ...],
    row: int,
    sample_mark: str = SAMPLE_MARK,
    save: bool = True,
) -> Dict[str, object]:
    """각 북·시트의 sample 열 `row`에 values 순서대로 1개씩 기록."""
    records: List[Dict[str, object]] = []
    with OriginSession() as op:
        op.open(opju_path)
        targets = find_patch_targets(op, sample_mark=sample_mark)
        if len(targets) != len(values):
            raise ValueError(
                f"expected {len(values)} sheets with {sample_mark!r}, found {len(targets)}"
            )

        wks_by_key: Dict[Tuple[str, str], Any] = {}
        for book, wks in iter_worksheets(op):
            wks_by_key[(getattr(book, "name", ""), wks_name(wks))] = wks

        for tgt, val in zip(targets, values):
            wks = wks_by_key[(tgt.book, tgt.sheet)]
            before = wks.cell(row, tgt.col)
            write_single_row(wks, tgt.col, row, val)
            after = wks.cell(row, tgt.col)
            records.append(
                {
                    "book": tgt.book,
                    "sheet": tgt.sheet,
                    "col": tgt.col,
                    "row": row,
                    "value": val,
                    "before": before,
                    "after": after,
                }
            )

        if save:
            op.save(opju_path)

    return {
        "status": "ok",
        "opju_path": opju_path,
        "row": row,
        "patches": records,
    }


def patch_row109(opju_path: str, **kwargs: object) -> Dict[str, object]:
    """하위 호환 — 109행 기본값."""
    return patch_row(
        opju_path,
        values=DEFAULT_ROW_109,
        row=109,
        **{k: v for k, v in kwargs.items() if k in ("sample_mark", "save")},
    )


def _artifact_name(row: int) -> str:
    return f"live_patch_row{row}_result.json"


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Updated opju 지정 행 패치")
    parser.add_argument("opju", nargs="?", default=DEFAULT_OPJU, help=".opju 경로")
    parser.add_argument("--row", type=int, default=109, help="1-based 행 (기본 109)")
    parser.add_argument(
        "--values",
        default="",
        help="쉼표 구분 값 (6개). 생략 시 row=111 → 1111..6666, row=109 → 12345..65432",
    )
    args = parser.parse_args(argv)

    if args.values.strip():
        values = tuple(int(x.strip()) for x in args.values.split(","))
    elif args.row == 111:
        values = DEFAULT_ROW_111
    elif args.row == 109:
        values = DEFAULT_ROW_109
    else:
        parser.error("--values required when --row is not 109 or 111")

    try:
        result = patch_row(args.opju, values=values, row=args.row)
    except Exception as exc:  # noqa: BLE001
        result = {
            "status": "error",
            "opju_path": args.opju,
            "row": args.row,
            "error": f"{type(exc).__name__}: {exc}",
        }

    artifact = Path(__file__).resolve().parent / _artifact_name(args.row)
    artifact.write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0 if result.get("status") == "ok" else 1


if __name__ == "__main__":
    raise SystemExit(main())
