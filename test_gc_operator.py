# -*- coding: utf-8 -*-
"""gc_operator — GC2 차완/차헌 메일 분기 단위 테스트."""

from __future__ import annotations

import json
import os
import tempfile
import unittest

import gc_operator as go


class GcOperatorTests(unittest.TestCase):
    def setUp(self) -> None:
        self._env_backup = {
            k: os.environ.get(k)
            for k in (
                "MAIL_TO_CHAWAN",
                "MAIL_TO_CHAHEON",
                "MAIL_TO",
                "GC_OPERATOR",
            )
        }
        os.environ["MAIL_TO_CHAWAN"] = "yangcw0103@kier.re.kr"
        os.environ["MAIL_TO_CHAHEON"] = "kimcha0809@naver.com"
        os.environ.pop("GC_OPERATOR", None)

    def tearDown(self) -> None:
        for key, value in self._env_backup.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value

    def test_dual_enabled(self) -> None:
        self.assertTrue(go.dual_operator_mail_enabled())
        del os.environ["MAIL_TO_CHAWAN"]
        self.assertFalse(go.dual_operator_mail_enabled())

    def test_operator_only_messages(self) -> None:
        self.assertTrue(go.message_is_operator_only("차완"))
        self.assertTrue(go.message_is_operator_only("차헌"))
        self.assertTrue(go.message_is_operator_only("chawan"))
        self.assertFalse(go.message_is_operator_only("차완 진행"))
        self.assertFalse(go.message_is_operator_only("진행"))

    def test_extract_from_initiation(self) -> None:
        self.assertEqual(go.extract_operator_from_message("차완 진행"), go.OPERATOR_CHAWAN)
        self.assertEqual(go.extract_operator_from_message("차헌 작업해줘"), go.OPERATOR_CHAHEON)
        self.assertEqual(go.extract_operator_from_message("진행"), None)

    def test_save_load_resolve(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            go.save_operator(tmp, "차완")
            self.assertEqual(go.load_operator(tmp), go.OPERATOR_CHAWAN)
            path = go.operator_file_path(tmp)
            with open(path, encoding="utf-8") as f:
                data = json.load(f)
            self.assertEqual(data["mail_to"], "yangcw0103@kier.re.kr")

            recipient, op = go.resolve_recipient(tmp, "fallback@x.com")
            self.assertEqual(op, go.OPERATOR_CHAWAN)
            self.assertEqual(recipient, "yangcw0103@kier.re.kr")

            go.save_operator(tmp, "차헌")
            recipient, op = go.resolve_recipient(tmp, "fallback@x.com")
            self.assertEqual(recipient, "kimcha0809@naver.com")
            self.assertEqual(op, go.OPERATOR_CHAHEON)

    def test_resolve_without_operator(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            recipient, op = go.resolve_recipient(tmp, "fallback@x.com")
            self.assertEqual(recipient, "")
            self.assertIsNone(op)


if __name__ == "__main__":
    unittest.main()
