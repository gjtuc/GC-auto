# -*- coding: utf-8 -*-
import unittest
from pathlib import Path

from data_pc_origin.live_data import find_companion_xlsx, resolve_live_job

LIVE_OPJU = (
    r"G:\연구소\실험\실험데이터\촉매 반응\DRE 반응(C2H6)"
    r"\20260626 DRE(1.5) 600C Ni5_Ce5_Al2O3_test"
    r"\20260626 DRE(1.5) 600C Ni5_Ce5_Al2O3_test.opju"
)


class TestLiveData(unittest.TestCase):
    def test_find_companion_xlsx(self) -> None:
        if not Path(LIVE_OPJU).is_file():
            self.skipTest("live opju not mounted")
        xlsx = find_companion_xlsx(LIVE_OPJU)
        self.assertIsNotNone(xlsx)
        assert xlsx is not None
        self.assertTrue(xlsx.lower().endswith(".xlsx"))
        self.assertNotIn("~$", xlsx)

    def test_resolve_live_job(self) -> None:
        if not Path(LIVE_OPJU).is_file():
            self.skipTest("live opju not mounted")
        ctx = resolve_live_job(LIVE_OPJU)
        self.assertGreater(ctx.row_count, 0)
        self.assertIn("H2 Yield (%)", ctx.columns)
        self.assertIn("20260620", ctx.sample_name)


if __name__ == "__main__":
    unittest.main()
