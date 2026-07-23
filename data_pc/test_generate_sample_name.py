# -*- coding: utf-8 -*-
"""Origin Comments — generate_sample_name 토큰 파서 unittest."""
from __future__ import annotations

import importlib.util
import os
import sys
import unittest

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
CALC_PATH = os.path.join(SCRIPT_DIR, "촉매 반응 계산.py")


def _load_calc():
    spec = importlib.util.spec_from_file_location("gc_calc_sample_name_test", CALC_PATH)
    mod = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(mod)
    return mod


class TestGenerateSampleName(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.mod = _load_calc()

    def _parse(self, filename, equipment=None):
        return self.mod.generate_sample_name(filename, equipment=equipment)

    def test_gc2_full_example(self):
        name, warns, needs, q = self._parse(
            "20260525 DRE(1.5) 600 Ni(0.1g, 8h)_Ni5_Ce5_Al2O3.xlsx",
            equipment="GC2",
        )
        self.assertFalse(needs)
        self.assertEqual(
            name,
            "20260525 DRE(1.5%)@600°C Ni_CVD(0.1g,8h)/Ni5/Ce5/Al2O3_DRM 장비",
        )
        self.assertEqual(warns, [])
        self.assertEqual(q, "")

    def test_gc3_suffix(self):
        name, _, needs, _ = self._parse(
            "20260525 DRE(1.5) 600 Ni(0.1g, 8h)_Ni5_Ce5_Al2O3.xlsx",
            equipment="GC3",
        )
        self.assertFalse(needs)
        self.assertTrue(name.endswith("_OCM 장비"))

    def test_yy_year_expansion(self):
        name, _, needs, _ = self._parse(
            "260525 DRE(1.5) 600C Ni5_Al2O3.xlsx",
            equipment="GC2",
        )
        self.assertFalse(needs)
        self.assertTrue(name.startswith("20260525 DRE(1.5%)@600°C"))

    def test_unparseable_foobar(self):
        name, _, needs, q = self._parse("foobar.xlsx", equipment="GC2")
        self.assertTrue(needs)
        self.assertIsNone(name)
        self.assertIn("날짜", q)

    def test_missing_equipment_blocks_origin(self):
        name, _, needs, q = self._parse(
            "20260525 DRE(1.5) 600 Ni5_Al2O3.xlsx",
            equipment=None,
        )
        self.assertTrue(needs)
        self.assertIsNone(name)
        self.assertIn("장비", q)

    def test_gc2_mail_hyphen_catalyst_to_slash(self):
        name, _, needs, _ = self._parse(
            "20260701 DRE(1.5%)@600C Ni5-Ce5La0.25-Al2O3 (citric acid).xlsx",
            equipment="GC2",
        )
        self.assertFalse(needs)
        self.assertEqual(
            name,
            "20260701 DRE(1.5%)@600°C Ni5/Ce5La0.25/Al2O3 (citric acid)_DRM 장비",
        )
        self.assertTrue(name.endswith("_DRM 장비"))

    def test_gc3_mail_hyphen_catalyst_to_slash(self):
        name, _, needs, _ = self._parse(
            "20260630 260630 DRE(1.5)600C Ni5-Al2O3.xlsx",
            equipment="GC3",
        )
        self.assertFalse(needs)
        self.assertIn("Ni5/Al2O3", name)
        self.assertTrue(name.endswith("_OCM 장비"))

    def test_equipment_from_output_file(self):
        self.assertEqual(
            self.mod.equipment_from_output_file(r"G:\a_GC2_DRE_계산완료.xlsx"),
            "GC2",
        )
        self.assertEqual(
            self.mod.equipment_from_output_file(r"G:\a_GC3_DRME_계산완료.xlsx"),
            "GC3",
        )

    def test_compressed_kch_stem_gc3(self):
        name, _, needs, q = self._parse(
            "20260706 0706DRE(1.5)600Ni_CVD(0.1)-Ni5-Ce5-Al2O3.xlsx",
            equipment="GC3",
        )
        self.assertTrue(needs)
        self.assertIsNone(name)
        self.assertIn("CVD", q)

    def test_compressed_kch_with_full_cvd(self):
        name, _, needs, _ = self._parse(
            "20260706 0706DRE(1.5)600Ni(0.1g,8h)-Ni5-Ce5-Al2O3.xlsx",
            equipment="GC3",
        )
        self.assertFalse(needs)
        self.assertEqual(
            name,
            "20260706 DRE(1.5%)@600°C Ni_CVD(0.1g,8h)/Ni5/Ce5/Al2O3_OCM 장비",
        )

    def test_experiment_basename_includes_equipment_suffix(self):
        saved = (
            "20260706 DRE(1.5)@600 Ni(0.1g,8h)-Ni5-Ce5-Al2O3"
            "_GC3_DRE_계산완료.xlsx"
        )
        base = self.mod.generate_experiment_basename(saved)
        self.assertEqual(
            base,
            "20260706 DRE(1.5%)@600C Ni_CVD(0.1g,8h)-Ni5-Ce5-Al2O3_OCM 장비",
        )

    def test_experiment_basename_drme_includes_temperature(self):
        saved = (
            "20260723 DRME(1.5)@600C Ni_CVD(0.1)-Ni5"
            "_GC3_DRME_계산완료.xlsx"
        )
        base = self.mod.generate_experiment_basename(saved)
        self.assertIn("@600C", base)
        self.assertTrue(base.startswith("20260723 DRME(1.5%)@600C "))
        self.assertTrue(base.endswith("_OCM 장비"))


if __name__ == "__main__":
    unittest.main()
