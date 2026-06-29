# -*- coding: utf-8 -*-
"""O0-C-04 장비 접미사 — strip/parse + identity 매칭."""
from __future__ import annotations

import unittest

from data_pc_origin.o0_comments import (
    comment_matches_identity,
    parse_equipment_suffix,
    strip_equipment_suffix,
)

_IDENTITY = ("20260620", "dre(1.5) 600c ni5_ce5_al2o3")


class TestO0C04EquipmentSuffix(unittest.TestCase):
    def test_strip_drm(self):
        raw = "20260620 DRE(1.5)@600°C Ni5_Ce5_Al2O3_DRM 장비"
        self.assertEqual(
            strip_equipment_suffix(raw),
            "20260620 DRE(1.5)@600°C Ni5_Ce5_Al2O3",
        )

    def test_parse_ocm(self):
        self.assertEqual(
            parse_equipment_suffix("20260620 DRME(1.5%)@600°C x_OCM 장비"),
            "GC3",
        )

    def test_identity_match_with_suffix(self):
        self.assertTrue(
            comment_matches_identity(
                "20260620 DRE(1.5)@600°C Ni5_Ce5_Al2O3_DRM 장비",
                _IDENTITY,
            )
        )


if __name__ == "__main__":
    unittest.main()
