# -*- coding: utf-8 -*-
"""T24 — gc1_runtime.layer2_gates (G-EX + G-ATOM stub) 테스트."""
from __future__ import annotations

import unittest

from gc1_runtime.layer2_gates import (
    AtomGateInput,
    ExportGateInput,
    GateAction,
    GateEvaluator,
)


def _run_ready(**kwargs: object) -> ExportGateInput:
    """기본 RUN 가능 컨텍스트."""
    base = dict(
        autochro_enabled=True,
        force=False,
        is_data_pc=False,
        prep_enabled=True,
        autochro_window_handles=1,
        mtd_path_exists=True,
        crm_export_needed=True,
        pipeline_locked=False,
    )
    base.update(kwargs)
    return ExportGateInput(**base)  # type: ignore[arg-type]


class TestGateExport(unittest.TestCase):
    def setUp(self) -> None:
        self.ev = GateEvaluator()

    def test_run_all_gates_pass(self):
        v = self.ev.evaluate_export(_run_ready())
        self.assertEqual(v.action, GateAction.RUN)
        self.assertTrue(v.ok_to_run)
        self.assertIsNone(v.fail_code)

    def test_g1_skip_disabled(self):
        v = self.ev.evaluate_export(_run_ready(autochro_enabled=False))
        self.assertEqual(v.action, GateAction.SKIP)
        self.assertEqual(v.gate_id, "Ω.A.L2.GEX.01")

    def test_g1_force_overrides_disabled(self):
        v = self.ev.evaluate_export(
            _run_ready(autochro_enabled=False, force=True),
        )
        self.assertEqual(v.action, GateAction.RUN)

    def test_g2_data_pc_block(self):
        v = self.ev.evaluate_export(_run_ready(is_data_pc=True))
        self.assertEqual(v.action, GateAction.BLOCK)
        self.assertEqual(v.fail_code, "E_IDENT_CROSS_PC")

    def test_g3_no_window_block(self):
        v = self.ev.evaluate_export(_run_ready(autochro_window_handles=0))
        self.assertEqual(v.fail_code, "E_WIN_NONE")

    def test_g4_mtd_missing_when_prep(self):
        v = self.ev.evaluate_export(_run_ready(mtd_path_exists=False))
        self.assertEqual(v.fail_code, "E_MTD_MISSING")

    def test_g4_skip_mtd_when_not_prep(self):
        v = self.ev.evaluate_export(
            _run_ready(prep_enabled=False, mtd_path_exists=False),
        )
        self.assertEqual(v.action, GateAction.RUN)

    def test_g5_skip_crm_fresh(self):
        v = self.ev.evaluate_export(_run_ready(crm_export_needed=False))
        self.assertEqual(v.action, GateAction.SKIP)
        self.assertEqual(v.gate_id, "Ω.A.L2.GEX.05")

    def test_g5_force_bypasses_crm_skip(self):
        v = self.ev.evaluate_export(
            _run_ready(crm_export_needed=False, force=True),
        )
        self.assertEqual(v.action, GateAction.RUN)

    def test_g6_pipeline_locked(self):
        v = self.ev.evaluate_export(_run_ready(pipeline_locked=True))
        self.assertEqual(v.fail_code, "E_PIPELINE_BUSY")


class TestGateAtomStub(unittest.TestCase):
    def setUp(self) -> None:
        self.ev = GateEvaluator()

    def test_pre_all_true(self):
        v = self.ev.evaluate_atom_pre((True, True))
        self.assertEqual(v.action, GateAction.RUN)

    def test_pre_one_false_blocks(self):
        v = self.ev.evaluate_atom_pre((True, False))
        self.assertEqual(v.action, GateAction.BLOCK)
        self.assertEqual(v.fail_code, "E_PRE_PROBE")

    def test_pre_empty_passes(self):
        v = self.ev.evaluate_atom_pre(())
        self.assertEqual(v.action, GateAction.RUN)

    def test_post_via_atom_gate_input(self):
        v = self.ev.evaluate_atom_post(AtomGateInput(post_probes=(True,)))
        self.assertTrue(v.ok_to_run)

    def test_should_retry_stub(self):
        self.assertTrue(self.ev.should_retry(1, 3))
        self.assertFalse(self.ev.should_retry(3, 3))


if __name__ == "__main__":
    unittest.main()
