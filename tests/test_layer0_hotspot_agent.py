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
            _state_path,
            should_enqueue_hotspot_agent,
            HOTSPOT_AGENT_STATE,
        )

        with tempfile.TemporaryDirectory() as tmp:
            os.environ["CURSOR_API_KEY"] = "test-key"
            state_file = os.path.join(tmp, HOTSPOT_AGENT_STATE)
            _save_json(
                state_file,
                {"last_trigger_at": time.time() - 60, "agent_in_flight": False},
            )
            ok, reason = should_enqueue_hotspot_agent(tmp, chemstation_mode="gc1")
            self.assertFalse(ok)
            self.assertIn("SKIP", reason)
            del os.environ["CURSOR_API_KEY"]

    def test_cooldown_allows_after_30min(self) -> None:
        from gc1_runtime.layer0_hotspot_agent import _save_json, should_enqueue_hotspot_agent

        with tempfile.TemporaryDirectory() as tmp:
            os.environ["CURSOR_API_KEY"] = "test-key"
            state_file = os.path.join(tmp, ".gc_hotspot_agent_state.json")
            _save_json(
                state_file,
                {"last_trigger_at": time.time() - 1900, "agent_in_flight": False},
            )
            ok, reason = should_enqueue_hotspot_agent(tmp, chemstation_mode="gc1")
            self.assertTrue(ok)
            self.assertEqual(reason, "enqueue")
            del os.environ["CURSOR_API_KEY"]

    def test_initiation_prompt_is_dongjakhae(self) -> None:
        from gc1_runtime.layer0_hotspot_agent import build_hotspot_initiation_prompt

        self.assertEqual(
            build_hotspot_initiation_prompt(ssid="iPhone", just_connected=True),
            "동작해",
        )


if __name__ == "__main__":
    unittest.main()
