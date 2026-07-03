# -*- coding: utf-8 -*-
"""O3 — originpro lazy import (singleton cache)."""

from __future__ import annotations

import importlib
from types import ModuleType
from typing import Callable, Optional

Importer = Callable[[], ModuleType]

_originpro_module: Optional[ModuleType] = None
_default_importer: Optional[Importer] = None


def _builtin_import() -> ModuleType:
    return importlib.import_module("originpro")


def import_originpro(*, force_reload: bool = False, importer: Importer | None = None) -> ModuleType:
    """originpro 모듈 — 두 번째 호출은 캐시 hit."""
    global _originpro_module
    fn = importer or _default_importer or _builtin_import
    if _originpro_module is not None and not force_reload:
        return _originpro_module
    mod = fn()
    _originpro_module = mod
    return mod


def reset_originpro_cache() -> None:
    global _originpro_module
    _originpro_module = None


def set_default_importer(importer: Importer | None) -> None:
    global _default_importer
    _default_importer = importer
