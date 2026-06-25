# -*- coding: utf-8 -*-
"""
data_pc_wifi_autoconnect.py — 차헌 데이터 PC Wi-Fi 자동 연결 (gc_wifi_autoconnect 래퍼)

Desktop\\.cursor\\gc_data_pc_wifi_autoconnect.bat 에서 호출.
"""

from __future__ import annotations

import os
import sys

_REPO_CANDIDATES = (
    os.path.dirname(os.path.abspath(__file__)),
    os.path.join(os.path.dirname(os.path.abspath(__file__)), "GC-auto-push"),
    os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."),
)
for _c in _REPO_CANDIDATES:
    if os.path.isfile(os.path.join(_c, "gc_wifi_autoconnect.py")) and _c not in sys.path:
        sys.path.insert(0, _c)
        break

from gc_wifi_autoconnect import ensure_wifi_connected, main  # noqa: E402

_DEFAULT_DIR = os.path.join(os.path.expanduser("~"), "Desktop", ".cursor")


def ensure_data_pc_wifi(script_dir: str | None = None) -> bool:
    return ensure_wifi_connected(script_dir or _DEFAULT_DIR)


if __name__ == "__main__":
    if len(sys.argv) == 1:
        ok = ensure_data_pc_wifi()
        sys.exit(0 if ok else 1)
    main()
