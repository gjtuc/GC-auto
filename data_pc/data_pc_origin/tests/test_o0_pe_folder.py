# -*- coding: utf-8 -*-
import unittest

from data_pc_origin.o0_pe_folder import (
    book_pe_path,
    path_in_pe_folder,
    pe_folder_label,
    reaction_from_sample_name,
    resolve_pe_folder,
)
from data_pc_origin.o5_duplicate_books import duplicate_long_name_groups, row_count_conflict_groups
from data_pc_origin.o5_fixtures import MockBook, make_mock_op
from data_pc_origin.o5_match import find_all_worksheets_for_keyword


class TestPeFolderLabel(unittest.TestCase):
    def test_dre_gc3(self) -> None:
        self.assertEqual(pe_folder_label("DRE", "GC3"), "DRE-GC3")

    def test_drme_gc3(self) -> None:
        self.assertEqual(pe_folder_label("DRME", "gc3"), "DRME-GC3")

    def test_incomplete(self) -> None:
        self.assertEqual(pe_folder_label("DRE", None), "")
        self.assertEqual(pe_folder_label("", "GC3"), "")

    def test_reaction_from_sample(self) -> None:
        self.assertEqual(
            reaction_from_sample_name("20261115 DRME(1.5%)@600°C Ni"),
            "DRME",
        )

    def test_resolve_explicit(self) -> None:
        self.assertEqual(
            resolve_pe_folder(pe_folder="DRE-GC3", reaction_type="DRME", equipment="GC3"),
            "DRE-GC3",
        )

    def test_resolve_from_parts(self) -> None:
        self.assertEqual(
            resolve_pe_folder(reaction_type="DRE", equipment="GC3"),
            "DRE-GC3",
        )


class TestPeFolderFilter(unittest.TestCase):
    def test_path_segment(self) -> None:
        pe = "/proj/DRME-GC3/"
        self.assertTrue(path_in_pe_folder(pe, "DRME-GC3"))
        self.assertFalse(path_in_pe_folder(pe, "DRE-GC3"))

    def test_find_all_scoped(self) -> None:
        a = MockBook("COyieldAB", "CO yield", ("Sheet1",))
        a.pe_path = "/root/DRME-GC3/"  # type: ignore[attr-defined]
        b = MockBook("COyield", "CO yield", ("Sheet1",))
        b.pe_path = "/root/DRE-GC3/"  # type: ignore[attr-defined]
        op = make_mock_op([a, b])
        all_hits = find_all_worksheets_for_keyword(op, "CO yield")
        self.assertEqual(len(all_hits), 2)
        dre_only = find_all_worksheets_for_keyword(op, "CO yield", pe_folder="DRE-GC3")
        self.assertEqual(len(dre_only), 1)
        self.assertEqual(book_pe_path(op, b), "/root/DRE-GC3/")

    def test_row_conflict_scoped(self) -> None:
        """다른 PE 폴더의 동명 Long Name 은 충돌이 아니다."""

        class _Sheet:
            cols = 2

            def get_label(self, i, kind):
                return "20261115 x" if i == 1 and kind == "C" else ""

            def to_list(self, i):
                return [1.0] * (80 if self._rows == 80 else 34)

            def __init__(self, rows: int) -> None:
                self._rows = rows
                self.name = "Sheet1"

        class _Book:
            def __init__(self, name: str, pe: str, rows: int) -> None:
                self.name = name
                self.lname = "CO yield"
                self.pe_path = pe
                self._sheets = [_Sheet(rows)]

            def __iter__(self):
                return iter(self._sheets)

        op = make_mock_op(
            [
                _Book("COyieldAB", "/r/DRME-GC3/", 34),  # type: ignore[list-item]
                _Book("COyield", "/r/DRE-GC3/", 80),  # type: ignore[list-item]
            ]
        )
        # pe_folder 없으면 폴더 무시하고 동명끼리 비교 → 충돌
        self.assertEqual(len(row_count_conflict_groups(op)), 1)
        # 폴더로 한정하면 각 폴더에 북 1개 → 충돌 없음
        self.assertEqual(row_count_conflict_groups(op, pe_folder="DRME-GC3"), [])
        self.assertEqual(row_count_conflict_groups(op, pe_folder="DRE-GC3"), [])
        self.assertEqual(len(duplicate_long_name_groups(op, pe_folder="DRME-GC3")), 0)
        # 같은 폴더 안 행 수 불일치 → 충돌
        op2 = make_mock_op(
            [
                _Book("COyieldA", "/r/DRE-GC3/", 80),  # type: ignore[list-item]
                _Book("COyieldB", "/r/DRE-GC3/", 34),  # type: ignore[list-item]
            ]
        )
        conflicts = row_count_conflict_groups(op2, pe_folder="DRE-GC3")
        self.assertEqual(len(conflicts), 1)


if __name__ == "__main__":
    unittest.main()
