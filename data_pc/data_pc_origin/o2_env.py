# -*- coding: utf-8 -*-
"""O2 — env (DATA_PC_SKIP_ORIGIN)."""

from __future__ import annotations

import os
from typing import Mapping, MutableMapping

SKIP_ORIGIN_ENV = "DATA_PC_SKIP_ORIGIN"
_TRUTHY = frozenset({"1", "true", "yes", "on"})


def read_env_raw(key: str, *, environ: Mapping[str, str] | None = None) -> str:
    env: Mapping[str, str] = environ if environ is not None else os.environ
    return (env.get(key) or "").strip().lower()


def parse_bool_env(value: str) -> bool:
    return (value or "").strip().lower() in _TRUTHY


def skip_origin_active(*, environ: Mapping[str, str] | None = None) -> bool:
    return parse_bool_env(read_env_raw(SKIP_ORIGIN_ENV, environ=environ))


def origin_feature_enabled(*, environ: Mapping[str, str] | None = None) -> bool:
    return not skip_origin_active(environ=environ)
