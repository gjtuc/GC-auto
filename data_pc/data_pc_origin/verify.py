# -*- coding: utf-8 -*-
"""
data_pc_origin 검증 — 층별·게이트별.

  python -m data_pc_origin.verify --gate O0-K-01-a-1
  python -m data_pc_origin.verify --rollup O1-P
  python -m data_pc_origin.verify --o0
  python -m data_pc_origin.verify --o1
  python -m data_pc_origin.verify --o3
"""
from __future__ import annotations

import argparse
import sys
import unittest
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

_LAYER_STATUS = Path(__file__).resolve().parent / "LAYER_STATUS.md"


def _ensure_gates() -> None:
    from data_pc_origin.gates.implementations import ensure_gates_loaded

    ensure_gates_loaded()


def _run_unit_tests(pattern: str = "test_*.py") -> bool:
    loader = unittest.TestLoader()
    suite = loader.discover(
        str(Path(__file__).parent / "tests"),
        pattern=pattern,
    )
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    return result.wasSuccessful()


def _run_rollup_gates(rollup_id: str) -> tuple[bool, list[str]]:
    from data_pc_origin.gates.registry import rollup_gate_ids
    from data_pc_origin.gates.runner import run_gates_in_order

    _ensure_gates()
    code, log, _ = run_gates_in_order(rollup_gate_ids(rollup_id))
    return code == 0, log


