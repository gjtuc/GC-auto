# -*- coding: utf-8 -*-
"""
T88 — ``layer0_ident`` Ω.B.IDENT + G-EX.02 연동 검증.
T89 — IDENT.01~08 ``read_ident_snapshot`` + resolve_profile mock.

정적: role 판별·경로 확장·CMP 헬퍼
실행: temp profile JSON · gate · snapshot · probe CLI

실행:
  python -m unittest test_gc1_runtime_layer0_ident -v
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import unittest
from types import SimpleNamespace
from unittest import mock

from gc1_runtime.layer0_ident import (
    IdentSnapshot,
    detect_data_pc,
    detect_machine_role,
    expand_profile_paths,
    is_data_pc_role,
    is_gc1_chemstation_mode,
    is_gc1_instance,
    is_gc_equipment_role,
    load_machine_profile,
    read_ident_snapshot,
    read_machine_role,
)
from gc1_runtime.layer2_gates import GateAction, GateEvaluator
from gc1_runtime.layer4_job import build_export_gate_input


class TestLayer0IdentStatic(unittest.TestCase):
    """정적 검증 — role 헬퍼."""

    def test_role_classifiers(self):
        self.assertTrue(is_data_pc_role("data_pc"))
        self.assertFalse(is_data_pc_role("gc1_pc"))
        self.assertTrue(is_gc_equipment_role("gc1_pc"))
        self.assertTrue(is_gc_equipment_role("gc2_pc"))

    def test_ident_cmp_leaves(self):
        self.assertTrue(is_gc1_instance("gc1"))
        self.assertFalse(is_gc1_instance("gc2"))
        self.assertTrue(is_gc1_chemstation_mode("gc1"))
        self.assertFalse(is_gc1_chemstation_mode("8860"))

    def test_expand_profile_paths_under_home(self):
        with tempfile.TemporaryDirectory() as home:
            paths = expand_profile_paths(home=home)
            self.assertTrue(any(p.endswith("machine_profile.json") for p in paths))
            self.assertTrue(all(p.startswith(home) for p in paths))


class TestLayer0IdentExecution(unittest.TestCase):
    """실행 검증 — temp profile · gate."""

    def test_read_data_pc_profile(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "machine_profile.json")
            with open(path, "w", encoding="utf-8") as fh:
                json.dump({"role": "data_pc"}, fh)
            self.assertEqual(read_machine_role(path), "data_pc")
            self.assertTrue(detect_data_pc([path]))

    def test_gc1_equipment_profile_wins_over_stray_data_pc(self):
        """GC1 PC + Desktop\\.cursor\\KCH data_pc 사본 — 장비 role 우선."""
        with tempfile.TemporaryDirectory() as home:
            gc1 = os.path.join(home, "Desktop", "박은규", "machine_profile.json")
            stray = os.path.join(home, "Desktop", ".cursor", "KCH", "machine_profile.json")
            os.makedirs(os.path.dirname(gc1), exist_ok=True)
            os.makedirs(os.path.dirname(stray), exist_ok=True)
            with open(gc1, "w", encoding="utf-8") as fh:
                json.dump({"role": "gc1_pc"}, fh)
            with open(stray, "w", encoding="utf-8") as fh:
                json.dump({"role": "data_pc"}, fh)
            self.assertFalse(detect_data_pc(home=home))

    def test_pure_data_pc_without_gc1_profile(self):
        with tempfile.TemporaryDirectory() as home:
            peg = os.path.join(home, "gc-data-pc", "PEG", "machine_profile.json")
            os.makedirs(os.path.dirname(peg), exist_ok=True)
            with open(peg, "w", encoding="utf-8") as fh:
                json.dump({"role": "data_pc"}, fh)
            self.assertTrue(detect_data_pc(home=home))

    def test_gc1_profile_not_data_pc(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "machine_profile.json")
            with open(path, "w", encoding="utf-8") as fh:
                json.dump({"role": "gc1_pc"}, fh)
            self.assertEqual(detect_machine_role([path]), "gc1_pc")
            self.assertFalse(detect_data_pc([path]))

    def test_missing_profile_returns_none(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "missing.json")
            self.assertIsNone(load_machine_profile(path))
            self.assertFalse(detect_data_pc([path]))

    def test_gex_blocks_data_pc(self):
        """G-EX.02 — ``build_export_gate_input`` + ``GateEvaluator``."""
        cfg = SimpleNamespace(enabled=True)
        with mock.patch("gc1_runtime.layer4_job.detect_data_pc", return_value=True):
            gate_in = build_export_gate_input(
                cfg=cfg,
                force=False,
                prep_enabled=True,
                crm_export_needed=True,
                window_handles=1,
                mtd_path_exists=True,
            )
        verdict = GateEvaluator().evaluate_export(gate_in)
        self.assertEqual(verdict.action, GateAction.BLOCK)
        self.assertEqual(verdict.fail_code, "E_IDENT_CROSS_PC")


class TestIdentSnapshot(unittest.TestCase):
    """T89 — ``read_ident_snapshot`` 실행 검증."""

    def _fake_resolve(self, instance: str = "gc1", mode: str = "gc1") -> SimpleNamespace:
        return SimpleNamespace(
            gc_instance=instance,
            chemstation_mode=mode,
            excel_output_dir=r"C:\fake\박은규",
            env_file=r"C:\fake\박은규\gc_automation.env",
        )

    def test_snapshot_gc1_ok(self):
        with tempfile.TemporaryDirectory() as home:
            repo = os.path.join(home, "repo")
            os.makedirs(repo)
            env_dir = os.path.join(home, "Desktop", "박은규")
            os.makedirs(env_dir)
            open(os.path.join(env_dir, "gc_automation.env"), "w", encoding="utf-8").close()
            prof = os.path.join(env_dir, "machine_profile.json")
            with open(prof, "w", encoding="utf-8") as fh:
                json.dump({"role": "gc1_pc"}, fh)

            snap = read_ident_snapshot(
                repo_root=repo,
                home=home,
                resolve_fn=lambda: self._fake_resolve(),
            )
            self.assertIsInstance(snap, IdentSnapshot)
            self.assertTrue(snap.repo_root_exists)
            self.assertTrue(snap.gc1_env_exists)
            self.assertEqual(snap.machine_role, "gc1_pc")
            self.assertTrue(snap.is_gc1_instance)
            self.assertTrue(snap.is_not_data_pc)
            self.assertTrue(snap.is_gc1_mode)
            self.assertTrue(snap.ok_for_gc1_autochro)
            d = snap.to_dict()
            self.assertIn("ok_for_gc1_autochro", d)
            self.assertTrue(d["ok_for_gc1_autochro"])

    def test_snapshot_wrong_instance(self):
        with tempfile.TemporaryDirectory() as home:
            repo = os.path.join(home, "repo")
            os.makedirs(repo)
            snap = read_ident_snapshot(
                repo_root=repo,
                home=home,
                resolve_fn=lambda: self._fake_resolve(instance="gc2", mode="8860"),
            )
            self.assertFalse(snap.is_gc1_instance)
            self.assertFalse(snap.is_gc1_mode)
            self.assertFalse(snap.ok_for_gc1_autochro)


class TestProbeGc1IdentScript(unittest.TestCase):
    """probe_gc1_ident.py — subprocess 실행 검증."""

    def test_probe_cli_runs(self):
        repo = os.path.dirname(os.path.abspath(__file__))
        script = os.path.join(repo, "scripts", "probe_gc1_ident.py")
        proc = subprocess.run(
            [sys.executable, script, "--pretty"],
            cwd=repo,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=30,
        )
        self.assertEqual(proc.returncode, 0, msg=proc.stderr or proc.stdout)
        data = json.loads(proc.stdout)
        self.assertIn("gc_instance", data)
        self.assertTrue(data.get("repo_root_exists"))


if __name__ == "__main__":
    unittest.main()
