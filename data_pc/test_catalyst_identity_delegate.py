# -*- coding: utf-8 -*-
"""촉매 반응 계산.py identity 헬퍼 ↔ O0 위임 — 코드·실행 검증.

코드 검증: bridge·촉매 래퍼가 동일 API 를 노출.
실행 검증: live GC 시료(20260620 DRE Ni5_Ce5_Al2O3) 토큰·Comments 매칭이 True.
"""
from __future__ import annotations

import importlib.util
import sys
import unittest
from pathlib import Path

_CURSOR = Path(__file__).resolve().parent
if str(_CURSOR) not in sys.path:
    sys.path.insert(0, str(_CURSOR))

from data_pc_origin.catalyst_identity_bridge import (
    catalyst_comment_matches_identity,
    catalyst_comment_sort_date,
    catalyst_identity_tokens,
)
from data_pc_origin.o0_comments import comment_matches_identity, parse_comment_date
from data_pc_origin.o0_identity import identity_match_tokens

_LIVE_IDENTITY = ("20260620", "dre(1.5) 600c ni5_ce5_al2o3")
_LIVE_COMMENT = "20260620 DRE(1.5%)@600°C Ni5/Ce5/Al2O3_OCM 장비"
_LEGACY_FOLDER = "20260620 DRE(1.5) 600C Ni5_Ce5_Al2O3 촉매"


def _load_catalyst_helpers():
    """촉매 모듈에서 위임 래퍼만 로드 (전체 파이프라인 실행 없음)."""
    spec = importlib.util.spec_from_file_location(
        "catalyst_calc",
        _CURSOR / "촉매 반응 계산.py",
    )
    mod = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(mod)
    return mod


class TestCatalystIdentityBridge(unittest.TestCase):
    def test_bridge_matches_o0_identity(self):
        sample = _LIVE_IDENTITY[1]
        self.assertEqual(catalyst_identity_tokens(sample), identity_match_tokens(sample))

    def test_bridge_matches_o0_comments(self):
        self.assertEqual(
            catalyst_comment_matches_identity(_LIVE_COMMENT, _LIVE_IDENTITY),
            comment_matches_identity(_LIVE_COMMENT, _LIVE_IDENTITY),
        )
        self.assertEqual(
            catalyst_comment_sort_date(_LIVE_COMMENT),
            parse_comment_date(_LIVE_COMMENT),
        )

    def test_live_comment_match_execution(self):
        """GC 파이프라인이 만든 Comments ↔ KCH identity — 실행 검증 고정값."""
        self.assertTrue(catalyst_comment_matches_identity(_LIVE_COMMENT, _LIVE_IDENTITY))

    def test_folder_identity_tokens_richer_than_legacy_regex(self):
        """O0-I-03: 농도·@600 토큰이 legacy 정규식보다 풍부 — G: 중복 판별 개선."""
        tokens = catalyst_identity_tokens(_LIVE_IDENTITY[1])
        self.assertIn("1.5", tokens)
        self.assertIn("@600", tokens)
        folder_lower = _LEGACY_FOLDER.lower()
        matched = sum(1 for t in tokens if t in folder_lower)
        threshold = max(2, int(len(tokens) * 0.6))
        self.assertGreaterEqual(matched, threshold)


class TestCatalystModuleDelegates(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.catalyst = _load_catalyst_helpers()

    def test_catalyst_identity_tokens_delegate(self):
        sample = _LIVE_IDENTITY[1]
        self.assertEqual(
            self.catalyst._identity_match_tokens(sample),
            identity_match_tokens(sample),
        )

    def test_catalyst_comment_matches_delegate(self):
        self.assertTrue(
            self.catalyst._comment_matches_identity(_LIVE_COMMENT, _LIVE_IDENTITY),
        )

    def test_catalyst_sort_date_delegate(self):
        self.assertEqual(
            self.catalyst._comment_sort_date(_LIVE_COMMENT),
            "20260620",
        )


if __name__ == "__main__":
    unittest.main()
