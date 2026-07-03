# -*- coding: utf-8 -*-
"""O1 — EXPERIMENT_DATA_ROOT (촉매·runtime 과 동일 기본값)."""

from __future__ import annotations

import os

DEFAULT_EXPERIMENT_DATA_ROOT = r"G:\연구소\실험\실험데이터"


def experiment_data_root() -> str:
    raw = os.environ.get("EXPERIMENT_DATA_ROOT", DEFAULT_EXPERIMENT_DATA_ROOT)
    text = (raw or "").strip()
    return text or DEFAULT_EXPERIMENT_DATA_ROOT
