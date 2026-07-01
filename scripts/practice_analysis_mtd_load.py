# -*- coding: utf-8 -*-
"""연습: CRM 읽기 → 분석목록 트리 시료 우클릭 → 분석방법 불러오기 → MTD 열기."""
from __future__ import annotations

import ctypes
import os
import sys
import time

_REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _REPO not in sys.path:
    sys.path.insert(0, _REPO)

from gc_autochro import (
    connect_main_window,
    load_autochro_config,
    read_crm_data_name,
    resolve_analysis_method_mtd_path,
    step_load_analysis_method,
    _select_analysis_tab,
)
from gc_mailer import load_dotenv_files


def main() -> int:
    os.environ.setdefault("GC_SCREEN_SHOW_FOCUS", "1")
    excel = os.path.join(os.path.expanduser("~"), "Desktop", "박은규")
    load_dotenv_files(_REPO, excel)
    cfg = load_autochro_config(excel)
    _, win = connect_main_window(cfg)
    ctypes.windll.user32.SetForegroundWindow(win.handle)
    time.sleep(0.4)

    print("=== CRM 읽기 (MTD 직전) ===")
    crm = read_crm_data_name(win)
    if not crm:
        print("FAIL: CRM 데이터명 없음")
        return 1
    print("CRM:", crm)

    mtd = resolve_analysis_method_mtd_path()
    print("MTD:", mtd)
    if not os.path.isfile(mtd):
        print("FAIL: MTD 파일 없음")
        return 1

    _select_analysis_tab(win)
    time.sleep(0.5)
    print("=== 트리 우클릭 → 분석방법 불러오기 → 열기 ===")
    name = step_load_analysis_method(win, cfg)
    print("OK — loaded MTD for", name)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
