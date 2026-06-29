# -*- coding: utf-8 -*-
"""Registry + runner tests."""

from __future__ import annotations

import unittest

from data_pc_origin.gates.implementations import ensure_gates_loaded
from data_pc_origin.gates.registry import (
    O0_IMPLEMENTATION_ORDER,
    ROLLUPS,
    get_gate,
    locked_reason,
)
from data_pc_origin.gates.runner import run_gate, run_rollup


class TestRegistry(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        ensure_gates_loaded()

    def test_o0_c_gate_count(self) -> None:
        from data_pc_origin.gates.registry import O0_C_GATES

        self.assertEqual(len(O0_C_GATES), 16)

    def test_o0_i_gate_count(self) -> None:
        from data_pc_origin.gates.registry import O0_I_GATES

        self.assertEqual(len(O0_I_GATES), 14)

    def test_o0_gate_count(self) -> None:
        self.assertEqual(len(O0_IMPLEMENTATION_ORDER), 71)

    def test_o1_gate_count(self) -> None:
        from data_pc_origin.gates.registry import O1_IMPLEMENTATION_ORDER

        self.assertEqual(len(O1_IMPLEMENTATION_ORDER), 27)

    def test_o2_gate_count(self) -> None:
        from data_pc_origin.gates.registry import O2_IMPLEMENTATION_ORDER

        self.assertEqual(len(O2_IMPLEMENTATION_ORDER), 21)

    def test_o3_gate_count(self) -> None:
        from data_pc_origin.gates.registry import O3_IMPLEMENTATION_ORDER

        self.assertEqual(len(O3_IMPLEMENTATION_ORDER), 12)

    def test_o5_i_gate_count(self) -> None:
        from data_pc_origin.gates.registry import O5_I_GATES

        self.assertEqual(len(O5_I_GATES), 24)

    def test_o5_t_gate_count(self) -> None:
        from data_pc_origin.gates.registry import O5_T_GATES

        self.assertEqual(len(O5_T_GATES), 27)

    def test_o5_m_gate_count(self) -> None:
        from data_pc_origin.gates.registry import O5_M_GATES

        self.assertEqual(len(O5_M_GATES), 54)

    def test_o5_core_gate_count(self) -> None:
        from data_pc_origin.gates.registry import O5_IMPLEMENTATION_ORDER

        self.assertEqual(len(O5_IMPLEMENTATION_ORDER), 105)

    def test_rollup_o0_l1_k(self) -> None:
        self.assertEqual(len(ROLLUPS["O0-L1-K"]), 9)

    def test_first_gate_no_lock(self) -> None:
        self.assertIsNone(locked_reason("O0-K-01-a-1", frozenset()))

    def test_second_gate_locked_without_first(self) -> None:
        reason = locked_reason("O0-K-01-b-1", frozenset())
        self.assertEqual(reason, "O0-K-01-a-1")

    def test_all_gates_registered(self) -> None:
        for gid in O0_IMPLEMENTATION_ORDER:
            spec = get_gate(gid)
            self.assertEqual(spec.gate_id, gid)


class TestRunner(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        ensure_gates_loaded()

    def test_run_first_gate(self) -> None:
        code, passed = run_gate("O0-K-01-a-1")
        self.assertEqual(code, 0)
        self.assertIn("O0-K-01-a-1", passed)

    def test_run_o0_l1_k_rollup(self) -> None:
        code, log, passed = run_rollup("O0-L1-K")
        self.assertEqual(code, 0, msg="\n".join(log))
        self.assertEqual(len(passed), 9)

    def test_run_full_o0_rollup(self) -> None:
        code, log, passed = run_rollup("O0")
        self.assertEqual(code, 0, msg="\n".join(log))
        self.assertEqual(len(passed), 71)

    def test_run_o1_p_rollup(self) -> None:
        code, log, passed = run_rollup("O1-P")
        self.assertEqual(code, 0, msg="\n".join(log))
        self.assertEqual(len(passed), 71 + 15)

    def test_run_o2_e_rollup(self) -> None:
        code, log, passed = run_rollup("O2-E")
        self.assertEqual(code, 0, msg="\n".join(log))
        self.assertEqual(len(passed), 98 + 6)

    def test_run_o3_s_rollup(self) -> None:
        code, log, passed = run_rollup("O3-S")
        self.assertEqual(code, 0, msg="\n".join(log))
        self.assertEqual(len(passed), 119 + 8)


    def test_run_o5_l1_i_rollup(self) -> None:
        code, log, passed = run_rollup("O5-L1-I")
        self.assertEqual(code, 0, msg="\n".join(log))
        self.assertEqual(len(passed), 139 + 24)

    def test_run_o5_l1_m_rollup(self) -> None:
        code, log, passed = run_rollup("O5-L1-M")
        self.assertEqual(code, 0, msg="\n".join(log))
        self.assertEqual(len(passed), 139 + 105)


if __name__ == "__main__":
    unittest.main()
