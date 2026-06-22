"""GC1 trim 규칙 단위 테스트 — python -m unittest test_gc1_trim"""
import unittest
from unittest.mock import patch

from gc_gc1 import trim_reduction_and_first_reaction


def _tcd(*, h2=None, co=None):
    rows = []
    if h2 is not None:
        rows.append({"name": "H2", "Area": h2})
    if co is not None:
        rows.append({"name": "CO", "Area": co})
    return rows


class TestGc1Trim(unittest.TestCase):
    def test_fixed_start_cycle_from_env(self):
        fid = [[{"name": "CH4", "Area": i}] for i in range(5)]
        tcd = [[{"name": "H2", "Area": i * 100}] for i in range(5)]
        with patch.dict("os.environ", {"GC1_EXCEL_START_CYCLE": "3"}):
            kept_fid, kept_tcd, skipped_pre, skipped_red, skipped_trans, skipped_first, ok = (
                trim_reduction_and_first_reaction(fid, tcd, quiet=True)
            )
        self.assertTrue(ok)
        self.assertEqual(len(kept_fid), 3)
        self.assertEqual(skipped_pre, 2)
        self.assertEqual(skipped_red, 0)

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


if __name__ == "__main__":
    unittest.main()
