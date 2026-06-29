# -*- coding: utf-8 -*-
"""O0-I-03 — Task C Origin Comments ↔ KCH identity 토큰 (실행·게이트 공용)."""
from __future__ import annotations

import unittest

from data_pc_origin.o0_comments import comment_matches_identity
from data_pc_origin.o0_identity import identity_match_tokens, token_match_score

# GC 테스트 실행(2026-06-29)과 동일한 시료
_LIVE_IDENTITY = ("20260620", "dre(1.5) 600c ni5_ce5_al2o3")
_LIVE_COMMENT = "20260620 DRE(1.5%)@600°C Ni5/Ce5/Al2O3_OCM 장비"


class TestO0I03TaskC(unittest.TestCase):
    def test_concentration_token(self):
        tokens = identity_match_tokens("dre(1.5) 600c ni5_ce5_al2o3")
        self.assertIn("1.5", tokens)
        self.assertIn("dre", tokens)

    def test_temperature_at_token_from_600c(self):
        self.assertIn("@600", identity_match_tokens("dre(1.5) 600c ni5"))

    def test_slash_catalyst_tokens(self):
        tokens = identity_match_tokens("ni5/ce5/al2o3")
        self.assertGreaterEqual({"ni5", "ce5", "al2o3"} & tokens, {"ni5", "ce5"})

    def test_live_comment_matches_identity(self):
        """실행 검증 — GC 파이프라인이 쓴 Comments ↔ KCH 파일명."""
        self.assertTrue(comment_matches_identity(_LIVE_COMMENT, _LIVE_IDENTITY))

    def test_score_on_task_c_comment_body(self):
        tokens = identity_match_tokens(_LIVE_IDENTITY[1])
        body = "dre(1.5%)@600°c ni5/ce5/al2o3"
        self.assertGreaterEqual(token_match_score(body, tokens), 0.6)


if __name__ == "__main__":
    unittest.main()
