# -*- coding: utf-8
import unittest

from pathlib import Path

from data_pc_origin.parallel_origin import (
    folder_parallel_reaction_key,
    folder_sample_body,
    folders_are_parallel_peers,
)


class TestParallelOrigin(unittest.TestCase):
    def test_parallel_reaction_key_dre(self) -> None:
        key = folder_parallel_reaction_key(
            "20260701 DRE(1.5%)@600C Ni5-Ce5La0.25-Al2O3 (citric acid)"
        )
        self.assertEqual(key, ("DRE", "1.5", "600"))

    def test_different_samples_same_reaction_are_peers(self) -> None:
        a = "20260701 DRE(1.5%)@600C Ni5-Al2O3"
        b = "20260701 DRE(1.5%)@600C Ni5-Ce5La0.25-Al2O3"
        self.assertTrue(
            folders_are_parallel_peers(a, b, window_sec=7200, ts_a=1000.0, ts_b=5000.0)
        )

    def test_same_sample_not_peer(self) -> None:
        a = "20260701 DRE(1.5%)@600C Ni5-Al2O3"
        b = "20260630 DRE(1.5%)@600C Ni5-Al2O3"
        self.assertFalse(
            folders_are_parallel_peers(a, b, window_sec=7200, ts_a=1000.0, ts_b=2000.0)
        )

    def test_outside_window_not_peer(self) -> None:
        a = "20260701 DRE(1.5%)@600C Ni5-Al2O3"
        b = "20260701 DRE(1.5%)@600C Ni20-Al2O3"
        self.assertFalse(
            folders_are_parallel_peers(a, b, window_sec=7200, ts_a=0.0, ts_b=100000.0)
        )

    def test_folder_identity_keeps_decimal_conc(self) -> None:
        from importlib.util import module_from_spec, spec_from_file_location

        spec = spec_from_file_location(
            "catalyst_mod",
            str(Path(__file__).resolve().parents[2] / "촉매 반응 계산.py"),
        )
        mod = module_from_spec(spec)
        assert spec.loader is not None
        spec.loader.exec_module(mod)
        ik = mod._experiment_identity_key("20260630 DRE(1.5)@600 Ni5-Al2O3")
        self.assertEqual(ik[1], "dre(1.5)@600 ni5-al2o3")
        a = "20260630 260630 DRE(1.5)600C Ni5-Al2O3"
        b = "20260701 DRE(1.5%)@600C Ni5-Ce5La0.25-Al2O3 (citric acid)"
        self.assertEqual(
            folder_parallel_reaction_key(a),
            ("DRE", "1.5", "600"),
        )
        self.assertTrue(
            folders_are_parallel_peers(a, b, window_sec=7200, ts_a=1000.0, ts_b=5000.0)
        )


if __name__ == "__main__":
    unittest.main()
