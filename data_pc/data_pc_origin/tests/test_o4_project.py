# -*- coding: utf-8 -*-
import unittest
from types import SimpleNamespace

from data_pc_origin.o4_errors import OriginOpenError
from data_pc_origin.o4_project import (
    open_project,
    open_project_with_retry,
    save_project,
    save_project_as,
    try_open_project,
    validate_opju_path,
)


class TestO4Project(unittest.TestCase):
    def test_validate_delegates_empty_path(self) -> None:
        r = validate_opju_path("")
        self.assertFalse(r.ok)
        self.assertEqual(r.code, "P01")

    def test_try_open_returns_bool(self) -> None:
        class Op(SimpleNamespace):
            def open(self, path: str) -> bool:
                return True

        self.assertTrue(try_open_project(Op(), r"G:\a.opju"))

    def test_open_raises_on_failure(self) -> None:
        class Op(SimpleNamespace):
            def open(self, path: str) -> bool:
                return False

        with self.assertRaises(OriginOpenError):
            open_project(Op(), r"G:\bad.opju")

    def test_retry_succeeds_second_try(self) -> None:
        state = {"n": 0}

        class Op(SimpleNamespace):
            def open(self, path: str) -> bool:
                state["n"] += 1
                return state["n"] >= 2

        open_project_with_retry(Op(), r"G:\retry.opju", max_retries=1)
        self.assertEqual(state["n"], 2)

    def test_save_calls_op_save(self) -> None:
        saved: list[str] = []

        class Op(SimpleNamespace):
            def save(self, path: str) -> None:
                saved.append(path)

        save_project(Op(), r"G:\same.opju")
        self.assertEqual(saved, [r"G:\same.opju"])

    def test_save_as_calls_op_save(self) -> None:
        saved: list[str] = []

        class Op(SimpleNamespace):
            def save(self, path: str) -> None:
                saved.append(path)

        save_project_as(Op(), r"G:\new.opju")
        self.assertEqual(saved, [r"G:\new.opju"])


if __name__ == "__main__":
    unittest.main()
