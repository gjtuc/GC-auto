# -*- coding: utf-8
"""Test helpers — env isolation when gc_automation.env sets SKIP_ORIGIN."""

from __future__ import annotations

import os
from contextlib import contextmanager

WORKFLOW_TEST_ENV = {"DATA_PC_SKIP_ORIGIN": "0"}


@contextmanager
def without_skip_origin():
    key = "DATA_PC_SKIP_ORIGIN"
    prior = os.environ.get(key)
    os.environ[key] = "0"
    try:
        yield
    finally:
        if prior is None:
            os.environ.pop(key, None)
        else:
            os.environ[key] = prior
