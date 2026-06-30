# -*- coding: utf-8 -*-
"""
gc_profiles.py — GC1 / GC2 / GC3 **장비 PC**별 출력 폴더·핫스팟·모드

=============================================================================
[PC 명칭 — 오해 금지]  docs/PC_NAMING.md
=============================================================================

  이 모듈은 **장비 PC에서만** gc_automation.py 가 사용합니다.
  은규 PC / 차헌 PC(데이터 PC)에서는 import 되지 않습니다.

  | 연구원 | 장비 PC (본 모듈)        | 데이터 PC (별도)     |
  |--------|--------------------------|----------------------|
  | 은규   | GC1 장비 PC              | 은규 PC              |
  | 차헌   | GC2/GC3 장비 PC          | 차헌 PC              |

  **폴더 이름만으로 PC 종류를 구분합니다 (machine_profile 과 무관):**
    Desktop\\박은규\\  → GC1 **장비** (은규 PC 아님)
    Desktop\\KCH\\     → GC2/GC3 **장비** (차헌 PC 아님)
    Desktop\\.cursor\\ → 은규 PC 또는 차헌 PC (촉매 반응 계산.py)

  같은 물리 PC에 박은규·KCH 폴더가 둘 다 있으면 **env 탐색 순서**에 따라
  gc1/gc2가 달라질 수 있으므로, 장비 PC에는 해당 인스턴스 env 하나만 두세요.

=============================================================================
[env 경로 요약]
=============================================================================

  | 장비 | env 경로                         | GC_INSTANCE | 핫스팟             |
  |------|----------------------------------|-------------|--------------------|
  | GC1  | Desktop\\박은규\\_GC자동화\\gc_automation.env | gc1         | iPhone             |
  | GC2  | Desktop\\KCH\\gc_automation.env    | gc2         | iptime / iptime 2 / iptime_5G |
  | GC3  | Desktop\\KCH\\gc_automation.env    | gc3         | iptime / iptime 2 / iptime_5G |

  GC1 → gc_autochro + gc_gc1 (PDF)
  GC2 → gc_chemstation (8860 acam)
  GC3 → gc_chem32 (Report.txt)

=============================================================================
[resolve_profile() 탐색 순서]
=============================================================================

  1) 환경변수 GC_INSTANCE / EXCEL_OUTPUT_DIR (env 로드 후)
  2) Desktop\\박은규\\_GC자동화\\gc_automation.env (또는 루트 레거시) → GC1 장비
  3) Desktop\\KCH\\gc_automation.env 존재 → GC2 또는 GC3 (env의 GC_INSTANCE)
  4) PROFILE_DEFAULTS 기본값 (gc2 쪽)

  확인: python gc_automation.py --show-profile

  PC 식별 JSON (선택): Desktop\\박은규 또는 KCH\\machine_profile.json
"""

from __future__ import annotations

import os
import sys
from dataclasses import dataclass
from typing import Iterable, List, Optional

from gc_config import DEFAULT_CHEMSTATION_DATA, DEFAULT_GC3_DATA, EXCEL_OUTPUT_DIR, REQUIRED_HOTSPOT_SSID
from gc_wifi import format_required_ssids_label

DESKTOP = os.path.join(os.path.expanduser("~"), "Desktop")
# GC1 **장비** PC 기본 출력 (Autochro PDF·xlsx). 「은규 PC」= Desktop\.cursor 와 다름.
DEFAULT_GC1_OUTPUT = os.path.join(DESKTOP, "박은규")
# GC2/GC3 **장비** PC 기본 출력. 「차헌 PC」= Desktop\.cursor 와 다름.
DEFAULT_GC2_OUTPUT = EXCEL_OUTPUT_DIR

# GC1 장비 PC: 실험 데이터(xlsx·pdf)와 자동화 파일 분리
GC1_RUNTIME_SUBDIR_DEFAULT = "_GC자동화"

