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


@contextmanager
def with_live_e2e_env(*, equipment: str = "GC3"):
    """G: live dry-run — Origin 실행 + companion xlsx 장비 기본값."""
    keys = {
        "DATA_PC_SKIP_ORIGIN": "0",
        "DATA_PC_DEFAULT_EQUIPMENT": equipment,
    }
    prior = {k: os.environ.get(k) for k in keys}
    os.environ.update(keys)
    try:
        yield
    finally:
        for k, v in prior.items():
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v
