# -*- coding: utf-8 -*-
import unittest

from data_pc_origin.o6_fixtures import fx_wks_empty, fx_wks_mixed_dated, fx_wks_three_dated
from data_pc_origin.o6_scan import dated_columns, iter_col_comments


class TestO6Scan(unittest.TestCase):
    def test_iter_col_comments_three(self) -> None:
        wks = fx_wks_three_dated()
        pairs = list(iter_col_comments(wks))
        self.assertEqual(len(pairs), 3)
        self.assertEqual(pairs[0][0], 1)
        self.assertTrue(pairs[0][1].startswith("20250601"))

    def test_iter_col_comments_empty(self) -> None:
        wks = fx_wks_empty()
        self.assertEqual(list(iter_col_comments(wks)), [])

    def test_dated_columns_filters(self) -> None:
        wks = fx_wks_mixed_dated()
        dated = dated_columns(wks)
        self.assertEqual([d[0] for d in dated], [1, 3])
        self.assertEqual([d[1] for d in dated], ["20250601", "20250620"])


if __name__ == "__main__":
    unittest.main()
