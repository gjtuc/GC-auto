# -*- coding: utf-8 -*-
"""
runtime_paths.py — GC 데이터 PC 런타임 부가 파일 경로 (은규 PC / 차헌 PC)

=============================================================================
[LLM/에이전트 참고]
=============================================================================

  **목적:** 실험과 무관한 Python·런타임 부가 파일을 gc-data-pc / Desktop\\.cursor
  운영 폴더에 흩뿌리지 않고, Cursor IDE 트리 아래로 모음.

  | 경로 | 용도 | 실험 데이터? |
  |------|------|-------------|
  | gc-data-pc\\PEG\\inbox | 메일 xlsx | ✅ 예 |
  | gc-data-pc\\PEG\\processed | 계산 완료 xlsx | ✅ 예 |
  | %USERPROFILE%\\.cursor\\gc-python-cache | __pycache__ / .pyc | ❌ 아니오 |
  | %USERPROFILE%\\.cursor\\gc-runtime-temp | 스크립트 임시 파일 | ❌ 아니오 |

  ⚠ %USERPROFILE%\\.cursor\\ 는 Cursor IDE 설정도 있지만,
    gc-* 하위 폴더만 GC 파이프라인 부가 파일용 (IDE 설정과 분리).

  **import 순서:** 촉매 반응 계산.py 최상단에서 pandas 등보다 **먼저** import.

=============================================================================
"""

from __future__ import annotations

import os
import sys

# [LLM] GC 부가 파일 루트 — Cursor IDE 폴더 아래 전용 하위 디렉터리
CURSOR_USER_ROOT = os.path.join(os.path.expanduser("~"), ".cursor")
PYTHON_CACHE_DIR = os.path.join(CURSOR_USER_ROOT, "gc-python-cache")
RUNTIME_TEMP_DIR = os.path.join(CURSOR_USER_ROOT, "gc-runtime-temp")


def ensure_runtime_dirs() -> None:
    """[LLM] gc-python-cache, gc-runtime-temp 폴더 생성 (없으면)."""
    for path in (PYTHON_CACHE_DIR, RUNTIME_TEMP_DIR):
        os.makedirs(path, exist_ok=True)


def redirect_python_cache() -> str:
    """
    [LLM] __pycache__ 를 gc-data-pc 에 두지 않고 .cursor\\gc-python-cache 로 리다이렉트.

    Python 3.8+: sys.pycache_prefix + PYTHONPYCACHEPREFIX 환경변수.
    pandas 등 무거운 import **전에** 호출할 것.
    """
    ensure_runtime_dirs()
    if hasattr(sys, "pycache_prefix"):
        sys.pycache_prefix = PYTHON_CACHE_DIR
    os.environ["PYTHONPYCACHEPREFIX"] = PYTHON_CACHE_DIR
    return PYTHON_CACHE_DIR


def runtime_temp_dir() -> str:
    """[LLM] 스크립트가 임시 파일이 필요할 때 쓸 디렉터리 (실험 데이터 아님)."""
    ensure_runtime_dirs()
    os.environ["GC_DATA_PC_RUNTIME"] = RUNTIME_TEMP_DIR
    return RUNTIME_TEMP_DIR


def setup_all() -> None:
    """촉매 반응 계산.py 시작 시 한 번 호출."""
    redirect_python_cache()
    runtime_temp_dir()


# import 즉시 적용 (촉매 반응 계산.py 가 `import runtime_paths` 만 해도 됨)
setup_all()
