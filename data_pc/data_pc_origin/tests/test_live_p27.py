# -*- coding: utf-8
import json
import tempfile
import unittest
from pathlib import Path

from data_pc_origin.live_github_refresh import ARTIFACT_NAME, run_live_github_refresh
from data_pc_origin.p27_github_refresh import (
    plan_github_refresh,
    sync_github_refresh,
    validate_github_refresh_artifact,
    verify_dest_markers,
)


class TestP27GithubRefresh(unittest.TestCase):
    def test_plan_real(self) -> None:
        script_dir = str(Path(__file__).resolve().parents[2])
        plan = plan_github_refresh(script_dir)
        self.assertTrue(plan.markers_ready)
        self.assertGreaterEqual(plan.gate_count, 190)

    def test_sync_temp(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            src = Path(tmp) / "src"
            repo = src / "GC-auto-push"
            (src / "data_pc_origin").mkdir(parents=True)
            for name in (
                "verify.py",
                "p26_watch_resident.py",
                "live_watch_resident.py",
                "p24_ops_rollup.py",
                "live_ops_rollup.py",
                "p25_native_live.py",
                "live_native_production.py",
            ):
                (src / "data_pc_origin" / name).write_text("# x", encoding="utf-8")
            for doc in ("P24.md", "P25.md", "P26.md"):
                (src / "data_pc_origin" / "design" / "catalog").mkdir(parents=True, exist_ok=True)
                (src / "data_pc_origin" / "design" / "catalog" / doc).write_text("# d", encoding="utf-8")
            (src / "data_pc_runtime").mkdir()
            (src / "data_pc_runtime" / "verify.py").write_text("# r", encoding="utf-8")
            (src / "data_pc_watch.py").write_text("# w", encoding="utf-8")
            (src / "data_pc_watchdog.py").write_text("# d", encoding="utf-8")
            (src / "촉매 반응 계산.py").write_text("# c", encoding="utf-8")
            for bat in (
                "gc_data_pc_watch_loop.bat",
                "gc_data_pc_ensure_watch.bat",
                "gc_data_pc_ensure_watch_hidden.vbs",
                "gc_data_pc_start_watch_hidden.vbs",
            ):
                (src / bat).write_text("x", encoding="utf-8")
            repo.mkdir()
            (repo / ".git").mkdir()
            out = sync_github_refresh(str(src), dry_run=False)
            self.assertEqual(out["status"], "ok")
            self.assertTrue(verify_dest_markers(str(src))["ok"])


class TestLiveGithubRefresh(unittest.TestCase):
    def test_dry_artifact(self) -> None:
        script_dir = str(Path(__file__).resolve().parents[2])
        root = Path(__file__).resolve().parents[1]
        out = run_live_github_refresh(artifact_dir=root, script_dir=script_dir)
        self.assertIn(out["status"], ("ok", "partial"))
        self.assertTrue(validate_github_refresh_artifact(out))
        data = json.loads((root / ARTIFACT_NAME).read_text(encoding="utf-8"))
        self.assertTrue(data["plan"]["markers_ready"])


if __name__ == "__main__":
    unittest.main()
