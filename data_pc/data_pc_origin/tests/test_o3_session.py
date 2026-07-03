# -*- coding: utf-8 -*-
"""O3 session — 단위 + 실행 검증 (mock originpro)."""

from __future__ import annotations

import unittest
from types import ModuleType, SimpleNamespace

from data_pc_origin.o3_import import import_originpro, reset_originpro_cache
from data_pc_origin.o3_plugins import DialogReadonlyPlugin, PluginRegistry, RetryOpenPlugin
from data_pc_origin.o3_session import OriginSession, is_origin_gui_running, kill_stale_origin_gui
from data_pc_origin.o3_session import (
    OriginGuiBusyError,
    ensure_origin_gui_clear_for_com,
    wait_origin_gui_stopped,
)


def _fake_op() -> ModuleType:
    class FakeOp(SimpleNamespace):
        def set_show(self, value: bool) -> None:
            self.show = value

        def oext(self, value: bool) -> None:
            self.oext_calls = getattr(self, "oext_calls", []) + [value]

        def exit(self) -> None:
            self.exited = True

    return FakeOp()  # type: ignore[return-value]


class TestO3Import(unittest.TestCase):
    def setUp(self) -> None:
        reset_originpro_cache()

    def tearDown(self) -> None:
        reset_originpro_cache()

    def test_cache_hit(self) -> None:
        n = {"c": 0}

        def imp() -> ModuleType:
            n["c"] += 1
            return _fake_op()

        a = import_originpro(importer=imp)
        b = import_originpro(importer=imp)
        self.assertIs(a, b)
        self.assertEqual(n["c"], 1)


class TestO3Session(unittest.TestCase):
    def test_with_block(self) -> None:
        op = _fake_op()
        with OriginSession(importer=lambda: op) as entered:
            self.assertIs(entered, op)
            self.assertFalse(op.show)
        self.assertTrue(getattr(op, "exited", False))

    def test_exit_on_exception(self) -> None:
        op = _fake_op()
        with self.assertRaises(ValueError):
            with OriginSession(importer=lambda: op):
                raise ValueError("boom")
        self.assertTrue(getattr(op, "exited", False))

    def test_kill_without_allow_is_noop(self) -> None:
        import unittest.mock

        with unittest.mock.patch(
            "data_pc_origin.o3_session.is_origin_gui_running",
            return_value=True,
        ):
            with unittest.mock.patch("data_pc_origin.o3_session.subprocess.run") as run:
                self.assertEqual(kill_stale_origin_gui(), 0)
                run.assert_not_called()

    def test_kill_with_allow_calls_taskkill(self) -> None:
        import unittest.mock

        with unittest.mock.patch(
            "data_pc_origin.o3_session.is_origin_gui_running",
            return_value=True,
        ):
            with unittest.mock.patch(
                "data_pc_origin.o3_session._origin_has_unsaved_changes",
                return_value=False,
            ):
                with unittest.mock.patch("data_pc_origin.o3_session.subprocess.run") as run:
                    run.return_value = unittest.mock.Mock(returncode=0)
                    with unittest.mock.patch("data_pc_origin.o3_session.time.sleep"):
                        n = kill_stale_origin_gui(allow_kill=True)
                    self.assertEqual(n, 2)
                    self.assertGreaterEqual(run.call_count, 2)

    def test_ensure_clear_when_stopped(self) -> None:
        import unittest.mock

        with unittest.mock.patch(
            "data_pc_origin.o3_session.is_origin_gui_running",
            return_value=False,
        ):
            self.assertTrue(ensure_origin_gui_clear_for_com())

    def test_ensure_clear_raises_when_keep_gui(self) -> None:
        import os
        import unittest.mock

        with unittest.mock.patch.dict(os.environ, {"DATA_PC_KEEP_ORIGIN_GUI": "1"}):
            with unittest.mock.patch(
                "data_pc_origin.o3_session.is_origin_gui_running",
                return_value=True,
            ):
                with self.assertRaises(OriginGuiBusyError):
                    ensure_origin_gui_clear_for_com(allow_kill=False)

    def test_save_and_force_quit_when_stopped(self) -> None:
        import unittest.mock

        with unittest.mock.patch(
            "data_pc_origin.o3_session.is_origin_gui_running",
            return_value=False,
        ):
            from data_pc_origin.o3_session import save_and_force_quit_origin_gui

            self.assertTrue(save_and_force_quit_origin_gui())

    def test_wait_origin_stopped(self) -> None:
        import unittest.mock

        seq = iter([True, True, False])

        def running() -> bool:
            return next(seq, False)

        with unittest.mock.patch(
            "data_pc_origin.o3_session.is_origin_gui_running",
            side_effect=running,
        ):
            with unittest.mock.patch("data_pc_origin.o3_session.time.sleep"):
                self.assertTrue(wait_origin_gui_stopped(timeout_sec=5, poll_sec=0.1))


class TestO3Plugins(unittest.TestCase):
    def test_registry_order(self) -> None:
        reg = PluginRegistry()
        p = DialogReadonlyPlugin()
        reg.register(p)
        self.assertEqual(len(reg.list_plugins()), 1)
        reg.unregister(p)
        self.assertEqual(len(reg.list_plugins()), 0)

    def test_retry_default_zero(self) -> None:
        self.assertEqual(RetryOpenPlugin().max_retries, 0)


class TestO3RuntimeImport(unittest.TestCase):
    def test_import_modules(self) -> None:
        import data_pc_origin.o3_import as o3i
        import data_pc_origin.o3_session as o3s

        self.assertTrue(callable(o3i.import_originpro))
        self.assertTrue(callable(o3s.OriginSession))


if __name__ == "__main__":
    unittest.main()
