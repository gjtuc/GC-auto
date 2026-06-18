# -*- coding: utf-8 -*-
import os
import unittest
from unittest.mock import patch

from gc_force_auth import force_authorized, require_force_auth


class TestGcForceAuth(unittest.TestCase):
    def test_open_when_unset(self):
        with patch.dict(os.environ, {}, clear=True):
            self.assertTrue(force_authorized())

    def test_token_required(self):
        with patch.dict(os.environ, {'GC_FORCE_TOKEN': 'abc'}, clear=True):
            self.assertFalse(force_authorized())
            self.assertTrue(force_authorized('abc'))

    def test_invoke_env(self):
        with patch.dict(os.environ, {'GC_FORCE_TOKEN': 'abc', 'GC_FORCE_INVOKE': 'abc'}, clear=True):
            self.assertTrue(force_authorized())

    def test_require_exit(self):
        with patch.dict(os.environ, {'GC_FORCE_TOKEN': 'x'}, clear=True):
            with self.assertRaises(SystemExit) as ctx:
                require_force_auth()
            self.assertEqual(ctx.exception.code, 3)


if __name__ == '__main__':
    unittest.main()
