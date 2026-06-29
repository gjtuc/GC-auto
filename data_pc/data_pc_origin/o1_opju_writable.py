# -*- coding: utf-8 -*-
"""O1 — .opju 쓰기 가능 probe."""

from __future__ import annotations

import os
import stat

from data_pc_origin.o0_types import ProbeResult


def probe_file_readable(path: str) -> ProbeResult:
    try:
        ok = os.access(path, os.R_OK)
    except OSError as exc:
        return ProbeResult(False, str(exc), "W01")
    if not ok:
        return ProbeResult(False, "not readable", "W01")
    return ProbeResult(True, "ok", "W01")


def probe_file_writable(path: str) -> ProbeResult:
    try:
        ok = os.access(path, os.W_OK)
    except OSError as exc:
        return ProbeResult(False, str(exc), "W02")
    if not ok:
        return ProbeResult(False, "not writable", "W02")
    return ProbeResult(True, "ok", "W02")


def probe_not_readonly_attr(path: str) -> ProbeResult:
    try:
        st = os.stat(path)
        if hasattr(st, "st_file_attributes"):
            if st.st_file_attributes & stat.FILE_ATTRIBUTE_READONLY:
                return ProbeResult(False, "read-only attribute", "W03")
    except OSError as exc:
        return ProbeResult(False, str(exc), "W03")
    if not os.access(path, os.W_OK):
        return ProbeResult(False, "read-only or no write access", "W03")
    return ProbeResult(True, "ok", "W03")


def probe_opju_writable(path: str) -> ProbeResult:
    for step in (probe_file_readable, probe_file_writable, probe_not_readonly_attr):
        result = step(path)
        if not result.ok:
            return result
    return ProbeResult(True, "", "")
