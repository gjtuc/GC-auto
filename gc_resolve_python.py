# -*- coding: utf-8 -*-
"""GC1 Autochro용 Python 경로 — 32-bit 우선 (pywinauto + 32-bit Autochro)."""
from __future__ import annotations

import os
import sys
from pathlib import Path


def python32_candidates() -> list[Path]:
    extra = os.getenv("GC_PYTHON32", "").strip()
    local = Path(os.environ.get("LOCALAPPDATA", ""))
    names = (
        "Python312-32",
        "Python311-32",
        "Python310-32",
    )
    paths: list[Path] = []
    if extra:
        paths.append(Path(extra))
    for name in names:
        paths.append(local / "Programs" / "Python" / name / "python.exe")
    return paths


def resolve_python_for_gc(*, prefer_32: bool = True) -> Path:
    if prefer_32:
        for candidate in python32_candidates():
            if candidate.is_file():
                return candidate
    return Path(sys.executable)


def main() -> int:
    print(str(resolve_python_for_gc()))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
