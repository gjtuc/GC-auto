# -*- coding: utf-8
import json
import tempfile
import unittest
from pathlib import Path

from data_pc_origin.live_cutover import ARTIFACT_NAME, run_live_cutover
from data_pc_origin.p17_env_config import SKIP_ORIGIN_ENV
from data_pc_origin.p21_cutover import (
    apply_cutover,
    plan_cutover,
    validate_cutover_artifact,
)


class TestP21Cutover(unittest.TestCase):
    def test_plan_detects_skip_origin(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            env = Path(tmp) / "gc_automation.env"
            env.write_text(f"{SKIP_ORIGIN_ENV}=1\nDATA_PC_ORIGIN_PIPELINE=1\n", encoding="utf-8")
            plan = plan_cutover(tmp)
            self.assertFalse(plan.already_production)
            keys = {c["key"] for c in plan.changes}
            self.assertIn(SKIP_ORIGIN_ENV, keys)

    def test_apply_sets_production(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            env = Path(tmp) / "gc_automation.env"
            env.write_text(f"{SKIP_ORIGIN_ENV}=1\nDATA_PC_ORIGIN_PIPELINE=1\n", encoding="utf-8")
            apply_cutover(tmp, backup=True)
            text = env.read_text(encoding="utf-8")
            self.assertIn(f"{SKIP_ORIGIN_ENV}=0", text)
            plan = plan_cutover(tmp)
            self.assertTrue(plan.already_production)


class TestLiveCutover(unittest.TestCase):
    def test_dry_artifact(self) -> None:
        script_dir = str(Path(__file__).resolve().parents[2])
        root = Path(__file__).resolve().parents[1]
        out = run_live_cutover(artifact_dir=root, script_dir=script_dir, dry=True)
        self.assertEqual(out["status"], "ok")
        self.assertTrue(validate_cutover_artifact(out))
        data = json.loads((root / ARTIFACT_NAME).read_text(encoding="utf-8"))
        self.assertIn("before", data)


if __name__ == "__main__":
    unittest.main()
