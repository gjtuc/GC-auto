# -*- coding: utf-8
import json
import unittest
from pathlib import Path

from data_pc_origin.live_env import ARTIFACT_NAME, run_live_env
from data_pc_origin.p14_runtime_bridge import ORIGIN_PIPELINE_ENV
from data_pc_origin.p17_env_config import (
    ORIGIN_ENV_DEFAULTS,
    effective_origin_config,
    env_file_documents_origin_stack,
    mask_env_value,
    merge_origin_defaults_into_text,
)


class TestP17EnvConfig(unittest.TestCase):
    def test_defaults_origin_on(self) -> None:
        self.assertEqual(ORIGIN_ENV_DEFAULTS[ORIGIN_PIPELINE_ENV], "1")

    def test_mask_secrets(self) -> None:
        self.assertEqual(mask_env_value("NAVER_APP_PASSWORD", "abc"), "***")

    def test_full_e2e_flag(self) -> None:
        script_dir = str(Path(__file__).resolve().parents[2])
        cfg = effective_origin_config(
            script_dir,
            environ={ORIGIN_PIPELINE_ENV: "1", "DATA_PC_SKIP_ORIGIN": "0"},
        )
        self.assertTrue(cfg["full_e2e_ready"])

    def test_merge_defaults_block(self) -> None:
        merged = merge_origin_defaults_into_text("FOO=1\n")
        self.assertIn(ORIGIN_PIPELINE_ENV, merged)


class TestLiveEnv(unittest.TestCase):
    def test_run_live_env_artifact(self) -> None:
        root = Path(__file__).resolve().parents[1]
        script_dir = str(root.parent)
        out = run_live_env(artifact_dir=root, script_dir=script_dir)
        self.assertEqual(out["status"], "ok")
        data = json.loads((root / ARTIFACT_NAME).read_text(encoding="utf-8"))
        self.assertTrue(data["origin_stack_documented"])
        blob = json.dumps(data)
        self.assertNotIn("Y1YV", blob)
        self.assertNotIn("password=", blob.lower())
        self.assertTrue(data["origin_pipeline"])


if __name__ == "__main__":
    unittest.main()
