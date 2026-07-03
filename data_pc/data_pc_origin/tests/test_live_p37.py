# -*- coding: utf-8
import json
import subprocess
import tempfile
import unittest
from pathlib import Path

from data_pc_origin.live_p37_github_push import ARTIFACT_NAME, run_live_p37_github_push
from data_pc_origin.p23_github_snapshot import SNAPSHOT_BRANCH
from data_pc_origin.p37_github_push import (
    plan_github_push_post36,
    validate_github_push_post36_artifact,
)
from data_pc_origin.p36_github_refresh import sync_github_refresh_post35, verify_dest_markers_post35


def _init_feat_branch(repo: Path) -> None:
    subprocess.run(
        ["git", "init", "-b", SNAPSHOT_BRANCH],
        cwd=str(repo),
        check=True,
        capture_output=True,
    )


class TestP37GithubPush(unittest.TestCase):
    def test_plan_real(self) -> None:
        script_dir = str(Path(__file__).resolve().parents[2])
        plan = plan_github_push_post36(script_dir)
        self.assertTrue(plan.push_ready)
        self.assertTrue(plan.dest_markers_ok)
        self.assertGreaterEqual(plan.gate_count, 270)

    def test_plan_after_sync_temp(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            src = Path(tmp) / "src"
            repo = src / "GC-auto-push"
            (src / "data_pc_origin").mkdir(parents=True)
            for name in (
                "verify.py",
                "p34_github_refresh.py",
                "live_p34_github_refresh.py",
                "p35_github_push.py",
                "live_p35_github_push.py",
            ):
                (src / "data_pc_origin" / name).write_text("# x", encoding="utf-8")
            for doc in ("P34.md", "P35.md"):
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
            _init_feat_branch(repo)
            out = sync_github_refresh_post35(str(src), dry_run=False)
            self.assertEqual(out["status"], "ok")
            self.assertTrue(verify_dest_markers_post35(str(src))["ok"])
            plan = plan_github_push_post36(str(src))
            self.assertTrue(plan.push_ready)


class TestLiveP37GithubPush(unittest.TestCase):
    def test_dry_artifact(self) -> None:
        script_dir = str(Path(__file__).resolve().parents[2])
        root = Path(__file__).resolve().parents[1]
        out = run_live_p37_github_push(artifact_dir=root, script_dir=script_dir)
        self.assertIn(out["status"], ("ok", "partial"))
        self.assertTrue(validate_github_push_post36_artifact(out))
        data = json.loads((root / ARTIFACT_NAME).read_text(encoding="utf-8"))
        self.assertTrue(data["plan"]["dest_markers_ok"])


if __name__ == "__main__":
    unittest.main()
