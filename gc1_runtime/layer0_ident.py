# -*- coding: utf-8 -*-
"""
gc1_runtime.layer0_ident — Ω.A.B.IDENT PC 역할·프로필 판별 (T88, T89)

설계: ``deploy/GC1_RUNTIME_DESIGN.md`` §B-IDENT
G-EX.02: ``role=data_pc`` 이면 Autochro export **BLOCK** (은규 PC).

프로브만 — 파일 쓰기 없음. ``layer4_job.build_export_gate_input`` 에서 사용.

T89: IDENT.01~08 스냅샷 — ``read_ident_snapshot()`` + ``gc_profiles.resolve_profile``.
"""
from __future__ import annotations

import json
import os
from dataclasses import dataclass
from typing import Any, Callable, Optional, Sequence

# 은규·차헌 data_pc 후보 (장비 profile 없을 때만)
_DATA_PC_PROFILE_CANDIDATES: tuple[str, ...] = (
    os.path.join("gc-data-pc", "PEG", "machine_profile.json"),
    os.path.join("gc-data-pc", "KCH", "machine_profile.json"),
    os.path.join("Desktop", ".cursor", "KCH", "machine_profile.json"),
)

# Ω.A.B.IDENT.05 — GC1 장비 PC (G-EX 는 이 role 이 우선)
_GC1_EQUIPMENT_PROFILE: str = os.path.join("Desktop", "박은규", "machine_profile.json")
_GC1_ENV_REL: str = os.path.join("Desktop", "박은규", "gc_automation.env")

# expand_profile_paths 용 전체 나열 (진단·테스트)
_DEFAULT_PROFILE_CANDIDATES: tuple[str, ...] = (
    _GC1_EQUIPMENT_PROFILE,
    *_DATA_PC_PROFILE_CANDIDATES,
    os.path.join("Desktop", "KCH", "machine_profile.json"),
)


def expand_profile_paths(
    relative_parts: Sequence[str] | None = None,
    *,
    home: str | None = None,
) -> tuple[str, ...]:
    """``%USERPROFILE%`` 기준 machine_profile.json 후보 경로."""
    root = home or os.path.expanduser("~")
    parts = relative_parts if relative_parts is not None else _DEFAULT_PROFILE_CANDIDATES
    return tuple(os.path.join(root, p) for p in parts)


def load_machine_profile(path: str) -> Optional[dict[str, Any]]:
    """JSON 로드 — 실패 시 None (정적·실행 공통)."""
    if not os.path.isfile(path):
        return None
    try:
        with open(path, encoding="utf-8") as fh:
            data = json.load(fh)
    except (OSError, json.JSONDecodeError):
        return None
    return data if isinstance(data, dict) else None


def read_machine_role(path: str) -> Optional[str]:
    """단일 profile 파일에서 ``role`` 문자열."""
    data = load_machine_profile(path)
    if not data:
        return None
    role = data.get("role")
    return str(role).strip() if role else None


def is_data_pc_role(role: Optional[str]) -> bool:
    return role == "data_pc"


def is_gc_equipment_role(role: Optional[str]) -> bool:
    """gc1_pc / gc2_pc / gc3_pc — 장비 PC."""
    return role in ("gc1_pc", "gc2_pc", "gc3_pc")


def detect_machine_role(
    search_paths: Sequence[str] | None = None,
) -> Optional[str]:
    """
    첫 번째로 읽히는 profile 의 ``role``.

    여러 profile 이 있으면 **첫 매칭** (테스트는 단일 경로 주입 권장).
    """
    for path in search_paths or expand_profile_paths():
        role = read_machine_role(path)
        if role:
            return role
    return None


def detect_data_pc(
    search_paths: Sequence[str] | None = None,
    *,
    home: str | None = None,
) -> bool:
    """
    Ω.A.B.IDENT.07 — G-EX.02 입력.

    우선순위 (동일 PC에 차헌 data_pc 사본이 있어도 GC1 장비가 우선):
      1. ``Desktop\\박은규\\machine_profile.json`` 이 있으면 그 ``role`` 만 사용
      2. 없으면 data_pc 전용 경로(gc-data-pc 등) 순회
    """
    if search_paths is not None:
        for path in search_paths:
            role = read_machine_role(path)
            if role:
                return is_data_pc_role(role)
        return False

    root = home or os.path.expanduser("~")
    gc1_profile = os.path.join(root, _GC1_EQUIPMENT_PROFILE)
    role = read_machine_role(gc1_profile)
    if role:
        return is_data_pc_role(role)

    for rel in _DATA_PC_PROFILE_CANDIDATES:
        r = read_machine_role(os.path.join(root, rel))
        if r:
            return is_data_pc_role(r)
    return False


def default_repo_root() -> str:
    """Ω.A.B.IDENT.01 — chemstation-gc-automation 루트 (본 패키지 기준)."""
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def path_gc1_env(*, home: str | None = None) -> str:
    """Ω.A.B.IDENT.02 — GC1 장비 env 경로."""
    root = home or os.path.expanduser("~")
    return os.path.join(root, _GC1_ENV_REL)


