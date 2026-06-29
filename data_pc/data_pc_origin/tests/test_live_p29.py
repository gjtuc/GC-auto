# -*- coding: utf-8
import json
import tempfile
import unittest
from pathlib import Path

from data_pc_origin.live_p29_github_refresh import ARTIFACT_NAME, run_live_p29_github_refresh
from data_pc_origin.p29_github_refresh import (
    plan_github_refresh_post28,
    sync_github_refresh_post28,
    validate_github_refresh_post28_artifact,
    verify_dest_markers_post28,
)


class TestP29GithubRefresh(unittest.TestCase):
    def test_plan_real(self) -> None:
        script_dir = str(Path(__file__).resolve().parents[2])
        plan = plan_github_refresh_post28(script_dir)
        self.assertTrue(plan.markers_ready)
        self.assertGreaterEqual(plan.gate_count, 206)

    def test_sync_temp(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            src = Path(tmp) / "src"
            repo = src / "GC-auto-push"
            (src / "data_pc_origin").mkdir(parents=True)
            for name in (
                "verify.py",
                "p27_github_refresh.py",
                "live_github_refresh.py",
                "p28_merge_readiness.py",
                "live_merge_readiness.py",
            ):
                (src / "data_pc_origin" / name).write_text("# x", encoding="utf-8")
            for doc in ("P27.md", "P28.md"):
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
            out = sync_github_refresh_post28(str(src), dry_run=False)
            self.assertEqual(out["status"], "ok")
            self.assertTrue(verify_dest_markers_post28(str(src))["ok"])


class TestLiveP29GithubRefresh(unittest.TestCase):
    def test_dry_artifact(self) -> None:
        script_dir = str(Path(__file__).resolve().parents[2])
        root = Path(__file__).resolve().parents[1]
        out = run_live_p29_github_refresh(artifact_dir=root, script_dir=script_dir)
        self.assertIn(out["status"], ("ok", "partial"))
        self.assertTrue(validate_github_refresh_post28_artifact(out))
        data = json.loads((root / ARTIFACT_NAME).read_text(encoding="utf-8"))
        self.assertTrue(data["plan"]["markers_ready"])


if __name__ == "__main__":
    unittest.main()
