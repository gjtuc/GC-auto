"""gc_autochro 적분 준비(손) — MTD 경로·트리 이름 매칭"""
import os
import tempfile
import unittest

from gc_autochro import (
    resolve_analysis_method_mtd_path,
    tree_label_matches_data_name,
)


class TestGcAutochroPrep(unittest.TestCase):
    def test_tree_matches_suffix(self):
        name = "20260629 dre(3) ni-ce-la"
        self.assertTrue(tree_label_matches_data_name(name, name))
        self.assertTrue(
            tree_label_matches_data_name("20260629 dre(3) ni-ce-la - 상온-1", name)
        )
        self.assertFalse(tree_label_matches_data_name("20260624 dre(3) ni-ce", name))

    def test_resolve_mtd_path_fixed_filename(self):
        with tempfile.TemporaryDirectory() as tmp:
            mtd = os.path.join(tmp, "20260629 분석방법.MTD")
            with open(mtd, "w", encoding="utf-8") as fh:
                fh.write("x")
            old_dir = os.environ.get("AUTOCHRO_ANALYSIS_METHOD_DIR")
            old_name = os.environ.get("AUTOCHRO_ANALYSIS_METHOD_FILENAME")
            os.environ["AUTOCHRO_ANALYSIS_METHOD_DIR"] = tmp
            os.environ.pop("AUTOCHRO_ANALYSIS_METHOD_MTD", None)
            try:
                path = resolve_analysis_method_mtd_path("20260630 other-name")
                self.assertEqual(path, mtd)
            finally:
                if old_dir is None:
                    os.environ.pop("AUTOCHRO_ANALYSIS_METHOD_DIR", None)
                else:
                    os.environ["AUTOCHRO_ANALYSIS_METHOD_DIR"] = old_dir
                if old_name is None:
                    os.environ.pop("AUTOCHRO_ANALYSIS_METHOD_FILENAME", None)
                else:
                    os.environ["AUTOCHRO_ANALYSIS_METHOD_FILENAME"] = old_name


if __name__ == "__main__":
    unittest.main()