PROFILE_DEFAULTS = {
    # gc1 — GC1 장비 PC (은규). Autochro PDF. 데이터 처리는 은규 PC.
    "gc1": {
        "output_dir": DEFAULT_GC1_OUTPUT,
        "hotspot": "iPhone",
        "chemstation_mode": "gc1",
    },
    # gc2 — GC2 장비 PC (차헌). acam. 계산·Origin은 차헌 PC.
    "gc2": {
        "output_dir": DEFAULT_GC2_OUTPUT,
        "hotspot": REQUIRED_HOTSPOT_SSID,
        "chemstation_mode": "8860",
    },
    # gc3 — GC3 장비 PC (차헌). Chem32. env에서 GC_INSTANCE=gc3.
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
    """gc_automation.env 탐색 순서 (첫 번째로 찾은 파일을 bootstrap_env 가 로드).

    박은규 → GC1 장비 PC, KCH → GC2/GC3 장비 PC.
    Desktop\\.cursor\\gc_automation.env 는 **데이터 PC(은규/차헌 PC)** 용이므로 여기서는 찾지 않음.
    """
    dirs: List[str] = []

    explicit = os.getenv("EXCEL_OUTPUT_DIR", "").strip()
    if explicit:
        dirs.append(explicit)

    for folder_name in ("박은규", "KCH"):
        path = os.path.join(DESKTOP, folder_name)
        search_bases = [path]
        if folder_name == "박은규":
            search_bases.insert(0, os.path.join(path, gc_runtime_subdir_name()))
        for base in search_bases:
            env_path = os.path.join(base, "gc_automation.env")
            if os.path.isfile(env_path):
                dirs.append(path)
                break

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
    for data_root in candidate_env_dirs(base_script_dir):
        search_bases = [data_root]
        if os.path.basename(data_root) == "박은규":
            search_bases.insert(0, os.path.join(data_root, gc_runtime_subdir_name()))
        for base in search_bases:
            for name in (".env", "gc_automation.env"):
                path = os.path.join(base, name)
                if os.path.isfile(path):
                    _load_env_file(path)
                    loaded_from = path
                    break
            if loaded_from:
                break
        if loaded_from:
            break
    return resolve_excel_output_dir(base_script_dir, loaded_from), loaded_from


def resolve_excel_output_dir(base_script_dir: str, loaded_env_file: Optional[str] = None) -> str:
    explicit = os.getenv("EXCEL_OUTPUT_DIR", "").strip()
    if explicit:
        return os.path.normpath(os.path.expanduser(explicit))
    if loaded_env_file:
        return _excel_root_from_env_path(loaded_env_file)
    instance = os.getenv("GC_INSTANCE", "").strip().lower()
    if instance == "gc1":
        return DEFAULT_GC1_OUTPUT
    return DEFAULT_GC2_OUTPUT


def resolve_gc_instance() -> str:
    """GC_INSTANCE 미설정 시 출력 폴더 basename 으로 gc1/gc2 추정.

    basename 이 '박은규' 이면 GC1 **장비** PC. 'KCH' 이면 GC2/GC3 **장비** PC.
  """
    instance = os.getenv("GC_INSTANCE", "").strip().lower()
    if instance in PROFILE_DEFAULTS:
        return instance
    output_dir = os.getenv("EXCEL_OUTPUT_DIR", "").strip()
    if output_dir.replace("\\", "/").endswith("/박은규") or output_dir.endswith("박은규"):
        return "gc1"
    if os.path.basename(resolve_excel_output_dir(script_dir())) == "박은규":
        return "gc1"
    return "gc2"


def gc_runtime_subdir_name() -> str:
    """GC1 자동화·watch·env 하위 폴더명 (env ``GC_RUNTIME_SUBDIR`` 로 변경 가능)."""
    raw = os.getenv("GC_RUNTIME_SUBDIR", GC1_RUNTIME_SUBDIR_DEFAULT).strip()
    return raw or GC1_RUNTIME_SUBDIR_DEFAULT


def _excel_root_from_env_path(env_path: str) -> str:
    """env 가 ``_GC자동화\\gc_automation.env`` 에 있어도 데이터 루트는 ``박은규``."""
    parent = os.path.normpath(os.path.dirname(os.path.abspath(env_path)))
    if os.path.basename(parent) == gc_runtime_subdir_name():
        return os.path.dirname(parent)
    return parent


def gc_runtime_dir(excel_output_dir: str, *, gc_instance: str | None = None) -> str:
    """
    GC1: ``Desktop\\박은규\\_GC자동화`` — watch·env·로그·Cursor 연동.
    GC2/GC3: ``excel_output_dir`` 그대로.
    """
    inst = (gc_instance or resolve_gc_instance()).strip().lower()
    if inst != "gc1":
        return os.path.normpath(excel_output_dir)
    return os.path.normpath(os.path.join(excel_output_dir, gc_runtime_subdir_name()))


def migrate_gc1_runtime_layout(excel_output_dir: str) -> int:
    """GC1 자동화 파일을 ``_GC자동화`` 로 이동 (xlsx·pdf 는 루트 유지)."""
    import glob
    import shutil

    if resolve_gc_instance() != "gc1":
        return 0
    data_root = os.path.normpath(excel_output_dir)
    runtime = gc_runtime_dir(data_root, gc_instance="gc1")
    os.makedirs(runtime, exist_ok=True)
    moved = 0
    for name in (
        ".gc_send_state.json",
        ".gc_watch_status.json",
        ".gc_watch.pid",
        "GC_감시_상태.txt",
        "GC_오류_최근.txt",
        "gc_automation.env",
        "gc_run_log.txt",
        "machine_profile.json",
        ".gc_error_handler_run.log",
        ".gc_error_handler_state.json",
        ".gc_error_log.jsonl",
        ".gc_error_pending.json",
        ".gc_hotspot_agent_state.json",
        ".gc_hotspot_agent_pending.json",
        ".gc_hotspot_agent_run.log",
    ):
        src = os.path.join(data_root, name)
        dst = os.path.join(runtime, name)
        if not os.path.isfile(src):
            continue
        if os.path.isfile(dst):
            try:
                os.remove(src)
                moved += 1
            except OSError:
                pass
            continue
        try:
            shutil.move(src, dst)
            moved += 1
        except OSError:
            pass
    for pattern in ("GC_대기_*.txt", "GC_중지_*.txt", "[0-9][0-9][0-9][0-9][0-9][0-9][0-9][0-9].txt"):
        for src in glob.glob(os.path.join(data_root, pattern)):
            dst = os.path.join(runtime, os.path.basename(src))
            if os.path.isfile(dst):
                try:
                    os.remove(src)
                    moved += 1
                except OSError:
                    pass
            elif os.path.isfile(src):
                try:
                    shutil.move(src, dst)
                    moved += 1
                except OSError:
                    pass
    for name in os.listdir(data_root):
        if name.startswith("GC1_") and name.lower().endswith(".bat"):
            src = os.path.join(data_root, name)
            dst = os.path.join(runtime, name)
            if not os.path.isfile(src):
                continue
            if os.path.isfile(dst):
                try:
                    os.remove(src)
                    moved += 1
                except OSError:
                    pass
            else:
                try:
                    shutil.move(src, dst)
                    moved += 1
                except OSError:
                    pass
    sys_dir = os.path.join(data_root, "_system")
    if os.path.isdir(sys_dir) and not os.path.isdir(os.path.join(runtime, "_system")):
        try:
            shutil.move(sys_dir, os.path.join(runtime, "_system"))
            moved += 1
        except OSError:
            pass
    for extra_name in ("GC1_baseline_chemstation-gc-automation.zip", "GC2_Cursor_핸드오프.md"):
        src = os.path.join(data_root, extra_name)
        dst = os.path.join(runtime, extra_name)
        if os.path.isfile(src):
            if os.path.isfile(dst):
                try:
                    os.remove(src)
                    moved += 1
                except OSError:
                    pass
            else:
                try:
                    shutil.move(src, dst)
                    moved += 1
                except OSError:
                    pass
    return moved


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


def resolve_data_path(default: str = DEFAULT_CHEMSTATION_DATA) -> str:
    """GC_INSTANCE / env / 모드에 맞는 ChemStation·Chem32 Data 루트."""
    explicit = os.getenv("CHEMSTATION_DATA_PATH", "").strip() or os.getenv("DATA_PATH", "").strip()
    if explicit:
        return os.path.normpath(os.path.expanduser(explicit))
    instance = resolve_gc_instance()
    mode = resolve_chemstation_mode()
    if instance == "gc3" or mode == "chem32":
        return DEFAULT_GC3_DATA
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


def paths_for_output_dir(output_dir: str, *, gc_instance: str | None = None) -> dict[str, str]:
    inst = gc_instance or resolve_gc_instance()
    runtime = gc_runtime_dir(output_dir, gc_instance=inst)
    os.makedirs(runtime, exist_ok=True)
    return {
        "data_root": os.path.normpath(output_dir),
        "runtime_dir": runtime,
        "send_state": os.path.join(runtime, ".gc_send_state.json"),
        "watch_status_json": os.path.join(runtime, ".gc_watch_status.json"),
        "watch_status_txt": os.path.join(runtime, "GC_감시_상태.txt"),
        "watch_pid": os.path.join(runtime, ".gc_watch.pid"),
    }


def print_output_dir_for_bat() -> None:
    profile = resolve_profile()
    sys.stdout.write(profile.excel_output_dir)


def print_profile_summary(profile: ResolvedProfile) -> None:
    runtime = gc_runtime_dir(profile.excel_output_dir, gc_instance=profile.gc_instance)
    print("[GC 프로필]")
    print(f"  인스턴스      : {profile.gc_instance}")
    print(f"  데이터 폴더    : {profile.excel_output_dir}")
    if runtime != profile.excel_output_dir:
        print(f"  자동화 폴더    : {runtime}")
    print(f"  env 파일       : {profile.env_file or '(없음)'}")
    print(f"  핫스팟 SSID    : {format_required_ssids_label(profile.required_ssid)}")
    print(f"  ChemStation 모드: {profile.chemstation_mode}")
    print(f"  Data 경로      : {resolve_data_path()}")


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--print-output-dir":
        print_output_dir_for_bat()
    elif len(sys.argv) > 1 and sys.argv[1] == "--show-profile":
        print_profile_summary(resolve_profile())
    else:
        print_output_dir_for_bat()
