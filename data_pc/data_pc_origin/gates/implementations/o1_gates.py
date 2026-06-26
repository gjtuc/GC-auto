# -*- coding: utf-8 -*-
"""O1 L4 gate bodies."""

from __future__ import annotations

import importlib
import os
import stat
import tempfile
import unittest.mock as mock
from dataclasses import FrozenInstanceError
from pathlib import Path

from data_pc_origin.gates.registry import O1_DEPS, register_gate
from data_pc_origin.o0_types import ProbeResult
from data_pc_origin.o1_opju_path import (
    normalize_g_path,
    probe_g_drive_root_accessible,
    probe_on_g_drive,
    probe_opju_path,
    probe_path_exists,
    probe_path_is_file,
    probe_path_nonempty,
    probe_suffix_opju,
)
from data_pc_origin.o1_opju_writable import (
    probe_file_readable,
    probe_file_writable,
    probe_not_readonly_attr,
    probe_opju_writable,
)
from data_pc_origin.o1_origin_install import (
    origin_exe_running,
    probe_origin_install,
    try_import_originpro,
)


def _assert(condition: bool, msg: str = "") -> None:
    if not condition:
        raise AssertionError(msg or "assertion failed")


def _gate_o1_p_01_a_1() -> None:
    _assert(not probe_path_nonempty("").ok)


def _gate_o1_p_01_b_1() -> None:
    _assert(not probe_path_nonempty("   ").ok)


def _gate_o1_p_02_a_1() -> None:
    missing = os.path.join(tempfile.gettempdir(), "data_pc_origin_no_such.opju")
    _assert(not probe_path_exists(missing).ok)


def _gate_o1_p_02_b_1() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        link = os.path.join(tmp, "broken.opju")
        target = os.path.join(tmp, "missing_target.opju")
        try:
            os.symlink(target, link)
        except OSError:
            return
        if os.path.exists(target):
            os.remove(target)
        _assert(not probe_path_exists(link).ok)


def _gate_o1_p_03_a_1() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        _assert(not probe_path_is_file(tmp).ok)


def _gate_o1_p_04_a_1() -> None:
    _assert(probe_suffix_opju(r"G:\x\sample.opju").ok)


def _gate_o1_p_04_b_1() -> None:
    _assert(probe_suffix_opju(r"G:\x\sample.OPJU").ok)


def _gate_o1_p_04_c_1() -> None:
    _assert(not probe_suffix_opju(r"G:\x\sample.opj").ok)


def _gate_o1_p_05_a_1() -> None:
    _assert(probe_on_g_drive(r"G:\a\b.opju").ok)


def _gate_o1_p_05_b_1() -> None:
    _assert(normalize_g_path(r"g:\a\b.opju").startswith("G:"))
    _assert(probe_on_g_drive(r"g:\a\b.opju").ok)


def _gate_o1_p_06_a_1() -> None:
    with mock.patch("data_pc_origin.o1_opju_path.experiment_data_root", return_value=r"G:\mock_root"):
        with mock.patch("os.path.isdir", return_value=True):
            _assert(probe_g_drive_root_accessible().ok)


def _gate_o1_p_06_b_1() -> None:
    root = r"G:\mock_missing_root"
    with mock.patch("data_pc_origin.o1_opju_path.experiment_data_root", return_value=root):
        with mock.patch("os.path.isdir", return_value=False):
            result = probe_g_drive_root_accessible()
            _assert(not result.ok)
            _assert(root in result.detail)


def _gate_o1_p_07_a_1() -> None:
    gpath = r"G:\mock\sample.opju"
    with mock.patch("os.path.isfile", return_value=True):
        with mock.patch("os.path.isdir", return_value=False):
            with mock.patch("os.path.islink", return_value=False):
                with mock.patch(
                    "data_pc_origin.o1_opju_path.probe_g_drive_root_accessible",
                    return_value=ProbeResult(True, "ok", "P06"),
                ):
                    _assert(probe_opju_path(gpath).ok)


def _gate_o1_p_07_b_1() -> None:
    result = probe_opju_path("")
    _assert(not result.ok)
    _assert(result.code == "P01")


def _gate_o1_p_07_c_1() -> None:
    r = ProbeResult(True, "x", "P07")
    try:
        r.ok = False  # type: ignore[misc]
        raise AssertionError("not frozen")
    except FrozenInstanceError:
        pass


def _gate_o1_w_01_a_1() -> None:
    with tempfile.NamedTemporaryFile(delete=False, suffix=".opju") as f:
        path = f.name
    try:
        _assert(probe_file_readable(path).ok)
    finally:
        os.remove(path)


def _gate_o1_w_01_b_1() -> None:
    with tempfile.NamedTemporaryFile(delete=False, suffix=".opju") as f:
        path = f.name
    try:
        with mock.patch("os.access", side_effect=lambda _p, mode: False if mode == os.R_OK else True):
            _assert(not probe_file_readable(path).ok)
    finally:
        os.remove(path)


def _gate_o1_w_02_a_1() -> None:
    with tempfile.NamedTemporaryFile(delete=False, suffix=".opju") as f:
        path = f.name
    try:
        _assert(probe_file_writable(path).ok)
    finally:
        os.remove(path)


