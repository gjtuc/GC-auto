# -*- coding: utf-8 -*-
"""
gc_profiles.py — GC1 / GC2 / GC3 PC별 출력 폴더·핫스팟·모드

=============================================================================
[다른 PC에서 읽을 때 — 핵심]
=============================================================================

  **한 repo, PC마다 env 파일만 다름.** 코드 수정은 GitHub push, env는 각 PC 로컬.

  | PC   | env 경로                    | GC_INSTANCE | 핫스팟              |
  |------|-----------------------------|-------------|---------------------|
  | GC1  | Desktop\\박은규\\gc_automation.env | gc1         | iPhone              |
  | GC2  | Desktop\\KCH\\gc_automation.env    | gc2         | AndroidHotspot5841  |
  | GC3  | Desktop\\KCH\\gc_automation.env    | gc3         | AndroidHotspot5841  |

  GC1 → gc_autochro + gc_gc1 (PDF)
  GC2 → gc_chemstation (8860 acam)
  GC3 → gc_chem32 (Report.txt)

=============================================================================
[resolve_profile() 탐색 순서]
=============================================================================

  1) 환경변수 GC_INSTANCE / EXCEL_OUTPUT_DIR (env 로드 후)
  2) Desktop\\박은규\\gc_automation.env 존재 → GC1
  3) Desktop\\KCH\\gc_automation.env 존재 → GC2 또는 GC3 (env의 GC_INSTANCE)
  4) PROFILE_DEFAULTS 기본값

  확인: python gc_automation.py --show-profile

  PC 식별 JSON (선택): Desktop\\...\\machine_profile.json — docs/CODEBASE_GUIDE.md
"""

from __future__ import annotations

import os
import sys
from dataclasses import dataclass
from typing import Iterable, List, Optional

from gc_config import DEFAULT_CHEMSTATION_DATA, EXCEL_OUTPUT_DIR, REQUIRED_HOTSPOT_SSID

DESKTOP = os.path.join(os.path.expanduser("~"), "Desktop")
DEFAULT_GC1_OUTPUT = os.path.join(DESKTOP, "박은규")
DEFAULT_GC2_OUTPUT = EXCEL_OUTPUT_DIR

PROFILE_DEFAULTS = {
    # gc1 — 은규 PC (DESKTOP-MBGSSME 등). Autochro PDF 파이프라인.
    "gc1": {
        "output_dir": DEFAULT_GC1_OUTPUT,
        "hotspot": "iPhone",
        "chemstation_mode": "gc1",
    },
    # gc2 — 차헌 PC. Agilent 8860 ChemStation acam.
    "gc2": {
        "output_dir": DEFAULT_GC2_OUTPUT,
        "hotspot": REQUIRED_HOTSPOT_SSID,
        "chemstation_mode": "8860",
    },
    # gc3 — 차헌 PC. Chem32 Report.txt. env에서 GC_INSTANCE=gc3.
    "gc3": {
        "output_dir": DEFAULT_GC2_OUTPUT,
        "hotspot": REQUIRED_HOTSPOT_SSID,
        "chemstation_mode": "chem32",
    },
}


@dataclass(frozen=True)
class ResolvedProfile:
    gc_instance: str
    excel_output_dir: str
    required_ssid: str
    chemstation_mode: str
    env_file: Optional[str] = None


def script_dir() -> str:
    return os.path.dirname(os.path.abspath(__file__))


def _dedupe_paths(paths: Iterable[str]) -> List[str]:
    seen = set()
    out: List[str] = []
    for raw in paths:
        path = os.path.normpath(os.path.expanduser(raw))
        if path not in seen:
            seen.add(path)
            out.append(path)
    return out


def candidate_env_dirs(base_script_dir: str) -> List[str]:
    """gc_automation.env 탐색 순서 (첫 번째로 찾은 파일을 bootstrap_env 가 로드)."""
    dirs: List[str] = []

    explicit = os.getenv("EXCEL_OUTPUT_DIR", "").strip()
    if explicit:
        dirs.append(explicit)

    for folder_name in ("박은규", "KCH"):
        path = os.path.join(DESKTOP, folder_name)
        env_path = os.path.join(path, "gc_automation.env")
        if os.path.isfile(env_path):
            dirs.append(path)

    dirs.extend([DEFAULT_GC1_OUTPUT, DEFAULT_GC2_OUTPUT, base_script_dir])
    return _dedupe_paths(dirs)


