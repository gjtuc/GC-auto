# -*- coding: utf-8 -*-
"""gc_identity — GC4(구 GC1) 표기·동의어."""

from __future__ import annotations

import unittest

import gc_identity as gi
from gc1_runtime.layer0_ident import (
    is_gc1_chemstation_mode,
    is_gc1_instance,
    is_gc_equipment_role,
)


class GcIdentityTests(unittest.TestCase):
    def test_autochro_codes(self) -> None:
        self.assertTrue(gi.is_autochro_instance("gc1"))
        self.assertTrue(gi.is_autochro_instance("gc4"))
        self.assertTrue(gi.is_autochro_mode("gc4"))
        self.assertFalse(gi.is_autochro_mode("8860"))
        self.assertEqual(gi.display_name_for_instance("gc4"), "GC4")
        self.assertEqual(gi.canonical_autochro_code("gc4"), "gc1")

    def test_layer0_aliases(self) -> None:
        self.assertTrue(is_gc1_instance("gc4"))
        self.assertTrue(is_gc1_chemstation_mode("gc4"))
        self.assertTrue(is_gc_equipment_role("gc4_pc"))
        self.assertTrue(is_gc_equipment_role("gc1_pc"))
        self.assertTrue(is_gc_equipment_role("gc2_pc"))


if __name__ == "__main__":
    unittest.main()
