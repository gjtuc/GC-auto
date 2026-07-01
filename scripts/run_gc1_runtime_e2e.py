# -*- coding: utf-8 -*-
"""run_gc1_runtime_e2e.py — GC1 runtime dry-run E2E (Step 8 보조, 실장비 불필요)

T63 ``test_gc1_runtime_e2e.py`` 를 실행 검증용 래퍼로 돌립니다.
Autochro·pywinauto·Tesseract 없이 P0→P9 atom ``status=ok`` 시뮬레이션을 확인합니다.

정적 검증: ``py_compile`` (import 구문·문법)
실행 검증: ``unittest`` (mock deps 로 phase·job JSON·PDF 생성)

Usage (repo 루트):
  python scripts/run_gc1_runtime_e2e.py
  python scripts/run_gc1_runtime_e2e.py --full    # test_gc1_runtime*.py 전체
  python scripts/run_gc1_runtime_e2e.py -v

관련 env (테스트 내부 mock — 본 스크립트는 설정 안 함):
  GC1_USE_RUNTIME=1, AUTOCHRO_DRY_RUN=1, GC1_AUTOCHRO_PREP_STEPS=0|1
"""
from __future__ import annotations

import argparse
import os
import py_compile
import subprocess
import sys

_REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_E2E_MODULE = "test_gc1_runtime_e2e"
_E2E_FILE = os.path.join(_REPO_ROOT, f"{_E2E_MODULE}.py")


def _compile_check() -> bool:
    """정적 검증 — 문법·import 수준 (실행과 별개)."""
    try:
        py_compile.compile(_E2E_FILE, doraise=True)
    except py_compile.PyCompileError as exc:
        print(f"[FAIL] py_compile: {exc}")
        return False
    print(f"[OK] py_compile: {_E2E_MODULE}.py")
    return True


def _run_unittest(pattern: str, *, verbose: bool) -> int:
    """실행 검증 — unittest discover."""
    cmd = [
        sys.executable,
        "-m",
        "unittest",
        "discover",
        "-s",
        _REPO_ROOT,
        "-p",
        pattern,
    ]
    if verbose:
        cmd.append("-v")
    else:
        cmd.append("-q")
    print(f"\n--- unittest discover -p {pattern!r} ---")
    result = subprocess.run(cmd, cwd=_REPO_ROOT)
    if result.returncode == 0:
        print(f"[OK] unittest: {pattern}")
    else:
        print(f"[FAIL] unittest exit={result.returncode}: {pattern}")
    return result.returncode


def main() -> int:
    parser = argparse.ArgumentParser(
        description="GC1 runtime dry-run E2E (no Autochro hardware)",
    )
    parser.add_argument(
        "--full",
        action="store_true",
        help="test_gc1_runtime*.py 전체 suite (기본: e2e 모듈만)",
    )
    parser.add_argument("-v", "--verbose", action="store_true", help="unittest -v")
    args = parser.parse_args()

    if not os.path.isfile(_E2E_FILE):
        print(f"[FAIL] missing: {_E2E_FILE}")
        return 1

    if not _compile_check():
        return 1

    pattern = "test_gc1_runtime*.py" if args.full else f"{_E2E_MODULE}.py"
    return _run_unittest(pattern, verbose=args.verbose)


if __name__ == "__main__":
    raise SystemExit(main())
