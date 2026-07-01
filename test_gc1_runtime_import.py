# -*- coding: utf-8 -*-
"""T20 — gc1_runtime 패키지 import·레이어 골격."""
import unittest

import gc1_runtime
from gc1_runtime import layer0, layer1, layer2, layer3, layer4


class TestGc1RuntimeImport(unittest.TestCase):
    def test_package_docstring_mentions_layers(self):
        doc = gc1_runtime.__doc__ or ""
        self.assertIn("L0", doc)
        self.assertIn("L4", doc)
        self.assertIn("아래만 import", doc)

    def test_layer_modules_importable(self):
        for mod in (layer0, layer1, layer2, layer3, layer4):
            self.assertTrue(mod.__name__.startswith("gc1_runtime.layer"))


if __name__ == "__main__":
    unittest.main()
