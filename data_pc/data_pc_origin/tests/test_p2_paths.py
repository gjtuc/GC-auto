# -*- coding: utf-8 -*-
import json
import os
import unittest
from pathlib import Path

from data_pc_origin.p2_paths import (
    build_stage4_paths,
    normalize_opju_path,
    resolve_stage4_save_path,
)


class TestP2Paths(unittest.TestCase):
    def test_normalize_g(self) -> None:
        self.assertTrue(normalize_opju_path("g:\\a.opju").startswith("G:"))

    def test_updated_suffix(self) -> None:
        src = r"G:\folder\test.opju"
        self.assertIn("_Updated", resolve_stage4_save_path(src, False))

    def test_write_p2_smoke_artifact(self) -> None:
        live = (
            r"G:\연구소\실험\실험데이터\촉매 반응\DRE 반응(C2H6)"
            r"\20260626 DRE(1.5) 600C Ni5_Ce5_Al2O3_test"
            r"\20260626 DRE(1.5) 600C Ni5_Ce5_Al2O3_test.opju"
        )
        norm = normalize_opju_path(live)
        out = {
            "normalized_prefix": norm[:2],
            "save_in_place": resolve_stage4_save_path(norm, True),
            "save_as": resolve_stage4_save_path(norm, False),
        }
        path = Path(__file__).resolve().parents[1] / "p2_paths_smoke.json"
        path.write_text(json.dumps(out, indent=2, ensure_ascii=False), encoding="utf-8")
        self.assertEqual(out["normalized_prefix"], "G:")
        self.assertTrue(out["save_as"].endswith("_Updated.opju"))

    @unittest.skipUnless(os.path.isdir("G:\\"), "G: not mounted")
    def test_live_opju_probe_if_present(self) -> None:
        live = (
            r"G:\연구소\실험\실험데이터\촉매 반응\DRE 반응(C2H6)"
            r"\20260626 DRE(1.5) 600C Ni5_Ce5_Al2O3_test"
            r"\20260626 DRE(1.5) 600C Ni5_Ce5_Al2O3_test.opju"
        )
        if not Path(live).is_file():
            self.skipTest("live opju not on disk")
        bundle = build_stage4_paths(live, save_in_place=False)
        self.assertTrue(bundle.probe.ok)


if __name__ == "__main__":
    unittest.main()
