# -*- coding: utf-8
import json
import tempfile
import unittest
from pathlib import Path

from data_pc_origin.live_github_snapshot import ARTIFACT_NAME, run_live_github_snapshot
from data_pc_origin.p23_github_snapshot import (
    plan_github_snapshot,
    sync_snapshot,
    validate_github_snapshot_artifact,
)


class TestP23GithubSnapshot(unittest.TestCase):
    def _seed_src(self, src: Path) -> None:
        (src / "data_pc_origin").mkdir(parents=True)
        (src / "data_pc_origin" / "verify.py").write_text("# v\n", encoding="utf-8")
        (src / "data_pc_runtime").mkdir()
        (src / "data_pc_runtime" / "verify.py").write_text("# r\n", encoding="utf-8")
        (src / "data_pc_watch.py").write_text("# w\n", encoding="utf-8")
        (src / "data_pc_watchdog.py").write_text("# d\n", encoding="utf-8")
        (src / "촉매 반응 계산.py").write_text("# c\n", encoding="utf-8")
        for name in (
            "gc_data_pc_watch_loop.bat",
            "gc_data_pc_ensure_watch.bat",
            "gc_data_pc_ensure_watch_hidden.vbs",
            "gc_data_pc_start_watch_hidden.vbs",
        ):
            (src / name).write_text("rem\n", encoding="utf-8")

    def test_plan_ready_real_repo(self) -> None:
        script_dir = str(Path(__file__).resolve().parents[2])
        plan = plan_github_snapshot(script_dir)
        self.assertTrue(plan.ready)
        self.assertGreaterEqual(plan.gate_count, 158)

    def test_sync_to_temp_repo(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            src = Path(tmp) / "src"
            repo = src / "GC-auto-push"
            self._seed_src(src)
            repo.mkdir()
            (repo / ".git").mkdir()
            out = sync_snapshot(str(src), dry_run=False)
            self.assertEqual(out["status"], "ok")
            self.assertTrue((repo / "data_pc" / "data_pc_origin" / "verify.py").is_file())


class TestLiveGithubSnapshot(unittest.TestCase):
    def test_dry_artifact(self) -> None:
        script_dir = str(Path(__file__).resolve().parents[2])
        root = Path(__file__).resolve().parents[1]
        out = run_live_github_snapshot(artifact_dir=root, script_dir=script_dir)
        self.assertIn(out["status"], ("ok", "partial"))
        self.assertTrue(validate_github_snapshot_artifact(out))
        data = json.loads((root / ARTIFACT_NAME).read_text(encoding="utf-8"))
        self.assertIn("plan", data)


if __name__ == "__main__":
    unittest.main()