def _patch_layer_status(
    *,
    o0_gates: bool | None = None,
    o1_gates: bool | None = None,
    o2_gates: bool | None = None,
    o3_gates: bool | None = None,
    o4_gates: bool | None = None,
    o5_i_gates: bool | None = None,
    o5_t_gates: bool | None = None,
    o5_m_gates: bool | None = None,
) -> None:
    if not _LAYER_STATUS.is_file():
        return
    lines = _LAYER_STATUS.read_text(encoding="utf-8").splitlines()
    out: list[str] = []
    for line in lines:
        if o0_gates is not None and line.startswith("| O0 L4 리프 |"):
            status = "**PASS** (61 L4)" if o0_gates else "FAIL"
            out.append(f"| O0 L4 리프 | {status} | `verify --rollup O0` | 61 gates |")
        elif o1_gates is not None and line.startswith("| O1 probes |"):
            status = "**PASS** (27 L4)" if o1_gates else "FAIL"
            out.append(f"| O1 probes | {status} | `verify --rollup O1` | 27 gates |")
        elif o2_gates is not None and line.startswith("| O2 gates |"):
            status = "**PASS** (21 L4)" if o2_gates else "FAIL"
            out.append(f"| O2 gates | {status} | `verify --rollup O2` | 21 gates |")
        elif o3_gates is not None and line.startswith("| O3 session |"):
            status = "**PASS** (12 L4)" if o3_gates else "FAIL"
            out.append(f"| O3 session | {status} | `verify --rollup O3` | 12 gates |")
        elif o4_gates is not None and line.startswith("| O4 project |"):
            status = "**PASS** (8 L4)" if o4_gates else "FAIL"
            out.append(f"| O4 project | {status} | `verify --rollup O4` | 8 gates |")
        elif o5_i_gates is not None and line.startswith("| O5-I iterate |"):
            status = "**PASS** (24 L4)" if o5_i_gates else "FAIL"
            out.append(f"| O5-I iterate | {status} | `verify --rollup O5-L1-I` | 24 gates |")
        elif o5_t_gates is not None and line.startswith("| O5-T text |"):
            status = "**PASS** (27 L4)" if o5_t_gates else "FAIL"
            out.append(f"| O5-T text | {status} | `verify --rollup O5-L1-T` | 27 gates |")
        elif o5_m_gates is not None and line.startswith("| O5-M match |"):
            status = "**PASS** (54 L4)" if o5_m_gates else "FAIL"
            out.append(f"| O5-M match | {status} | `verify --rollup O5-L1-M` | 54 gates |")
        elif o5_m_gates is not None and line.startswith("| O5 worksheet |"):
            out.append(
                "| O5 worksheet | **PASS** (core 105/105) | `verify --rollup O5-M` | I+T+M |"
            )
        elif o5_t_gates is not None and line.startswith("| O5 worksheet |"):
            out.append(
                "| O5 worksheet | LOCKED (I+T **PASS** 51/105) | `O5-M-01-a-1` … | O5-REGISTRY |"
            )
        elif o5_i_gates is not None and line.startswith("| O5 worksheet |"):
            status = "LOCKED (I **PASS** 24/105)" if o5_i_gates else line
            if o5_i_gates:
                out.append(
                    "| O5 worksheet | LOCKED (I **PASS** 24/105) | `O5-T-01-a-1` … | O5-REGISTRY |"
                )
            else:
                out.append(line)
        else:
            out.append(line)
    _LAYER_STATUS.write_text("\n".join(out) + "\n", encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="data_pc_origin 층별·게이트 검증")
    parser.add_argument("--gate", metavar="ID", help="단일 L4 gate (선행 gate 자동 실행)")
    parser.add_argument("--rollup", metavar="ID", help="합본 (O0, O1-P, O1, …)")
    parser.add_argument("--o0", action="store_true", help="O0: 61 gate + unittest")
    parser.add_argument("--o1", action="store_true", help="O1: O0+O1 gates + unittest")
    parser.add_argument("--o2", action="store_true", help="O2: O0+O1+O2 gates + unittest")
    parser.add_argument("--o3", action="store_true", help="O3: O0..O3 gates + unittest")
    parser.add_argument("--o4", action="store_true", help="O4: O0..O4 gates + unittest")
    parser.add_argument("--o5-i", action="store_true", help="O5-I: O0..O4+O5-I (24) gates + unittest")
    parser.add_argument("--o5-t", action="store_true", help="O5-T: O0..O4+O5-I+T (51) gates + unittest")
    parser.add_argument("--o5-m", action="store_true", help="O5-M: O0..O4+O5 core 105 gates + unittest")
    parser.add_argument("--o5-debug", action="store_true", help="O5 DEBUG: core+ DEBUG(5) + unittest")
    parser.add_argument("--o5-meta", action="store_true", help="O5 meta: core+ E2E(3)+R(4) + unittest")
    parser.add_argument("--o6-s", action="store_true", help="O6-S: scan (4) + unittest")
    parser.add_argument("--o6-p", action="store_true", help="O6-P: S+F+P (12) + unittest")
    parser.add_argument("--o6", action="store_true", help="O6: full column layer (16) + unittest")
    parser.add_argument("--o7", action="store_true", help="O7: write layer (9) + unittest")
    parser.add_argument("--o8", action="store_true", help="O8: job layer (11) + unittest")
    parser.add_argument("--o9", action="store_true", help="O9: facade (10) + unittest")
    parser.add_argument("--o9-live", action="store_true", help="O9 live harness: O9(10)+L(3) + unittest")
    parser.add_argument("--list", action="store_true", help="전체 gate 순서 출력")
    args = parser.parse_args(argv)

    if args.list:
        from data_pc_origin.gates.registry import FULL_IMPLEMENTATION_ORDER

        for i, gid in enumerate(FULL_IMPLEMENTATION_ORDER, 1):
            print(f"{i:3}. {gid}")
        return 0

    if args.gate:
        _ensure_gates()
        from data_pc_origin.gates.registry import implementation_prefix
        from data_pc_origin.gates.runner import run_gate

        passed: set[str] = set()
        try:
            prefix = implementation_prefix(args.gate)
        except ValueError:
            print(f"[UNKNOWN] {args.gate}")
            return 3
        for gid in prefix:
            code, passed = run_gate(gid, passed)
            if code == 2:
                print(f"[LOCKED] {gid}")
                return 2
            if code == 3:
                print(f"[UNKNOWN] {gid}")
                return 3
            if code != 0:
                print(f"[FAIL] {gid}")
                return 1
        print(f"[PASS] {args.gate}")
        return 0

    if args.rollup:
        _ensure_gates()
        from data_pc_origin.gates.runner import run_rollup

        code, log, _ = run_rollup(args.rollup)
        for line in log:
            print(line)
        return code

    if args.o9_live:
        print("=== data_pc_origin verify: O9-L (O9 10 + live harness 3 gates + unittest) ===\n")
        gates_ok, gate_log = _run_rollup_gates("O9-L")
        for line in gate_log:
            print(line)
        print()
        unit_ok = _run_unit_tests("test_*.py")
        if gates_ok and unit_ok:
            print("\n[OK] O0..O9 + O9-L (13) gates + unit tests passed")
            return 0
        print("\n[FAIL] O9-L verify failed")
        return 1

    if args.o9:
        print("=== data_pc_origin verify: O9 (facade 7 gates + unittest) ===\n")
        gates_ok, gate_log = _run_rollup_gates("O9")
        for line in gate_log:
            print(line)
        print()
        unit_ok = _run_unit_tests("test_*.py")
        if gates_ok and unit_ok:
            print("\n[OK] O0..O8 + O9 (10) gates + unit tests passed")
            return 0
        print("\n[FAIL] O9 verify failed")
        return 1

    if args.o8:
        print("=== data_pc_origin verify: O8 (job 11 gates + unittest) ===\n")
        gates_ok, gate_log = _run_rollup_gates("O8")
        for line in gate_log:
            print(line)
        print()
        unit_ok = _run_unit_tests("test_*.py")
        if gates_ok and unit_ok:
            print("\n[OK] O0..O7 + O8 (11) gates + unit tests passed")
            return 0
        print("\n[FAIL] O8 verify failed")
        return 1

    if args.o7:
        print("=== data_pc_origin verify: O7 (write 9 gates + unittest) ===\n")
        gates_ok, gate_log = _run_rollup_gates("O7")
        for line in gate_log:
            print(line)
        print()
        unit_ok = _run_unit_tests("test_*.py")
        if gates_ok and unit_ok:
            print("\n[OK] O0..O6 + O7 (9) gates + unit tests passed")
            return 0
        print("\n[FAIL] O7 verify failed")
        return 1

    if args.o6:
        print("=== data_pc_origin verify: O6 full (16 gates + unittest) ===\n")
        gates_ok, gate_log = _run_rollup_gates("O6")
        for line in gate_log:
            print(line)
        print()
        unit_ok = _run_unit_tests("test_*.py")
        if gates_ok and unit_ok:
            print("\n[OK] O0..O5 meta + O6 full (16) gates + unit tests passed")
            return 0
        print("\n[FAIL] O6 verify failed")
        return 1

    if args.o6_p:
        print("=== data_pc_origin verify: O6-P (S+F+P 12 gates + unittest) ===\n")
        gates_ok, gate_log = _run_rollup_gates("O6-P")
        for line in gate_log:
            print(line)
        print()
        unit_ok = _run_unit_tests("test_*.py")
        if gates_ok and unit_ok:
            print("\n[OK] O0..O5 meta + O6 S+F+P (12) gates + unit tests passed")
            return 0
        print("\n[FAIL] O6-P verify failed")
        return 1

    if args.o6_s:
        print("=== data_pc_origin verify: O6-S (O0..O5 meta + scan 4 + unittest) ===\n")
        gates_ok, gate_log = _run_rollup_gates("O6-S")
        for line in gate_log:
            print(line)
        print()
        unit_ok = _run_unit_tests("test_*.py")
        if gates_ok and unit_ok:
            print("\n[OK] O0..O5 meta + O6-S (4) gates + unit tests passed")
            return 0
        print("\n[FAIL] O6-S verify failed")
        return 1

    if args.o5_debug:
        print("=== data_pc_origin verify: O5-DEBUG (core + DEBUG 5 + unittest) ===\n")
        gates_ok, gate_log = _run_rollup_gates("O5-DEBUG")
        for line in gate_log:
            print(line)
        print()
        unit_ok = _run_unit_tests("test_*.py")
        if gates_ok and unit_ok:
            print("\n[OK] O0..O4 + O5 core + DEBUG (110) gates + unit tests passed")
            return 0
        print("\n[FAIL] O5-DEBUG verify failed")
        return 1

    if args.o5_meta:
        print("=== data_pc_origin verify: O5 meta (core + E2E + R + unittest) ===\n")
        gates_ok, gate_log = _run_rollup_gates("O5-META")
        for line in gate_log:
            print(line)
        print()
        unit_ok = _run_unit_tests("test_*.py")
        if gates_ok and unit_ok:
            print("\n[OK] O0..O4 + O5 full meta (112) gates + unit tests passed")
            return 0
        print("\n[FAIL] O5 meta verify failed")
        return 1

    if args.o5_m:
        print("=== data_pc_origin verify: O5-M (O0..O4 + O5 core 105 + unittest) ===\n")
        gates_ok, gate_log = _run_rollup_gates("O5-L1-M")
        for line in gate_log:
            print(line)
        print()
        unit_ok = _run_unit_tests("test_*.py")
        if gates_ok and unit_ok:
            _patch_layer_status(
                o0_gates=True,
                o1_gates=True,
                o2_gates=True,
                o3_gates=True,
                o4_gates=True,
                o5_i_gates=True,
                o5_t_gates=True,
                o5_m_gates=True,
            )
            print("\n[OK] O0..O4 + O5 core (234) gates + unit tests passed")
            return 0
        print("\n[FAIL] O5-M verify failed")
        return 1

    if args.o5_t:
        print("=== data_pc_origin verify: O5-T (O0..O4 + O5-L1-T + unittest) ===\n")
        gates_ok, gate_log = _run_rollup_gates("O5-L1-T")
        for line in gate_log:
            print(line)
        print()
        unit_ok = _run_unit_tests("test_*.py")
        if gates_ok and unit_ok:
            _patch_layer_status(
                o0_gates=True,
                o1_gates=True,
                o2_gates=True,
                o3_gates=True,
                o4_gates=True,
                o5_i_gates=True,
                o5_t_gates=True,
            )
            print("\n[OK] O0..O4 + O5-I+T gates (180) + unit tests passed")
            return 0
        print("\n[FAIL] O5-T verify failed")
        return 1

    if args.o5_i:
        print("=== data_pc_origin verify: O5-I (O0..O4 + O5-L1-I + unittest) ===\n")
        gates_ok, gate_log = _run_rollup_gates("O5-L1-I")
        for line in gate_log:
            print(line)
        print()
        unit_ok = _run_unit_tests("test_*.py")
        if gates_ok and unit_ok:
            _patch_layer_status(
                o0_gates=True,
                o1_gates=True,
                o2_gates=True,
                o3_gates=True,
                o4_gates=True,
                o5_i_gates=True,
            )
            print("\n[OK] O0..O4 + O5-I gates (153) + unit tests passed")
            return 0
        print("\n[FAIL] O5-I verify failed")
        return 1

    if args.o4:
        print("=== data_pc_origin verify: O4 (O0..O4 gates + unittest) ===\n")
        gates_ok, gate_log = _run_rollup_gates("O4")
        for line in gate_log:
            print(line)
        print()
        unit_ok = _run_unit_tests("test_*.py")
        if gates_ok and unit_ok:
            _patch_layer_status(
                o0_gates=True,
                o1_gates=True,
                o2_gates=True,
                o3_gates=True,
                o4_gates=True,
            )
            print("\n[OK] O0..O4 gates (129) + unit tests passed")
            return 0
        print("\n[FAIL] O4 verify failed")
        return 1

    if args.o3:
        print("=== data_pc_origin verify: O3 (O0..O3 gates + unittest) ===\n")
        gates_ok, gate_log = _run_rollup_gates("O3")
        for line in gate_log:
            print(line)
        print()
        unit_ok = _run_unit_tests("test_*.py")
        if gates_ok and unit_ok:
            _patch_layer_status(o0_gates=True, o1_gates=True, o2_gates=True, o3_gates=True)
            print("\n[OK] O0..O3 gates (121) + unit tests passed")
            return 0
        print("\n[FAIL] O3 verify failed")
        return 1

    if args.o2:
        print("=== data_pc_origin verify: O2 (O0+O1+O2 gates + unittest) ===\n")
        gates_ok, gate_log = _run_rollup_gates("O2")
        for line in gate_log:
            print(line)
        print()
        unit_ok = _run_unit_tests("test_*.py")
        if gates_ok and unit_ok:
            _patch_layer_status(o0_gates=True, o1_gates=True, o2_gates=True)
            print("\n[OK] O0+O1+O2 gates (109) + unit tests passed")
            return 0
        print("\n[FAIL] O2 verify failed")
        return 1

    if args.o1:
        print("=== data_pc_origin verify: O1 (O0+O1 gates + unittest) ===\n")
        gates_ok, gate_log = _run_rollup_gates("O1")
        for line in gate_log:
            print(line)
        print()
        unit_ok = _run_unit_tests("test_*.py")
        if gates_ok and unit_ok:
            _patch_layer_status(o0_gates=True, o1_gates=True)
            print("\n[OK] O0+O1 gates (88) + unit tests passed")
            return 0
        print("\n[FAIL] O1 verify failed")
        return 1

    if args.o0:
        print("=== data_pc_origin verify: O0 (gates + unittest) ===\n")
        gates_ok, gate_log = _run_rollup_gates("O0")
        for line in gate_log:
            print(line)
        print()
        unit_ok = _run_unit_tests("test_*.py")
        if gates_ok and unit_ok:
            _patch_layer_status(o0_gates=True)
            print("\n[OK] O0 gates (61) + unit tests passed")
            return 0
        print("\n[FAIL] O0 verify failed")
        return 1

    print("[info] 기본: O0 (--o0). O1: --o1 · O2: --o2 · O3: --o3 · O4: --o4")
    args.o0 = True
    return main(["--o0"])


if __name__ == "__main__":
    raise SystemExit(main())
