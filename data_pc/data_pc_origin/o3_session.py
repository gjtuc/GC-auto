# -*- coding: utf-8 -*-
"""O3 — OriginSession context manager."""

from __future__ import annotations

from types import ModuleType
from typing import Callable, Optional

from data_pc_origin.o3_import import import_originpro
from data_pc_origin.o3_plugins import PluginRegistry


def set_show_false(op: ModuleType) -> None:
    op.set_show(False)


def set_oext(op: ModuleType, enabled: bool) -> None:
    """originpro 버전별 — callable oext() 또는 bool 속성 대입."""
    if not hasattr(op, "oext"):
        return
    member = getattr(op, "oext", None)
    if callable(member):
        member(enabled)
        return
    try:
        setattr(op, "oext", enabled)
    except (AttributeError, TypeError):
        pass


class OriginSession:
    """with OriginSession() as op: … — set_show(False), enter/exit, finally op.exit()."""

    def __init__(
        self,
        *,
        plugins: PluginRegistry | None = None,
        importer: Callable[[], ModuleType] | None = None,
    ) -> None:
        self.plugins = plugins or PluginRegistry()
        self._importer = importer
        self._op: ModuleType | None = None
        self._entered = False

    def __enter__(self) -> ModuleType:
        if self._importer is not None:
            self._op = self._importer()
        else:
            self._op = import_originpro()
        set_show_false(self._op)
        set_oext(self._op, True)
        self._entered = True
        return self._op

    def __exit__(self, exc_type, exc, tb) -> bool:
        op = self._op
        self._entered = False
        if op is not None:
            try:
                op.exit()
            finally:
                set_oext(op, False)
                self._op = None
        return False