def _gate_o1_w_02_b_1() -> None:
    with tempfile.NamedTemporaryFile(delete=False, suffix=".opju") as f:
        path = f.name
    try:
        with mock.patch("os.access", side_effect=lambda _p, mode: False if mode == os.W_OK else True):
            _assert(not probe_file_writable(path).ok)
    finally:
        os.remove(path)


def _gate_o1_w_03_a_1() -> None:
    with tempfile.NamedTemporaryFile(delete=False, suffix=".opju") as f:
        path = f.name
    try:
        _assert(probe_not_readonly_attr(path).ok)
    finally:
        os.remove(path)


def _gate_o1_w_03_b_1() -> None:
    with tempfile.NamedTemporaryFile(delete=False, suffix=".opju") as f:
        path = f.name
    try:
        if os.name == "nt":
            import ctypes

            FILE_ATTRIBUTE_READONLY = 0x1
            ctypes.windll.kernel32.SetFileAttributesW(path, FILE_ATTRIBUTE_READONLY)
            try:
                _assert(not probe_not_readonly_attr(path).ok)
            finally:
                ctypes.windll.kernel32.SetFileAttributesW(path, 0x80)
        else:
            os.chmod(path, stat.S_IRUSR)
            _assert(not probe_not_readonly_attr(path).ok)
    finally:
        try:
            os.chmod(path, stat.S_IWUSR | stat.S_IRUSR)
        except OSError:
            pass
        os.remove(path)


def _gate_o1_w_04_a_1() -> None:
    with tempfile.NamedTemporaryFile(delete=False, suffix=".opju") as f:
        path = f.name
    try:
        _assert(probe_opju_writable(path).ok)
    finally:
        os.remove(path)


def _gate_o1_i_01_a_1() -> None:
    with mock.patch.object(importlib, "import_module", side_effect=ImportError("mock missing")):
        result, mod = try_import_originpro()
        _assert(not result.ok)
        _assert(mod is None)


def _gate_o1_i_01_b_1() -> None:
    fake = object()
    with mock.patch.object(importlib, "import_module", return_value=fake):
        result, mod = try_import_originpro()
        _assert(result.ok)
        _assert(mod is fake)


def _gate_o1_i_02_a_1() -> None:
    with mock.patch("subprocess.run") as run:
        run.return_value.stdout = "Origin64.exe    123 Console"
        run.return_value.returncode = 0
        _assert(origin_exe_running().detail == "running")


def _gate_o1_i_02_b_1() -> None:
    with mock.patch("subprocess.run") as run:
        run.return_value.stdout = "INFO: no tasks"
        run.return_value.returncode = 0
        result = origin_exe_running()
        _assert(result.ok)
        _assert(result.detail == "not running")


def _gate_o1_i_03_a_1() -> None:
    fake = object()
    with mock.patch.object(importlib, "import_module", return_value=fake):
        result = probe_origin_install()
        _assert(result.ok)
        _assert(result.code == "I03")


_O1_GATES = [
    ("O1-P-01-a-1", _gate_o1_p_01_a_1),
    ("O1-P-01-b-1", _gate_o1_p_01_b_1),
    ("O1-P-02-a-1", _gate_o1_p_02_a_1),
    ("O1-P-02-b-1", _gate_o1_p_02_b_1),
    ("O1-P-03-a-1", _gate_o1_p_03_a_1),
    ("O1-P-04-a-1", _gate_o1_p_04_a_1),
    ("O1-P-04-b-1", _gate_o1_p_04_b_1),
    ("O1-P-04-c-1", _gate_o1_p_04_c_1),
    ("O1-P-05-a-1", _gate_o1_p_05_a_1),
    ("O1-P-05-b-1", _gate_o1_p_05_b_1),
    ("O1-P-06-a-1", _gate_o1_p_06_a_1),
    ("O1-P-06-b-1", _gate_o1_p_06_b_1),
    ("O1-P-07-a-1", _gate_o1_p_07_a_1),
    ("O1-P-07-b-1", _gate_o1_p_07_b_1),
    ("O1-P-07-c-1", _gate_o1_p_07_c_1),
    ("O1-W-01-a-1", _gate_o1_w_01_a_1),
    ("O1-W-01-b-1", _gate_o1_w_01_b_1),
    ("O1-W-02-a-1", _gate_o1_w_02_a_1),
    ("O1-W-02-b-1", _gate_o1_w_02_b_1),
    ("O1-W-03-a-1", _gate_o1_w_03_a_1),
    ("O1-W-03-b-1", _gate_o1_w_03_b_1),
    ("O1-W-04-a-1", _gate_o1_w_04_a_1),
    ("O1-I-01-a-1", _gate_o1_i_01_a_1),
    ("O1-I-01-b-1", _gate_o1_i_01_b_1),
    ("O1-I-02-a-1", _gate_o1_i_02_a_1),
    ("O1-I-02-b-1", _gate_o1_i_02_b_1),
    ("O1-I-03-a-1", _gate_o1_i_03_a_1),
]


def register_o1_gates() -> None:
    for gate_id, fn in _O1_GATES:
        register_gate(gate_id, fn, depends=O1_DEPS[gate_id], layer="O1")