def _load_env_file(path: str) -> bool:
    try:
        from dotenv import load_dotenv
    except ImportError:
        print("[오류] python-dotenv 미설치: pip install python-dotenv")
        return False
    load_dotenv(path, override=False)
    return True


def bootstrap_env(base_script_dir: str) -> tuple[str, Optional[str]]:
    """첫 번째 env 파일을 로드하고 출력 폴더 경로를 반환."""
    loaded_from: Optional[str] = None
    for base in candidate_env_dirs(base_script_dir):
        for name in (".env", "gc_automation.env"):
            path = os.path.join(base, name)
            if os.path.isfile(path):
                _load_env_file(path)
                loaded_from = path
                break
        if loaded_from:
            break
    return resolve_excel_output_dir(base_script_dir, loaded_from), loaded_from


def resolve_excel_output_dir(base_script_dir: str, loaded_env_file: Optional[str] = None) -> str:
    explicit = os.getenv("EXCEL_OUTPUT_DIR", "").strip()
    if explicit:
        return os.path.normpath(os.path.expanduser(explicit))
    if loaded_env_file:
        return os.path.dirname(os.path.abspath(loaded_env_file))
    instance = os.getenv("GC_INSTANCE", "").strip().lower()
    if instance == "gc1":
        return DEFAULT_GC1_OUTPUT
    return DEFAULT_GC2_OUTPUT


def resolve_gc_instance() -> str:
    instance = os.getenv("GC_INSTANCE", "").strip().lower()
    if instance in PROFILE_DEFAULTS:
        return instance
    output_dir = os.getenv("EXCEL_OUTPUT_DIR", "").strip()
    if output_dir.replace("\\", "/").endswith("/박은규") or output_dir.endswith("박은규"):
        return "gc1"
    if os.path.basename(resolve_excel_output_dir(script_dir())) == "박은규":
        return "gc1"
    return "gc2"


def resolve_required_hotspot(default: str = REQUIRED_HOTSPOT_SSID) -> str:
    for key in ("REQUIRED_HOTSPOT", "REQUIRED_HOTSPOT_SSID"):
        value = os.getenv(key, "").strip()
        if value:
            return value
    instance = resolve_gc_instance()
    return PROFILE_DEFAULTS.get(instance, PROFILE_DEFAULTS["gc2"])["hotspot"]


def resolve_chemstation_mode(default: str = "auto") -> str:
    env_mode = os.getenv("CHEMSTATION_MODE", "").strip().lower()
    if env_mode in ("chem32", "8860", "auto", "gc1"):
        return env_mode
    instance = resolve_gc_instance()
    if instance in PROFILE_DEFAULTS:
        return PROFILE_DEFAULTS[instance]["chemstation_mode"]
    return default


def resolve_profile(base_script_dir: Optional[str] = None) -> ResolvedProfile:
    base = base_script_dir or script_dir()
    output_dir, env_file = bootstrap_env(base)
    instance = resolve_gc_instance()
    return ResolvedProfile(
        gc_instance=instance,
        excel_output_dir=output_dir,
        required_ssid=resolve_required_hotspot(),
        chemstation_mode=resolve_chemstation_mode(),
        env_file=env_file,
    )


def paths_for_output_dir(output_dir: str) -> dict[str, str]:
    return {
        "send_state": os.path.join(output_dir, ".gc_send_state.json"),
        "watch_status_json": os.path.join(output_dir, ".gc_watch_status.json"),
        "watch_status_txt": os.path.join(output_dir, "GC_감시_상태.txt"),
        "watch_pid": os.path.join(output_dir, ".gc_watch.pid"),
    }


def print_output_dir_for_bat() -> None:
    profile = resolve_profile()
    sys.stdout.write(profile.excel_output_dir)


def print_profile_summary(profile: ResolvedProfile) -> None:
    print("[GC 프로필]")
    print(f"  인스턴스      : {profile.gc_instance}")
    print(f"  출력 폴더      : {profile.excel_output_dir}")
    print(f"  env 파일       : {profile.env_file or '(없음)'}")
    print(f"  핫스팟 SSID    : {profile.required_ssid}")
    print(f"  ChemStation 모드: {profile.chemstation_mode}")


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--print-output-dir":
        print_output_dir_for_bat()
    elif len(sys.argv) > 1 and sys.argv[1] == "--show-profile":
        print_profile_summary(resolve_profile())
    else:
        print_output_dir_for_bat()
