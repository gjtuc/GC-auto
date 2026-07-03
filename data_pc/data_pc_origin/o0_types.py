# -*- coding: utf-8 -*-
"""O0 — 공유 타입 (originpro 불필요)."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import NewType, Tuple

IdentityKey = Tuple[str, str]
OriginPath = NewType("OriginPath", str)


@dataclass(frozen=True)
class ProbeResult:
    ok: bool
    detail: str = ""
    code: str = ""


@dataclass(frozen=True)
class OriginWarning:
    code: str
    detail: str = ""


def gap_policy_members() -> set[str]:
    from data_pc_origin.o0_series import GapPolicy

    return {m.name for m in GapPolicy}
