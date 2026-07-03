# -*- coding: utf-8 -*-
"""GC1 핫스팟 → Cursor 에이전트 쿨다운·enqueue 검사."""

from __future__ import annotations

import json
import os
import tempfile
import time
import unittest


class HotspotAgentCooldownTests(unittest.TestCase):
    def test_cooldown_blocks_within_30min(self) -> None:
        from gc1_runtime.layer0_hotspot_agent import (
            _save_json,
            should_run_hotspot_session,
            HOTSPOT_AGENT_STATE,
        )

        with tempfile.TemporaryDirectory() as tmp:
            state_file = os.path.join(tmp, HOTSPOT_AGENT_STATE)
            _save_json(
                state_file,
                {"last_trigger_at": time.time() - 60, "agent_in_flight": False},
            )
            ok, reason = should_run_hotspot_session(tmp, chemstation_mode="gc1")
            self.assertFalse(ok)
            self.assertIn("SKIP", reason)

    def test_cooldown_allows_after_30min(self) -> None:
        from gc1_runtime.layer0_hotspot_agent import _save_json, should_run_hotspot_session

        with tempfile.TemporaryDirectory() as tmp:
            state_file = os.path.join(tmp, ".gc_hotspot_agent_state.json")
            _save_json(
                state_file,
                {"last_trigger_at": time.time() - 1900, "agent_in_flight": False},
            )
            ok, reason = should_run_hotspot_session(tmp, chemstation_mode="gc1")
            self.assertTrue(ok)
            self.assertEqual(reason, "ok")

    def test_no_api_key_still_allows_ocr_session(self) -> None:
        from gc1_runtime.layer0_hotspot_agent import should_run_hotspot_session

        with tempfile.TemporaryDirectory() as tmp:
            os.environ.pop("CURSOR_API_KEY", None)
            ok, reason = should_run_hotspot_session(tmp, chemstation_mode="gc1")
            self.assertTrue(ok)
            self.assertEqual(reason, "ok")

    def test_ensure_gc1_ocr_env_sets_defaults(self) -> None:
        from gc1_runtime.layer0_hotspot_agent import ensure_gc1_ocr_env

        for key in (
            "GC1_AUTOCHRO_EYE",
            "GC1_AUTOCHRO_EYE_ADAPT",
            "GC1_OCR_CASE_STUDY",
        ):
            os.environ.pop(key, None)
        applied = ensure_gc1_ocr_env()
        self.assertIn("GC1_AUTOCHRO_EYE", applied)
        self.assertEqual(os.environ.get("GC1_AUTOCHRO_EYE"), "1")

    def test_initiation_prompt_is_dongjakhae(self) -> None:
        from gc1_runtime.layer0_hotspot_agent import build_hotspot_initiation_prompt

        self.assertEqual(
            build_hotspot_initiation_prompt(ssid="iPhone", just_connected=True),
            "동작해",
        )


if __name__ == "__main__":
    unittest.main()
