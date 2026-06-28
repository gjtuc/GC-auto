# -*- coding: utf-8
import json
import os
import unittest
from pathlib import Path

from data_pc_origin.live_runtime import ARTIFACT_NAME, run_live_runtime
from data_pc_origin.p14_runtime_bridge import (
    ORIGIN_PIPELINE_ENV,
    origin_pipeline_enabled,
    parse_imap_workflow_result,
    resolve_job_pipeline,
    run_runtime_pipeline_once,
)

RUNTIME_LIVE = os.getenv("DATA_PC_RUNTIME_LIVE", "").strip().lower() in (
    "1",
    "true",
    "yes",
)


class TestP14RuntimeBridge(unittest.TestCase):
    def test_parse_imap_ok(self) -> None:
        parsed = parse_imap_workflow_result({"status": "ok", "workflow_ok": True})
        self.assertEqual(parsed.workflow_count, 1)
        self.assertFalse(parsed.gdrive_retry_needed)

    def test_parse_imap_gdrive_skip(self) -> None:
        parsed = parse_imap_workflow_result(
            {"status": "skipped", "reason": "G: drive not available"}
        )
        self.assertTrue(parsed.gdrive_retry_needed)

    def test_origin_pipeline_env_flag(self) -> None:
        self.assertFalse(origin_pipeline_enabled({ORIGIN_PIPELINE_ENV: "0"}))
        self.assertTrue(origin_pipeline_enabled({ORIGIN_PIPELINE_ENV: "1"}))

    def test_resolve_legacy_pipeline(self) -> None:
        script_dir = str(Path(__file__).resolve().parents[2])
        cb = resolve_job_pipeline(
            script_dir,
            environ={ORIGIN_PIPELINE_ENV: "0"},
        )
        self.assertTrue(callable(cb))

    def test_resolve_origin_pipeline(self) -> None:
        script_dir = str(Path(__file__).resolve().parents[2])
        cb = resolve_job_pipeline(
            script_dir,
            environ={ORIGIN_PIPELINE_ENV: "1"},
        )
        self.assertTrue(callable(cb))


class TestLiveRuntime(unittest.TestCase):
    def test_dry_pipeline(self) -> None:
        root = Path(__file__).resolve().parents[1]
        out = run_live_runtime(artifact_dir=root, dry_run=True)
        self.assertEqual(out["status"], "dry_run")
        self.assertEqual(out["mode"], "dry")
        data = json.loads((root / ARTIFACT_NAME).read_text(encoding="utf-8"))
        self.assertIn("pipeline", data)

    def test_dry_job_runner(self) -> None:
        root = Path(__file__).resolve().parents[1]
        out = run_live_runtime(artifact_dir=root, dry_job=True)
        self.assertEqual(out["mode"], "dry_job")
        self.assertTrue(out.get("job_ran"))
        self.assertEqual(out.get("job_status_code"), "pipeline_done")

    def test_runtime_pipeline_dry_once(self) -> None:
        result = run_runtime_pipeline_once(dry_run=True, printer=lambda _: None)
        self.assertEqual(result.workflow_count, 0)
        self.assertFalse(result.gdrive_retry_needed)

    @unittest.skipUnless(RUNTIME_LIVE, "set DATA_PC_RUNTIME_LIVE=1 for live runtime bridge")
    def test_live_runtime_if_env(self) -> None:
        root = Path(__file__).resolve().parents[1]
        os.environ[ORIGIN_PIPELINE_ENV] = "1"
        out = run_live_runtime(artifact_dir=root, dry_run=False)
        self.assertIn(out["status"], ("ok", "skipped", "error"))


if __name__ == "__main__":
    unittest.main()
