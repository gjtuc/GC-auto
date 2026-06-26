# -*- coding: utf-8 -*-
"""O2 env·lock·gate chain 단위 + 실행 검증."""

from __future__ import annotations

import os
import tempfile
import unittest
from pathlib import Path

from data_pc_origin.o0_types import ProbeResult
from data_pc_origin.o2_env import skip_origin_active, parse_bool_env, read_env_raw
from data_pc_origin.o2_gate_chain import evaluate_origin_gate
from data_pc_origin.o2_origin_lock import OriginLock
from data_pc_origin.o2_pipeline_lock import pipeline_busy, read_pipeline_lock


class TestO2Env(unittest.TestCase):
    def test_read_unset(self) -> None:
        self.assertEqual(read_env_raw("NO_SUCH_ENV_X", environ={}), "")

    def test_parse_bool(self) -> None:
        self.assertTrue(parse_bool_env("yes"))
        self.assertFalse(parse_bool_env("no"))

    def test_skip_origin(self) -> None:
        self.assertTrue(skip_origin_active(environ={"DATA_PC_SKIP_ORIGIN": "1"}))
        self.assertFalse(skip_origin_active(environ={"DATA_PC_SKIP_ORIGIN": "0"}))


class TestO2Lock(unittest.TestCase):
    def test_origin_lock_acquire_release(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            lock = os.path.join(tmp, "t.lock")
            with OriginLock(lock):
                self.assertTrue(os.path.isfile(lock))
            self.assertFalse(os.path.isfile(lock))

    def test_pipeline_busy_current_pid(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            lock = os.path.join(tmp, "p.lock")
            Path(lock).write_text(str(os.getpid()), encoding="ascii")
            self.assertTrue(pipeline_busy(lock))
            status = read_pipeline_lock(lock)
            self.assertTrue(status.busy)


class TestO2GateChain(unittest.TestCase):
    def test_skip_origin_verdict(self) -> None:
        v = evaluate_origin_gate(
            opju_probe=ProbeResult(True),
            pipeline_lock_path="/x",
            origin_lock_path="/y",
            skip_origin=True,
            acquire_origin_lock=False,
        )
        self.assertEqual(v.code, "skip_origin")

    def test_ready_when_clear(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            v = evaluate_origin_gate(
                opju_probe=ProbeResult(True, "ok"),
                pipeline_lock_path=os.path.join(tmp, "free.pipe"),
                origin_lock_path=os.path.join(tmp, "free.origin"),
                skip_origin=False,
                acquire_origin_lock=True,
            )
            self.assertEqual(v.code, "ready")


class TestO2RuntimeImport(unittest.TestCase):
    """모듈 import·CLI 노출 — 실행 검증."""

    def test_import_o2_modules(self) -> None:
        import data_pc_origin.o2_env as env
        import data_pc_origin.o2_gate_chain as chain
        import data_pc_origin.o2_origin_lock as ol
        import data_pc_origin.o2_paths as paths

        self.assertTrue(callable(env.skip_origin_active))
        self.assertTrue(callable(chain.evaluate_origin_gate))
        self.assertTrue(hasattr(ol, "OriginLock"))
        self.assertIn(".origin_update.lock", paths.origin_lock_path(Path("/tmp/k")))


if __name__ == "__main__":
    unittest.main()
