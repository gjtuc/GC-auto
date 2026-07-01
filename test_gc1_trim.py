"""GC1 trim 규칙 단위 테스트 — python -m unittest test_gc1_trim"""
import unittest

from gc_gc1 import trim_reduction_and_first_reaction


def _tcd(*, h2=None, co=None, co2=None):
    rows = []
    if h2 is not None:
        rows.append({"name": "H2", "Area": h2})
    if co is not None:
        rows.append({"name": "CO", "Area": co})
    if co2 is not None:
        rows.append({"name": "CO2", "Area": co2})
    return rows


class TestGc1Trim(unittest.TestCase):
    def test_keeps_first_reaction_cycle_after_transition(self):
        """GC1 전용: 환원·전환 제외 후 첫 반응 사이클도 엑셀에 포함 (GC2/GC3 와 무관)."""
        fid = [[], [], [], [{"name": "CH4", "Area": 1.0}], [{"name": "CH4", "Area": 2.0}]]
        tcd = [
            _tcd(h2=50, co=10),  # 사전 노이즈
            _tcd(h2=20000, co=10),  # 환원
            _tcd(h2=500, co=50),  # 전환
            _tcd(h2=1000, co=500),  # 첫 반응 — 이제 포함
            _tcd(h2=1200, co=600),  # 두 번째 반응
        ]
        kept_fid, kept_tcd, skipped_pre, skipped_red, skipped_trans, skipped_first, found_first = (
            trim_reduction_and_first_reaction(fid, tcd, quiet=True)
        )
        self.assertEqual(len(kept_tcd), 2)
        self.assertEqual(skipped_pre, 1)
        self.assertEqual(skipped_red, 1)
        self.assertEqual(skipped_trans, 1)
        self.assertEqual(skipped_first, 0)
        self.assertTrue(found_first)
        self.assertEqual(kept_tcd[0], _tcd(h2=1000, co=500))

    def test_co2_only_starts_reaction_while_h2_still_reduction(self):
        """CO 미검출·H2 환원대역이어도 CO2>20 이면 반응 시작."""
        fid = [[], [], [], [{"name": "CH4", "Area": 1.0}], [{"name": "CH4", "Area": 2.0}]]
        tcd = [
            _tcd(h2=50, co=10),
            _tcd(h2=20000, co=10),
            _tcd(h2=20000, co=5, co2=15),  # 전환 (CO2 미달)
            _tcd(h2=20000, co=0, co2=25),  # 첫 반응 — CO2만
            _tcd(h2=20000, co=30, co2=10),  # 이후 CO 낮아도 유지
        ]
        kept_fid, kept_tcd, skipped_pre, skipped_red, skipped_trans, skipped_first, found_first = (
            trim_reduction_and_first_reaction(fid, tcd, quiet=True)
        )
        self.assertTrue(found_first)
        self.assertEqual(len(kept_tcd), 2)
        self.assertEqual(skipped_red, 2)
        self.assertEqual(skipped_trans, 0)
        self.assertEqual(kept_tcd[0], _tcd(h2=20000, co=0, co2=25))

    def test_co_over_100_starts_reaction_while_h2_still_reduction(self):
        """CO≥100 이면 H2 환원대역이어도 반응 시작."""
        fid = [[], [], [{"name": "CH4", "Area": 1.0}], [{"name": "CH4", "Area": 2.0}]]
        tcd = [
            _tcd(h2=20000, co=10),
            _tcd(h2=20000, co=500),
            _tcd(h2=20000, co=30),
        ]
        kept_fid, kept_tcd, _, skipped_red, skipped_trans, _, found_first = (
            trim_reduction_and_first_reaction(fid, tcd, quiet=True)
        )
        self.assertTrue(found_first)
        self.assertEqual(len(kept_tcd), 2)
        self.assertEqual(skipped_red, 1)
        self.assertEqual(skipped_trans, 0)
        self.assertEqual(kept_tcd[0], _tcd(h2=20000, co=500))

    def test_co_and_co2_both_high_starts_reaction(self):
        """CO·CO2 동시에 기준 초과 — 반응 시작."""
        fid = [[], [{"name": "CH4", "Area": 1.0}], [{"name": "CH4", "Area": 2.0}]]
        tcd = [
            _tcd(h2=20000, co=10),
            _tcd(h2=20000, co=500, co2=80),
            _tcd(h2=18000, co=200, co2=50),
        ]
        kept_fid, kept_tcd, _, skipped_red, _, _, found_first = (
            trim_reduction_and_first_reaction(fid, tcd, quiet=True)
        )
        self.assertTrue(found_first)
        self.assertEqual(len(kept_tcd), 2)
        self.assertEqual(skipped_red, 1)
        self.assertEqual(kept_tcd[0], _tcd(h2=20000, co=500, co2=80))

    def test_reduction_only_leaves_no_kept_cycles(self):
        """환원+전환만 있고 반응 시작 전 - trim 후 비움 (환원 단계)."""
        fid = [[], []]
        tcd = [_tcd(h2=20000, co=10), _tcd(h2=500, co=50)]
        kept_fid, kept_tcd, skipped_pre, skipped_red, skipped_trans, skipped_first, found_first = (
            trim_reduction_and_first_reaction(fid, tcd, quiet=True)
        )
        self.assertEqual(len(kept_fid), 0)
        self.assertEqual(len(kept_tcd), 0)
        self.assertEqual(skipped_red, 1)
        self.assertGreaterEqual(skipped_trans, 1)
        self.assertFalse(found_first)


if __name__ == "__main__":
    unittest.main()
