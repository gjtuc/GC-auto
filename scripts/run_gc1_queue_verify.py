# -*- coding: utf-8 -*-
"""run_gc1_queue_verify.py — Agent 큐 T20~T84 + MOD 파이프라인 일괄 검증

에이전트 작업 큐가 전부 [x] 된 뒤 회귀용.
**정적 검증**(py_compile)과 **실행 검증**(unittest·CLI)을 분리해 순서대로 돌립니다.

Usage (repo 루트):
  python scripts/run_gc1_queue_verify.py
  python scripts/run_gc1_queue_verify.py --quick     # MOD·runtime e2e만
  python scripts/run_gc1_queue_verify.py -v

Exit: 0 = 전부 PASS, 1 = 실패
"""
from __future__ import annotations

import argparse
import os
import py_compile
import subprocess
import sys

_REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# 정적 검증 대상 — 핵심 모듈·스크립트 (문법·import 수준)
_COMPILE_TARGETS = (
    "gc1_rt_validate.py",
    "gc3_screen_read.py",
    "gc1_runtime/mod_registry.py",
    "gc1_runtime/mod_apply.py",
    "gc1_runtime/mod_lifecycle.py",
    "gc1_runtime/mod_intake.py",
    "gc1_runtime/mod_pipeline.py",
    "gc1_runtime/layer0_ident.py",
    "gc1_runtime/layer0_retry.py",
    "gc1_runtime/layer0_gpost.py",
    "gc1_runtime/layer0_fallback.py",
    "gc1_runtime/layer4_atom_fallback.py",
    "gc1_runtime/layer0_resume.py",
    "gc1_runtime/layer4_job.py",
    "scripts/validate_gc1_rt.py",
    "scripts/validate_gc1_mod_slots.py",
    "scripts/validate_gc1_retry_policy.py",
    "scripts/validate_gc1_resume_policy.py",
    "scripts/apply_gc1_mod.py",
    "scripts/status_gc1_mod.py",
    "scripts/intake_gc1_mod.py",
    "scripts/run_gc1_mod_pipeline.py",
    "scripts/close_gc1_mod.py",
    "scripts/run_gc1_runtime_e2e.py",
    "scripts/probe_gc1_ident.py",
)

# 실행 검증 — unittest discover 패턴
_UNITTEST_PATTERNS_FULL = (
    "test_gc1_runtime*.py",
    "test_gc1_mod_*.py",
    "test_gc1_rt_validate.py",
    "test_gc1_resume_policy.py",
    "test_gc1_runtime_layer0_gpost.py",
    "test_gc1_runtime_layer4_atom_fallback.py",
    "test_data_pc_cli.py",
    "test_gc2_regression_script.py",
    "test_gc3_screen_read.py",
)

_UNITTEST_PATTERNS_QUICK = (
    "test_gc1_mod_*.py",
    "test_gc1_runtime_e2e.py",
)

# 실행 검증 — CLI smoke (실장비·메일 불필요)
_CLI_SMOKE = (
    ([sys.executable, "scripts/validate_gc1_rt.py", "--sync-check"], "validate_gc1_rt --sync-check"),
    ([sys.executable, "scripts/validate_gc1_mod_slots.py"], "validate_gc1_mod_slots"),
    ([sys.executable, "scripts/validate_gc1_retry_policy.py"], "validate_gc1_retry_policy"),
    ([sys.executable, "scripts/validate_gc1_resume_policy.py"], "validate_gc1_resume_policy"),
    ([sys.executable, "scripts/status_gc1_mod.py"], "status_gc1_mod"),
    ([sys.executable, "scripts/apply_gc1_mod.py", "--dry-run"], "apply_gc1_mod --dry-run"),
    ([sys.executable, "scripts/run_gc1_mod_pipeline.py"], "run_gc1_mod_pipeline"),
)


def _compile_all() -> bool:
    ok = True
    print("=== [1/3] py_compile (static) ===\n")
    for rel in _COMPILE_TARGETS:
        path = os.path.join(_REPO, rel.replace("/", os.sep))
        if not os.path.isfile(path):
            print(f"[FAIL] missing: {rel}")
            ok = False
            continue
        try:
            py_compile.compile(path, doraise=True)
            print(f"[OK] {rel}")
        except py_compile.PyCompileError as exc:
            print(f"[FAIL] {rel}: {exc}")
            ok = False
    print()
    return ok


def _run_unittest(patterns: tuple[str, ...], *, verbose: bool) -> bool:
    print("=== [2/3] unittest discover (execution) ===\n")
    ok = True
    for pattern in patterns:
        cmd = [
            sys.executable,
            "-m",
            "unittest",
            "discover",
            "-s",
            _REPO,
            "-p",
            pattern,
        ]
        if verbose:
            cmd.append("-v")
        else:
            cmd.append("-q")
        print(f"--- pattern: {pattern!r} ---")
        result = subprocess.run(cmd, cwd=_REPO)
        if result.returncode == 0:
            print(f"[OK] {pattern}\n")
        else:
            print(f"[FAIL] {pattern} exit={result.returncode}\n")
            ok = False
    return ok


def _run_cli_smoke() -> bool:
    print("=== [3/3] CLI smoke (execution) ===\n")
    ok = True
    for cmd, label in _CLI_SMOKE:
        result = subprocess.run(cmd, cwd=_REPO, capture_output=True, text=True, encoding="utf-8", errors="replace")
        if result.returncode == 0:
            print(f"[OK] {label}")
        else:
            print(f"[FAIL] {label} exit={result.returncode}")
            if result.stderr:
                print(result.stderr[:400])
            ok = False
    # run_gc1_runtime_e2e helper (default mode)
    e2e = [sys.executable, "scripts/run_gc1_runtime_e2e.py"]
    result = subprocess.run(e2e, cwd=_REPO, capture_output=True, text=True, encoding="utf-8", errors="replace")
    if result.returncode == 0:
        print("[OK] run_gc1_runtime_e2e.py")
    else:
        print(f"[FAIL] run_gc1_runtime_e2e.py exit={result.returncode}")
        ok = False
    print()
    return ok


def main() -> int:
    parser = argparse.ArgumentParser(description="GC1 agent queue regression verify")
    parser.add_argument("--quick", action="store_true", help="MOD + runtime e2e unittest only")
    parser.add_argument("-v", "--verbose", action="store_true")
    args = parser.parse_args()

    patterns = _UNITTEST_PATTERNS_QUICK if args.quick else _UNITTEST_PATTERNS_FULL

    c_ok = _compile_all()
    u_ok = _run_unittest(patterns, verbose=args.verbose)
    s_ok = _run_cli_smoke() if not args.quick else True

    if c_ok and u_ok and s_ok:
        print("[PASS] GC1 queue verify - static + execution OK")
        return 0
    print("[FAIL] GC1 queue verify - see errors above")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
