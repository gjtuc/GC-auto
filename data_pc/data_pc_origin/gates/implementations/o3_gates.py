# -*- coding: utf-8 -*-
"""O3 L4 gate bodies — mock originpro (dry)."""

from __future__ import annotations

from types import ModuleType, SimpleNamespace

from data_pc_origin.gates.registry import O3_DEPS, register_gate
from data_pc_origin.o3_import import import_originpro, reset_originpro_cache
from data_pc_origin.o3_plugins import (
    DEFAULT_PLUGIN_REGISTRY,
    DialogReadonlyPlugin,
    OriginPlugin,
    PluginRegistry,
    RetryOpenPlugin,
)
from data_pc_origin.o3_session import OriginSession, set_oext, set_show_false


def _assert(condition: bool, msg: str = "") -> None:
    if not condition:
        raise AssertionError(msg or "assertion failed")


def _fake_op() -> ModuleType:
    calls: dict = {"show": [], "oext": [], "exit": 0}

    class FakeOp(SimpleNamespace):
        def set_show(self, value: bool) -> None:
            calls["show"].append(value)

        def oext(self, value: bool) -> None:
            calls["oext"].append(value)

        def exit(self) -> None:
            calls["exit"] += 1

    op = FakeOp()
    op._calls = calls  # type: ignore[attr-defined]
    return op  # type: ignore[return-value]


def _gate_o3_s_01_a_1() -> None:
    reset_originpro_cache()
    n = {"count": 0}

    def importer() -> ModuleType:
        n["count"] += 1
        return _fake_op()

    a = import_originpro(importer=importer)
    b = import_originpro(importer=importer)
    _assert(a is b)
    _assert(n["count"] == 1)


def _gate_o3_s_01_b_1() -> None:
    reset_originpro_cache()

    def bad_importer() -> ModuleType:
        raise ImportError("no originpro")

    try:
        import_originpro(importer=bad_importer, force_reload=True)
        raise AssertionError("expected ImportError")
    except ImportError:
        pass


def _gate_o3_s_02_a_1() -> None:
    op = _fake_op()
    set_show_false(op)
    _assert(op._calls["show"] == [False])  # type: ignore[attr-defined]


def _gate_o3_s_03_a_1() -> None:
    op = _fake_op()
    set_oext(op, True)
    _assert(op._calls["oext"] == [True])  # type: ignore[attr-defined]


def _gate_o3_s_04_a_1() -> None:
    op = _fake_op()
    op.exit()
    _assert(op._calls["exit"] == 1)  # type: ignore[attr-defined]


def _gate_o3_s_04_b_1() -> None:
    op = _fake_op()
    set_oext(op, True)
    set_oext(op, False)
    _assert(op._calls["oext"] == [True, False])  # type: ignore[attr-defined]


def _gate_o3_s_05_a_1() -> None:
    op = _fake_op()

    def boom_importer() -> ModuleType:
        return op

    try:
        with OriginSession(importer=boom_importer):
            raise RuntimeError("inside session")
    except RuntimeError:
        pass
    _assert(op._calls["exit"] == 1)  # type: ignore[attr-defined]
    _assert(op._calls["oext"][-1] is False)  # type: ignore[attr-defined]


def _gate_o3_s_06_a_1() -> None:
    op = _fake_op()
    with OriginSession(importer=lambda: op) as entered:
        _assert(entered is op)
        _assert(op._calls["show"] == [False])  # type: ignore[attr-defined]
    _assert(op._calls["exit"] == 1)  # type: ignore[attr-defined]


def _gate_o3_p_01_a_1() -> None:
    class P:
        def on_open_start(self, path: str) -> None:
            pass

        def on_open_end(self, path: str, *, ok: bool) -> None:
            pass

    _assert(isinstance(P(), OriginPlugin))


def _gate_o3_p_02_a_1() -> None:
    reg = PluginRegistry()
    p = DialogReadonlyPlugin()
    reg.register(p)
    _assert(len(reg.list_plugins()) == 1)
    reg.unregister(p)
    _assert(len(reg.list_plugins()) == 0)


def _gate_o3_p_03_a_1() -> None:
    _assert(DialogReadonlyPlugin.enabled is False)
    _assert(DialogReadonlyPlugin() not in DEFAULT_PLUGIN_REGISTRY.list_plugins())


def _gate_o3_p_04_a_1() -> None:
    plugin = RetryOpenPlugin(max_retries=0)
    _assert(plugin.max_retries == 0)
    _assert(plugin not in DEFAULT_PLUGIN_REGISTRY.list_plugins())


_O3_GATES = [
    ("O3-S-01-a-1", _gate_o3_s_01_a_1),
    ("O3-S-01-b-1", _gate_o3_s_01_b_1),
    ("O3-S-02-a-1", _gate_o3_s_02_a_1),
    ("O3-S-03-a-1", _gate_o3_s_03_a_1),
    ("O3-S-04-a-1", _gate_o3_s_04_a_1),
    ("O3-S-04-b-1", _gate_o3_s_04_b_1),
    ("O3-S-05-a-1", _gate_o3_s_05_a_1),
    ("O3-S-06-a-1", _gate_o3_s_06_a_1),
    ("O3-P-01-a-1", _gate_o3_p_01_a_1),
    ("O3-P-02-a-1", _gate_o3_p_02_a_1),
    ("O3-P-03-a-1", _gate_o3_p_03_a_1),
    ("O3-P-04-a-1", _gate_o3_p_04_a_1),
]


def register_o3_gates() -> None:
    for gate_id, fn in _O3_GATES:
        register_gate(gate_id, fn, depends=O3_DEPS[gate_id], layer="O3")