def path_gc1_machine_profile(*, home: str | None = None) -> str:
    """Ω.A.B.IDENT.05 — GC1 장비 machine_profile.json."""
    root = home or os.path.expanduser("~")
    return os.path.join(root, _GC1_EQUIPMENT_PROFILE)


def is_repo_root(path: str | None = None) -> bool:
    """Ω.A.B.IDENT.01.FS.isdir — repo 루트 존재."""
    return os.path.isdir(path or default_repo_root())


def has_gc1_env_file(*, home: str | None = None) -> bool:
    """Ω.A.B.IDENT.02.FS.isfile."""
    return os.path.isfile(path_gc1_env(home=home))


def has_gc1_machine_profile(*, home: str | None = None) -> bool:
    """Ω.A.B.IDENT.05.FS.isfile — optional profile."""
    return os.path.isfile(path_gc1_machine_profile(home=home))


def is_gc1_instance(instance: str) -> bool:
    """Ω.A.B.IDENT.04.CMP.instance."""
    return instance.strip().lower() == "gc1"


def is_gc1_chemstation_mode(mode: str) -> bool:
    """Ω.A.B.IDENT.08.CMP.chemstation_mode."""
    return mode.strip().lower() == "gc1"


def read_resolved_profile(
    resolve_fn: Callable[[], Any] | None = None,
) -> Any:
    """
    Ω.A.B.IDENT.03.PURE.resolve_profile — ``gc_profiles.resolve_profile()`` 래퍼.

    테스트는 ``resolve_fn`` 주입 (실제 env 로드 방지).
    """
    if resolve_fn is not None:
        return resolve_fn()
    from gc_profiles import resolve_profile  # noqa: PLC0415 — lazy, 장비 PC 전용

    return resolve_profile()


@dataclass(frozen=True)
class IdentSnapshot:
    """
    Ω.A.B.IDENT.01~08 프로브 결과 묶음 (진단·G-EX 보조).

    ``ok_for_gc1_autochro``: IDENT.04 ∧ IDENT.07 ∧ IDENT.08 (타워 A export 전제).
    """

    repo_root_exists: bool
    gc1_env_exists: bool
    gc_instance: str
    chemstation_mode: str
    excel_output_dir: str
    env_file: str
    machine_profile_path: str
    machine_role: Optional[str]
    is_gc1_instance: bool
    is_not_data_pc: bool
    is_gc1_mode: bool
    ok_for_gc1_autochro: bool

    def to_dict(self) -> dict[str, Any]:
        """CLI·로그용 JSON-serializable dict."""
        return {
            "repo_root_exists": self.repo_root_exists,
            "gc1_env_exists": self.gc1_env_exists,
            "gc_instance": self.gc_instance,
            "chemstation_mode": self.chemstation_mode,
            "excel_output_dir": self.excel_output_dir,
            "env_file": self.env_file,
            "machine_profile_path": self.machine_profile_path,
            "machine_role": self.machine_role,
            "is_gc1_instance": self.is_gc1_instance,
            "is_not_data_pc": self.is_not_data_pc,
            "is_gc1_mode": self.is_gc1_mode,
            "ok_for_gc1_autochro": self.ok_for_gc1_autochro,
        }


def read_ident_snapshot(
    *,
    repo_root: str | None = None,
    home: str | None = None,
    resolve_fn: Callable[[], Any] | None = None,
) -> IdentSnapshot:
    """
    IDENT leaf 전부 읽기 — 정적·실행 검증 공통 진입점.

    ``home``/``resolve_fn`` 은 unittest 에서 temp·mock 용.
    """
    root = home or os.path.expanduser("~")
    repo = repo_root or default_repo_root()
    profile_path = path_gc1_machine_profile(home=root)
    role = read_machine_role(profile_path) if has_gc1_machine_profile(home=root) else None
    not_data_pc = not detect_data_pc(home=root)

    resolved = read_resolved_profile(resolve_fn)
    instance = str(getattr(resolved, "gc_instance", "") or "")
    mode = str(getattr(resolved, "chemstation_mode", "") or "")
    output_dir = str(getattr(resolved, "excel_output_dir", "") or "")
    env_file = str(getattr(resolved, "env_file", "") or "")

    inst_ok = is_gc1_instance(instance)
    mode_ok = is_gc1_chemstation_mode(mode)

    return IdentSnapshot(
        repo_root_exists=os.path.isdir(repo),
        gc1_env_exists=has_gc1_env_file(home=root),
        gc_instance=instance,
        chemstation_mode=mode,
        excel_output_dir=output_dir,
        env_file=env_file,
        machine_profile_path=profile_path,
        machine_role=role,
        is_gc1_instance=inst_ok,
        is_not_data_pc=not_data_pc,
        is_gc1_mode=mode_ok,
        ok_for_gc1_autochro=inst_ok and not_data_pc and mode_ok,
    )
