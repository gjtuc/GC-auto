# -*- coding: utf-8 -*-
"""차완 PC GC 작업: Downloads 최신 xlsx -> 계산 -> kier 폴더 체인 -> Origin.

Repo: scripts/run_gc_chawan.py
운영: python scripts/run_gc_chawan.py  (chemstation-gc-automation 루트에서)
"""
from __future__ import annotations

import importlib.util
import json
import os
import re
import shutil
import sys
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


def latest_gc_xlsx(downloads: Path) -> Path | None:
    files = [
        p for p in downloads.glob("*.xlsx")
        if p.is_file() and not SKIP_XLSX.search(p.name)
    ]
    return max(files, key=lambda p: p.stat().st_mtime) if files else None


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
    script_dir, profile_path, downloads = resolve_paths()
    profile = load_profile(profile_path)
    xlsx = latest_gc_xlsx(downloads)
    if not xlsx:
        print("Downloads에 GC xlsx 없음")
        return 1

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
    experiment_base = mod.generate_experiment_basename(str(xlsx))
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
