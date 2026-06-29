# -*- coding: utf-8 -*-
import unittest

from data_pc_origin.o5_fixtures import fx_opju_two_books, make_mock_op
from data_pc_origin.o5_iterate import iter_pages_w, iter_worksheets


class TestO5Iterate(unittest.TestCase):
    def test_iter_pages_w_calls_w(self) -> None:
        calls: list[str] = []
        from data_pc_origin.o5_fixtures import MockBook

        op = make_mock_op([MockBook("B", "", ("S",))], pages_calls=calls)
        list(iter_pages_w(op))
        self.assertEqual(calls, ["w"])

    def test_iter_worksheets_eight_pairs(self) -> None:
        op, _ = fx_opju_two_books()
        pairs = list(iter_worksheets(op))
        self.assertEqual(len(pairs), 8)
        self.assertEqual(pairs[0][1].name, "H2yield")

    def test_iter_pages_w_none_raises(self) -> None:
        with self.assertRaises(TypeError):
            list(iter_pages_w(None))  # type: ignore[arg-type]

    def test_empty_op_no_pairs(self) -> None:
        op = make_mock_op([])
        self.assertEqual(list(iter_worksheets(op)), [])


if __name__ == "__main__":
    unittest.main()
