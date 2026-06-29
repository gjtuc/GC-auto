# -*- coding: utf-8 -*-
"""O3 — session plugins (기본 비활성)."""

from __future__ import annotations

from typing import List, Protocol, runtime_checkable


@runtime_checkable
class OriginPlugin(Protocol):
    def on_open_start(self, path: str) -> None: ...

    def on_open_end(self, path: str, *, ok: bool) -> None: ...


class PluginRegistry:
    def __init__(self) -> None:
        self._plugins: List[OriginPlugin] = []

    def register(self, plugin: OriginPlugin) -> None:
        if plugin not in self._plugins:
            self._plugins.append(plugin)

    def unregister(self, plugin: OriginPlugin) -> None:
        if plugin in self._plugins:
            self._plugins.remove(plugin)

    def list_plugins(self) -> List[OriginPlugin]:
        return list(self._plugins)

    def notify_open_start(self, path: str) -> None:
        for plugin in self._plugins:
            plugin.on_open_start(path)

    def notify_open_end(self, path: str, *, ok: bool) -> None:
        for plugin in self._plugins:
            plugin.on_open_end(path, ok=ok)


class DialogReadonlyPlugin:
    """Read-Only 대화상자 자동 Yes — 기본 registry 에 미등록."""

    enabled: bool = False

    def on_open_start(self, path: str) -> None:
        return None

    def on_open_end(self, path: str, *, ok: bool) -> None:
        return None


class RetryOpenPlugin:
    """op.open 재시도 — max_retries=0 기본."""

    def __init__(self, max_retries: int = 0) -> None:
        self.max_retries = max_retries

    def on_open_start(self, path: str) -> None:
        return None

    def on_open_end(self, path: str, *, ok: bool) -> None:
        return None


DEFAULT_PLUGIN_REGISTRY = PluginRegistry()
