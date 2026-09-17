# -*- coding: utf-8 -*-
"""같은 Long Name 워크북은 행 수가 다를 때만 쓰기를 막는다."""

import unittest

from data_pc_origin.o5_duplicate_books import (
    duplicate_long_name_groups,
    row_count_conflict_groups,
)


class _Wks:
    def __init__(self, rows: int):
        self.cols = 3
        self.rows = rows

    def get_label(self, idx, kind):
        if idx == 2 and kind == "C":
            return "20260811 sample"
        return ""

    def to_list(self, idx):
        return [1.0] * self.rows


class _Book:
    def __init__(self, name: str, lname: str, rows: int):
        self.name = name
        self.lname = lname
        self._wks = [_Wks(rows)]

    def __iter__(self):
        return iter(self._wks)


class _Op:
    def __init__(self, books):
        self._books = books

    def pages(self, kind):
        return self._books


class DuplicateLongNameTests(unittest.TestCase):
    def test_same_row_count_does_not_block(self):
        op = _Op(
            [
                _Book("H2yieldA", "H2 yield", 114),
                _Book("H2yieldAB", "H2 yield", 114),
            ]
        )
        groups = duplicate_long_name_groups(op)
        self.assertEqual(len(groups), 1)
        names = [name for name, _rows in groups[0][1]]
        self.assertEqual(names, ["H2yieldA", "H2yieldAB"])
        self.assertEqual(row_count_conflict_groups(op), [])

    def test_different_row_count_blocks(self):
        op = _Op(
            [
                _Book("H2yield", "H2 yield", 140),
                _Book("H2yieldA", "H2 yield", 114),
            ]
        )
        conflicts = row_count_conflict_groups(op)
        self.assertEqual(len(conflicts), 1)
        self.assertEqual(conflicts[0][0], "H2 yield")
        rows = sorted(rows for _name, rows in conflicts[0][1])
        self.assertEqual(rows, [114, 140])

    def test_unique_long_name_is_allowed(self):
        op = _Op([_Book("H2yield", "H2 yield", 114)])
        self.assertEqual(duplicate_long_name_groups(op), [])


if __name__ == "__main__":
    unittest.main()
