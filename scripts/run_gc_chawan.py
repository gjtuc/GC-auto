# -*- coding: utf-8 -*-
"""차완 PC GC 작업: Downloads xlsx -> 계산 -> kier 폴더 체인 -> Origin.

파일 선택 (GC 작업 지시 시):
  - Downloads *.xlsx 중 GC 형식
  - 수정 시각이 **현재 기준 3시간 이내**
  - 그중 **가장 최근** 1개
  - 없으면 exit 3 (사용자에게 파일 확인 요청)
  - 브라우저 중복: ``파일 (1).xlsx`` 허용
  - GC2용: 파일명 끝 ``_DRM 장비`` ``_OCM 장비`` 등 **장비 표시 제거** 후 처리

수동 지정: ``python scripts/run_gc_chawan.py --file "C:\\...\\file.xlsx"``
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import os
import re
import shutil
import sys
from datetime import datetime, timedelta
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
DEFAULT_HOME = Path(os.environ.get("USERPROFILE", "")) / "gc-data-pc-chawan"
DEFAULT_DOWNLOADS = Path(os.environ.get("USERPROFILE", "")) / "Downloads"

ORIGIN_MAPPING = {
    "C2H6 Conversion (%)": "C2H6 conversion",
    "CH4 Conversion (%)": "CH4 conversion",
    "CO2 Conversion (%)": "CO2 conversion",
    "H2 Yield (%)": "H2 yield",
    "CO Yield (%)": "CO yield",
    "CH4 (%)": "CH4",
    "C2H4 (%)": "C2H4",
    "C2H6 (%)": "C2H6",
}

SKIP_XLSX = re.compile(r"계산완료|Raman|특허|KIPRIS|~\$", re.I)
# GC2 실험 KCH xlsx — 반응 키워드 (파일명 또는 시트)
GC_REACTION = re.compile(r"\b(DRE|DRM|DRME)\b", re.I)
# 다운로드 중복: "sample (1).xlsx"
DOWNLOAD_DUP = re.compile(r"\s*\(\d+\)$")
# GC2 장비 PC가 붙이는 접미사: _DRM 장비, _OCM 장비, _DRE 장비 …
EQUIPMENT_TAG = re.compile(r"_(?:DRM|DRE|DRME|OCM)\s*장비\s*$", re.I)

FRESH_HOURS = 3
EXIT_NEED_FILE = 3


def resolve_paths() -> tuple[Path, Path, Path]:
    """(script_dir, profile_path, downloads_dir)."""
    home = Path(os.environ.get("GC_CHAWAN_HOME", DEFAULT_HOME))
    profile = home / "KCH" / "machine_profile.json"
    downloads = DEFAULT_DOWNLOADS
    if profile.is_file():
        with open(profile, encoding="utf-8-sig") as f:
            prof = json.load(f)
        paths = prof.get("paths") or {}
        if paths.get("script_dir"):
            home = Path(paths["script_dir"])
            profile = home / "KCH" / "machine_profile.json"
        if paths.get("downloads_inbox"):
            downloads = Path(paths["downloads_inbox"])
    script = home / "촉매 반응 계산.py"
    if not script.is_file():
        raise FileNotFoundError(
            f"촉매 반응 계산.py 없음: {script}\n"
            "docs/차완PC_Cursor_시작.md §2 설치 참고"
        )
    return home, profile, downloads


def load_profile(profile_path: Path) -> dict:
    if not profile_path.is_file():
        raise FileNotFoundError(f"machine_profile 없음: {profile_path}")
    with open(profile_path, encoding="utf-8-sig") as f:
        return json.load(f)


def load_catalyst(script_dir: Path):
    script = script_dir / "촉매 반응 계산.py"
    sys.path.insert(0, str(script_dir))
    spec = importlib.util.spec_from_file_location("catalyst_calc", script)
    mod = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(mod)
    return mod


def normalize_gc_stem(stem: str) -> str:
    """브라우저 (1) 접미사·장비 표시(_DRM 장비 등) 제거."""
    s = DOWNLOAD_DUP.sub("", stem.strip())
    s = EQUIPMENT_TAG.sub("", s)
    return s.strip()


def is_gc_xlsx_candidate(path: Path) -> bool:
    if not path.is_file() or path.suffix.lower() != ".xlsx":
        return False
    if SKIP_XLSX.search(path.name):
        return False
    stem = normalize_gc_stem(path.stem)
    if GC_REACTION.search(stem):
        return True
    # 파일명에 반응 없어도 KCH 시트 형식이면 허용
    try:
        import pandas as pd

        xls = pd.ExcelFile(path)
        for sn in xls.sheet_names[:3]:
            df = pd.read_excel(xls, sheet_name=sn, nrows=5)
            if df.empty:
                continue
            cols = {str(c).strip() for c in df.columns}
            if "Time" in cols and ("Area" in cols or "#" in cols):
                return True
    except Exception:
        pass
    return False


def list_download_candidates(downloads: Path) -> list[Path]:
    return sorted(
        [p for p in downloads.glob("*.xlsx") if is_gc_xlsx_candidate(p)],
        key=lambda p: p.stat().st_mtime,
        reverse=True,
    )


def select_fresh_xlsx(
    downloads: Path,
    *,
    now: datetime | None = None,
    fresh_hours: float = FRESH_HOURS,
) -> tuple[Path | None, list[Path], list[Path]]:
    """(선택 파일, 3h 이내 목록, 전체 GC 후보 목록)."""
    now = now or datetime.now()
    cutoff = now - timedelta(hours=fresh_hours)
    all_cands = list_download_candidates(downloads)
    fresh = [p for p in all_cands if datetime.fromtimestamp(p.stat().st_mtime) >= cutoff]
    if not fresh:
        return None, fresh, all_cands
    return max(fresh, key=lambda p: p.stat().st_mtime), fresh, all_cands


def stage_normalized_xlsx(source: Path, work_dir: Path) -> Path:
    """정규화된 파일명으로 inbox 스테이징 (계산·폴더명에 장비 접미사 미반영)."""
    work_dir.mkdir(parents=True, exist_ok=True)
    clean_stem = normalize_gc_stem(source.stem)
    dest = work_dir / f"{clean_stem}{source.suffix}"
    shutil.copy2(source, dest)
    return dest


def format_mtime(path: Path) -> str:
    return datetime.fromtimestamp(path.stat().st_mtime).strftime("%Y-%m-%d %H:%M:%S")


def report_no_fresh_file(all_cands: list[Path], fresh_hours: float) -> None:
    print(f"Downloads에 최근 {fresh_hours:g}시간 이내 수정된 GC xlsx 가 없습니다.")
    print("어떤 파일로 작업할지 알려 주세요. (예: --file \"C:\\Users\\User\\Downloads\\....xlsx\")")
    if all_cands:
        print("\n[Downloads GC xlsx 목록 — 수정 시각]")
        for p in all_cands[:15]:
            print(f"  - {p.name}  ({format_mtime(p)})")
    else:
        print("\n[Downloads] GC 형식 xlsx 후보 없음")


def norm_key(text: str) -> str:
    return re.sub(r"[\s_\-°º/]+", "", (text or "").lower())


def find_latest_folder(root: Path) -> Path | None:
    if not root.is_dir():
        return None
    folders = [
        root / name
        for name in os.listdir(root)
        if (root / name).is_dir() and not name.startswith(".")
    ]
    return max(folders, key=lambda p: p.name) if folders else None


def resolve_seed_opju(profile: dict, reaction: str) -> Path | None:
    paths = profile.get("paths") or {}
    key = f"origin_seed_{reaction.lower()}"
    for c in (paths.get(key), paths.get("origin_seed_dre") if reaction.upper() == "DRE" else None):
        if c and Path(c).is_file():
            return Path(c)
    return None


def copy_experiment_chain(
    reaction: str,
    experiment_base: str,
    calc_xlsx: Path,
    profile: dict,
) -> tuple[Path, Path, Path]:
    roots = profile.get("reaction_roots") or {}
    root = Path(roots[reaction.upper()])
    root.mkdir(parents=True, exist_ok=True)
    dest = root / experiment_base
    latest = find_latest_folder(root)
    seed_opju = resolve_seed_opju(profile, reaction)

    if dest.exists():
        print(f"[3] 기존 폴더 갱신: {dest}")
    elif latest and latest.name != experiment_base:
        print(f"[3] 최신 폴더 복사: {latest.name} -> {experiment_base}")
        shutil.copytree(latest, dest)
        old_stem = None
        for p in dest.iterdir():
            if p.suffix.lower() == ".opju" and "_updated" not in p.name.lower():
                old_stem = p.stem
                break
        if old_stem and old_stem != experiment_base:
            for p in list(dest.iterdir()):
                if p.stem == old_stem:
                    p.rename(dest / f"{experiment_base}{p.suffix}")
        for p in list(dest.iterdir()):
            if p.name.lower().endswith("_updated.opju") or "계산완료" in p.name:
                try:
                    p.unlink()
                except OSError:
                    pass
    elif seed_opju:
        print(f"[3] Origin 초안 시드 -> 첫 폴더: {seed_opju.name}")
        dest.mkdir(parents=True, exist_ok=True)
        shutil.copy2(seed_opju, dest / f"{experiment_base}.opju")
    else:
        print(f"[3] 시드 없음 — 빈 폴더: {experiment_base}")
        dest.mkdir(parents=True, exist_ok=True)

    dest_xlsx = dest / f"{experiment_base}.xlsx"
    shutil.copy2(calc_xlsx, dest_xlsx)
    opju = dest / f"{experiment_base}.opju"
    if not opju.is_file():
        for p in dest.glob("*.opju"):
            if "_updated" not in p.name.lower():
                opju = p
                break
    return dest, opju, dest_xlsx


def update_origin(opju: Path, df, sample_name: str) -> int:
    import originpro as op

    op.set_show(True)
    op.open(str(opju))
    updated = 0
    for df_col, keyword in ORIGIN_MAPPING.items():
        if df_col not in df.columns:
            continue
        nk = norm_key(keyword)
        target = None
        for book in op.pages("w"):
            for wks in book:
                s = norm_key(f"{book.name} {getattr(book, 'lname', '')} {wks.name}")
                if nk in s:
                    target = wks
                    break
            if target:
                break
        if not target:
            continue
        col_idx = int(target.cols)
        if col_idx > 0:
            try:
                last = col_idx - 1
                cm = target.get_label(last, "Comments") or ""
                data0 = target.to_list(last) or []
                empty = (not cm) and not any(
                    str(v).strip() not in ("", "nan", "None") for v in data0[:3]
                )
                if empty:
                    col_idx = last
            except Exception:
                pass
        if col_idx >= int(target.cols):
            target.cols = col_idx + 1
        target.from_list(col_idx, df[df_col].astype(float).tolist(), comments=sample_name)
        updated += 1
        print(f"  Origin OK: {keyword} col {col_idx}")
    if updated:
        op.save(str(opju))
    return updated


def main() -> int:
    parser = argparse.ArgumentParser(description="차완 PC GC 작업")
    parser.add_argument(
        "--file",
        help="Downloads 자동 선택 대신 지정 xlsx (3시간 초과 파일은 사용자 확인 후)",
    )
    parser.add_argument(
        "--fresh-hours",
        type=float,
        default=FRESH_HOURS,
        help=f"Downloads 자동 선택 시 수정 시각 허용 범위 (기본 {FRESH_HOURS}h)",
    )
    args = parser.parse_args()

    script_dir, profile_path, downloads = resolve_paths()
    profile = load_profile(profile_path)

    if args.file:
        xlsx_raw = Path(args.file)
        if not xlsx_raw.is_file():
            print(f"파일 없음: {xlsx_raw}")
            return 1
        if not is_gc_xlsx_candidate(xlsx_raw):
            print(f"GC xlsx 형식이 아님: {xlsx_raw.name}")
            return 1
        print(f"[수동] 지정 파일: {xlsx_raw.name}")
    else:
        xlsx_raw, fresh, all_cands = select_fresh_xlsx(
            downloads, fresh_hours=args.fresh_hours
        )
        if xlsx_raw is None:
            report_no_fresh_file(all_cands, args.fresh_hours)
            return EXIT_NEED_FILE
        print(
            f"[자동] {args.fresh_hours:g}h 이내 {len(fresh)}개 중 최신: "
            f"{xlsx_raw.name} ({format_mtime(xlsx_raw)})"
        )

    staging = script_dir / "KCH" / "inbox"
    xlsx = stage_normalized_xlsx(xlsx_raw, staging)
    if xlsx.stem != normalize_gc_stem(xlsx_raw.stem):
        print(f"     정규화 파일명: {xlsx.name}  (원본: {xlsx_raw.name})")

    mod = load_catalyst(script_dir)
    print("=" * 60)
    print("차완 PC GC 작업")
    print(f"입력: {xlsx.name}")
    print(f"DRE root: {profile.get('reaction_roots', {}).get('DRE')}")
    print("=" * 60)

    df_final, saved_excel, warnings, feed_desc = mod.process_excel(str(xlsx))
    if df_final is None:
        print("계산 실패")
        for w in warnings:
            print(" -", w)
        return 1

    eq = mod.equipment_from_output_file(saved_excel)
    sample_result = mod.generate_sample_name(str(xlsx), equipment=eq)
    sample_name = sample_result[0] if isinstance(sample_result, tuple) else sample_result
    # Origin Comments 에도 장비 접미사 제거 (GC2 전용)
    sample_name = EQUIPMENT_TAG.sub("", sample_name).strip()
    experiment_base = mod.generate_experiment_basename(str(xlsx))
    experiment_base = normalize_gc_stem(experiment_base)
    reaction = mod.reaction_type_from_output_file(saved_excel)

    print(f"장비: {eq} | 반응: {reaction}")
    print(f"Feed: {feed_desc}")
    print(f"계산: {saved_excel}")
    print(f"실험 폴더: {experiment_base}")
    for w in warnings:
        print("경고:", w)

    calc_path = Path(saved_excel)
    dest, opju, dest_xlsx = copy_experiment_chain(
        reaction, experiment_base, calc_path, profile
    )
    print(f"[3] 폴더: {dest}")
    print(f"     xlsx: {dest_xlsx.name}")
    print(f"     opju: {opju.name if opju.is_file() else 'NONE'}")

    processed = script_dir / "KCH" / "processed"
    processed.mkdir(parents=True, exist_ok=True)
    shutil.copy2(calc_path, processed / calc_path.name)

    if opju.is_file():
        print("[4] Origin 반영...")
        n = update_origin(opju, df_final, sample_name)
        print(f"[4] Origin 워크시트 {n}개 저장")
    else:
        print("[4] Origin 파일 없음 - 건너뜀")

    print("PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
