# -*- coding: utf-8 -*-
import os
import tempfile
import unittest
from datetime import datetime, timedelta

from gc_state import (
    can_auto_send_for_mode,
    format_auto_mail_slot_status,
    is_mail_slot_available,
    record_auto_mail_sent,
    save_send_state,
    uses_mail_cooldown,
)


class TestGcMailCooldown(unittest.TestCase):
    def test_uses_mail_cooldown_gc2_gc3_only(self):
        self.assertFalse(uses_mail_cooldown("gc1"))
        self.assertTrue(uses_mail_cooldown("8860"))
        self.assertTrue(uses_mail_cooldown("chem32"))

    def test_slot_available_after_cooldown(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, ".gc_send_state.json")
            save_send_state(path, {})
            allowed, _ = can_auto_send_for_mode(path, "chem32")
            self.assertTrue(allowed)

            sent_at = datetime.now() - timedelta(hours=4)
            record_auto_mail_sent(path, sent_at)
            allowed, _ = can_auto_send_for_mode(path, "chem32")
            self.assertTrue(allowed)

    def test_slot_blocked_within_cooldown(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, ".gc_send_state.json")
            record_auto_mail_sent(path, datetime.now())
            allowed, reason = can_auto_send_for_mode(path, "8860")
            self.assertFalse(allowed)
            self.assertIn("슬롯 0/1", reason)

    def test_format_slot_status(self):
        state = {"last_auto_mail_sent_at": datetime.now().strftime("%Y-%m-%dT%H:%M:%S")}
        self.assertIn("0/1", format_auto_mail_slot_status(state))
        self.assertTrue(is_mail_slot_available({}))


if __name__ == "__main__":
    unittest.main()
