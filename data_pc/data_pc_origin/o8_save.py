# -*- coding: utf-8 -*-
"""O8 — opju save path (촉매 save_in_place 분기)."""

from __future__ import annotations


def resolve_save_path(opju_path: str, save_in_place: bool) -> str:
    """save_in_place=False → `*_Updated.opju` (촉매 L1729–1731)."""
    if save_in_place:
        return opju_path
    return opju_path.replace(".opju", "_Updated.opju")
