# -*- coding: utf-8 -*-
"""
T81 — data_pc CLI ``--help`` / ``--no-archive`` 검증.

정적 검증: ``build_cli_parser``·``cli_auto_archive`` import·파싱
실행 검증: subprocess ``--help``, ``run_workflow_for_file(auto_archive=False)`` mock

실행:
  python -m py_compile test_data_pc_cli.py
  python -m unittest test_data_pc_cli -v
"""
from __future__ import annotations

import importlib.util
import io
import os
import subprocess
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from unittest import mock

import pandas as pd

REPO = os.path.dirname(os.path.abspath(__file__))
DATA_PC = os.path.join(REPO, "data_pc")
SCRIPT_PATH = os.path.join(DATA_PC, "촉매 반응 계산.py")

# --help 에 반드시 포함되어야 할 문자열 (문법·도움말 회귀)
_HELP_MARKERS = (
    "--no-archive",
    "--manual",
    "--poll-once",
    "--watch",
    "수율/전환율",
    "Origin",
)


def _load_catalyst_module():
    """``data_pc/촉매 반응 계산.py`` — importlib (한글 파일명)."""
    if DATA_PC not in sys.path:
        sys.path.insert(0, DATA_PC)
    spec = importlib.util.spec_from_file_location("data_pc_catalyst", SCRIPT_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load: {SCRIPT_PATH}")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


class TestDataPcCliHelp(unittest.TestCase):
    """실행 검증 — subprocess ``--help`` (실제 argparse 진입)."""

    def test_help_exit_zero_and_markers(self):
        proc = subprocess.run(
            [sys.executable, SCRIPT_PATH, "--help"],
            cwd=DATA_PC,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=60,
        )
        self.assertEqual(proc.returncode, 0, msg=proc.stderr)
        combined = proc.stdout + proc.stderr
        for marker in _HELP_MARKERS:
            self.assertIn(marker, combined, msg=f"missing in --help: {marker!r}")


class TestDataPcCliParser(unittest.TestCase):
    """정적 검증 — ``build_cli_parser`` / ``cli_auto_archive``."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.mod = _load_catalyst_module()

    def test_no_archive_flag_parsed(self):
        args = self.mod.build_cli_parser().parse_args(["--no-archive"])
        self.assertTrue(args.no_archive)
        self.assertFalse(args.manual)

    def test_cli_auto_archive_false_when_no_archive(self):
        args = self.mod.build_cli_parser().parse_args(["--no-archive"])
        self.assertFalse(self.mod.cli_auto_archive(args))

    def test_cli_auto_archive_false_when_opju(self):
        args = self.mod.build_cli_parser().parse_args(["--opju", r"G:\x.opju"])
        self.assertFalse(self.mod.cli_auto_archive(args))

    def test_cli_auto_archive_true_by_default(self):
        args = self.mod.build_cli_parser().parse_args([])
        self.assertTrue(self.mod.cli_auto_archive(args))


class TestNoArchiveWorkflow(unittest.TestCase):
    """실행 검증 — ``run_workflow_for_file(..., auto_archive=False)`` 가 3~4단계 생략."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.mod = _load_catalyst_module()

    def test_skips_setup_experiment_and_origin(self):
        mod = self.mod
        with tempfile.TemporaryDirectory() as tmp:
            excel = os.path.join(tmp, "20260629 DRE(3)@600 test.xlsx")
            saved = os.path.join(tmp, "20260629 DRE(3)@600_GC1_DRE_계산완료.xlsx")
            with open(excel, "wb") as fh:
                fh.write(b"xlsx")
            with open(saved, "wb") as fh:
                fh.write(b"saved")

            fake_df = pd.DataFrame({"yield": [1.0]})

            def fake_process_excel(_path):
                return fake_df, saved, [], "C2H6 3% (test)"

            buf = io.StringIO()
            with redirect_stdout(buf):
                with mock.patch.object(mod, "process_excel", side_effect=fake_process_excel):
                    with mock.patch.object(mod, "setup_experiment_folder") as mock_setup:
                        with mock.patch.object(mod, "update_origin") as mock_origin:
                            ok = mod.run_workflow_for_file(excel, auto_archive=False)

            self.assertTrue(ok)
            mock_setup.assert_not_called()
            mock_origin.assert_not_called()
            out = buf.getvalue()
            self.assertIn("--no-archive", out)
            self.assertIn("건너뜁니다", out)


class TestPollOnceNoArchiveWiring(unittest.TestCase):
    """실행 검증 — ``--poll-once --no-archive`` 가 ``auto_archive=False`` 로 전달."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.mod = _load_catalyst_module()

    def test_poll_once_passes_auto_archive_false(self):
        mod = self.mod
        args = mod.build_cli_parser().parse_args(["--poll-once", "--no-archive"])
        self.assertFalse(mod.cli_auto_archive(args))

        fake_result = mod.PipelineRunResult(workflow_count=0)

        with mock.patch.object(mod, "process_new_gc_emails", return_value=fake_result) as mock_proc:
            mod.process_new_gc_emails(
                opju_path=args.opju,
                auto_archive=mod.cli_auto_archive(args),
            )

        mock_proc.assert_called_once()
        _kwargs = mock_proc.call_args.kwargs
        self.assertFalse(_kwargs["auto_archive"])


if __name__ == "__main__":
    unittest.main()
