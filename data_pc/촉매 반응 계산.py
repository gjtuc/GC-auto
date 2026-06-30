import runtime_paths  # noqa: F401 — [LLM] .cursor\\gc-python-cache 로 __pycache__ 리다이렉트 (실험 폴더 오염 방지)

import pandas as pd
import numpy as np
import os
import sys
import re
import base64
import time
import shutil
import argparse
import threading
import imaplib
import email
import json
from email.header import decode_header
from email.utils import parsedate_to_datetime
from datetime import datetime, timedelta
from typing import NamedTuple


class PipelineRunResult(NamedTuple):
    """watch 쿨다운 판정용 — G: 잠금 시 gdrive_retry_needed=True (1시간 쿨다운 생략)."""
    workflow_count: int
    gdrive_retry_needed: bool = False

'''
=============================================================================
촉매 반응 계산.py — GC 데이터 자동 계산 · 실험 폴더 아카이브 · Origin 연동
=============================================================================

[GitHub repo 위치]
  data_pc/촉매 반응 계산.py  (통합 repo: https://github.com/gjtuc/GC-auto)

[운영 설치 경로 — LLM/에이전트 필독]  deploy/DATA_PC_HOME_LAYOUT.md
  이 파일(촉매 반응 계산.py)은 repo가 아니라 **사용자 PC 로컬**에 복사해 실행합니다.
  SCRIPT_DIR = 이 .py 파일이 있는 폴더 (아래 둘 중 하나).

  | PC 종류   | 권장 운영 폴더 (script_dir)              | 바탕화면 노출 |
  |-----------|------------------------------------------|---------------|
  | 은규 PC   | %USERPROFILE%\\gc-data-pc\\              | 없음 (거슬리지 않음) |
  | 차헌 PC   | %USERPROFILE%\\Desktop\\.cursor\\       | 있음 (기존 관례) |

  ⚠ %USERPROFILE%\\.cursor\\gc-python-cache\\ — Python __pycache__ 전용 (runtime_paths.py)
  ⚠ %USERPROFILE%\\.cursor\\gc-runtime-temp\\ — 스크립트 임시 파일 (실험 데이터 아님)
  IDE 설정·확장과 섞이지 않도록 gc-* 접두사 하위에만 둠.

  하위 구조 (script_dir 기준, 연구원별 폴더명):
    gc_automation.env          — 네이버 IMAP (Git 제외)
    촉매 반응 계산.py          — 본 스크립트
    PEG\\ 또는 KCH\\           — inbox/processed + machine_profile.json
      inbox\\                  — 메일 첨부 xlsx 수신
      processed\\              — 계산 완료 검토용 사본
      machine_profile.json     — PC 식별 + reaction_roots 로컬 오버라이드 (Git 제외)

[어느 PC에서 실행?]  docs/PC_NAMING.md
  **은규 PC** 또는 **차헌 PC** (업무·Origin PC). GC **장비** PC에서 실행 금지.

  [LLM] 실험 저장 위치 — PC마다 다름:
    · 은규 PC: C:\\Users\\User\\Desktop\\새 폴더\\연구노트\\DRE 등 (G: **없음**)
    · 차헌 PC: G:\\연구소\\실험\\... (SecuYouSB 보안 USB)
  경로는 PEG/KCH\\machine_profile.json 이 repo 기본값보다 우선.

  | 연구원 | 이 스크립트를 돌리는 PC | 메일을 보내는 장비 PC        |
  |--------|-------------------------|------------------------------|
  | 은규   | 은규 PC                 | GC1 장비 PC                  |
  | 차헌   | 차헌 PC                 | GC2/GC3 장비 PC              |

  · Origin, 실험 저장 경로, IMAP 메일 계정은 데이터 PC(은규/차헌 PC)에 있음
  · machine_profile.json: role=data_pc — paths·reaction_roots 는 **PC마다 다름**
  · gc_automation.env 는 script_dir 에 둠 (장비 PC의 박은규/KCH env 와 별개)

[장비 PC와의 관계]
  GC1/GC2/GC3 **장비 PC**: repo gc_automation.py → KCH 원본 xlsx → SMTP 발송
  **은규 PC / 차헌 PC** (본 스크립트): IMAP 수신 → 계산 → 실험 폴더 → Origin

[사용자가 이 스크립트를 만든 목적]
  연구실 GC(Agilent) 분석 후 반복되는 수작업을 줄이기 위함:
  · KCH 원본 엑셀에서 Area → 수율/전환율 계산
  · Origin .opju 워크시트에 시료 열 자동 추가
  · 실험 폴더(연구노트 또는 G:)에 .opju / .pptx / .xlsx 정리

[전체 파이프라인 — 두 대 PC]
  GC2/GC3 장비 PC (차헌): ChemStation → gc_automation.py → KCH 원본.xlsx → SMTP → **차헌 PC**
  GC1 장비 PC (은규): Autochro → gc_automation.py → KCH 원본.xlsx → SMTP → **은규 PC**
  은규 PC / 차헌 PC (본 스크립트):
    1) IMAP 메일 수신 — 받은·보낸·내게쓴(미읽음) → {PEG|KCH}/inbox (오래된 순 전건 반영)
    2) 수율/전환율 계산 → {PEG|KCH}/processed (검토용 사본)
    3) 실험 폴더 생성 (반응별 최신 폴더 복사 템플릿) — 은규: 연구노트, 차헌: G:
    4) Origin .opju 워크시트에 새 시료 열(Comments) 추가 (그래프 plot 은 수동)

[gc_automation.env 용도]
  네이버 메일(IMAP) 계정만 저장: NAVER_EMAIL, NAVER_APP_PASSWORD
  보안 USB 비밀번호 등은 env에 넣지 않음 — G: 잠금 해제는 사용자가 GUI에서 직접.

[G: 드라이브 / SecuYouSB — 차헌 PC 위주]
  [LLM] 은규 PC는 G: 를 쓰지 않음 — machine_profile → 연구노트 로컬 경로.
  차헌 PC: 실험 데이터는 G:\\연구소\\실험\\실험데이터\\... (보안 USB) 위에 있음.
  USB 세션 만료 시 G: 경로가 탐색기에서 사라짐.
  · 이 스크립트는 G:를 "열"거나 USB에 로그인하지 않음 (공식 API 없음).
  · os.path.isdir() 로 경로 존재만 확인 → 없으면 안내 후 중단.
  · 사용자가 SecuYouSB에서 직접 로그인 → 스크립트 재실행.

[시료명 이중 규칙 — DRM / DRE / DRME 공통]
  generate_experiment_basename() → G: 폴더·파일명 (유연, Windows 금지문자 제거)
    · (x) = Origin 과 동일 — 주반응물 feed 농도(%)
    예: 20260615 DRE(1.5)@600 Ni20-Al2O3
        20260613 DRM(5)@650C Ni10-Al2O3 촉매 0.25g
  generate_sample_name() → Origin Comments (엄격, °C·슬래시·CVD 규칙)
    · 괄호 (x) = 주반응물 feed 농도(%): 파일명에서 추출 → 화공 양론으로 ppm 산출
      DRME x% → C2H6·CH4 각 x%, CO2 3x%   DRE x% → C2H6 x%, CO2 2x%   DRM x% → CH4·CO2 각 x%
    · 파일명 농도 표기 (_extract_concentration 우선순위):
        (1.5)% / 1.5%          — 명시적 퍼센트
        dre@(3) / DRM@(5)      — gc_automation KCH·GC PDF stem (반응@(농도))
        DRE(3) / DRE (3)       — 반응 바로 뒤 괄호 (예: DRE(3)@600 → C2H6 3%)
        C2H6(1.5) / CH4(5)     — 레거시
    · 파일명에 농도 없으면 USER SETTINGS 기본 ppm (fallback)
    · 촉매 무게(0.25g 등)는 Origin Comments 에 넣지 않음 — DRE/DRME/DRM 공통
      (G: 폴더명에는 DRM 등에서 "촉매 0.25g" 유지)
    예: 20260615 DRE(1.5)@600°C Ni20/Al2O3
        20260613 DRM(5)@650°C Ni10/Al2O3
        (X) 20260613 DRM(5)@650°C Ni10/Al2O3/0.25g  ← 구형, 사용 안 함

[G: 실험 폴더 생성 규칙 (3단계)]
  반응별 루트에서 폴더명(YYYYMMDD…) 기준 최신 폴더를 템플릿으로 복사.
  새 폴더명 = generate_experiment_basename(입력 엑셀).
  복사본 안: .opju/.pptx 이름 변경, 기존 .xlsx 삭제, 계산 xlsx 배치.
  .opju 는 이전 실험 열이 쌓인 상태 → update_origin() 으로 새 열 1개 추가.

[G: 중복 실험 폴더 정리 — Canonical Chain (비트코인 최장 체인 합의)]
  날짜만 하루 차이·시료명 동일한 폴더가 둘 이상 있을 때, 각 폴더 안 xlsx 를 비교.
  짧은 체인이 긴 체인의 앞부분(prefix)과 동일하면 → 같은 실험의 중복 생성으로 판단.
  주입(사이클) 수가 더 많은 폴더만 남기고, 짧은 쪽 폴더 전체(.opju/.pptx/.xlsx) 삭제.
  DRM / DRE / DRME 공통. 내용이 다르면 삭제하지 않음.

[실행]
  python "촉매 반응 계산.py"              # 메일 → 계산 → G: → Origin
  python "촉매 반응 계산.py" --no-archive  # 계산만
  python "촉매 반응 계산.py" --manual       # 엑셀 직접 지정
=============================================================================
'''

if hasattr(sys.stdout, "reconfigure"):
    try: sys.stdout.reconfigure(encoding="utf-8")
    except Exception: pass

# originpro — 4단계(update_origin) 호출 시에만 import (--no-archive 는 Origin 불필요)
_originpro = None

def _get_originpro():
    """Origin 워크시트 연동 시에만 originpro 로드."""
    global _originpro
    if _originpro is None:
        try:
            import originpro as op
            _originpro = op
        except ImportError:
            print("❌ [오류] originpro 라이브러리가 설치되어 있지 않습니다.")
            print("   G:/Origin 연동(3~4단계)에 필요합니다. 계산만 할 때는 --no-archive 를 사용하세요.")
            sys.exit(1)
    return _originpro


# ---------------------------------------------------------------------------
# Origin 자동화 보조 — [4단계] update_origin() 전용
#
# [배경]
#   originpro(op.open)는 동일 .opju 를 다른 Python/Origin 세션이 이미 열고 있으면
#   GUI 확인창을 띄운다:
#     "The file is opened in another instance of Origin.
#      Do you still want to open it as Read-Only?"
#   예전에는 watchdog+watch 가 중복 기동되며 이 창이 반복되어 수동 Yes 가 필요했다.
#
# [대응 — 3겹]
#   1) KCH\.origin_update.lock
#        Origin 4단계(열기→워크시트 반영→저장→exit) 전 구간을 PID 파일로 직렬화.
#        data_pc_runtime 파이프라인 락과 별개 — Origin COM 세션만 보호.
#   2) _origin_exit_quiet()
#        op.open 직전 이 프로세스의 이전 originpro 외부 세션(op.oext) 정리.
#   3) _origin_dialog_watcher + Win32 EnumWindows
#        op.open / op.save 동안 백그라운드 스레드가 Read-Only 확인창을 감지해 Yes 클릭.
#        (잔여 경쟁·Origin 내부 잠금 지연 대비 — 완전 차단은 1)+2)가 담당)
#
# [로그] %USERPROFILE%\.cursor\gc-runtime-temp\origin_automation.log
# [운영] 차헌·은규 PC 공통 — SCRIPT_DIR\KCH\.origin_update.lock
# ---------------------------------------------------------------------------


def _origin_update_lock_path():
    """Origin 4단계 직렬화 락 파일 (KCH 하위, PID 한 줄)."""
    return os.path.join(SCRIPT_DIR, _DATA_PC_WORK, ".origin_update.lock")


def _origin_lock_pid_alive(pid: int) -> bool:
    """락 파일에 기록된 PID 가 아직 살아 있는지 (Windows: OpenProcess SYNCHRONIZE)."""
    if pid <= 0:
        return False
    if sys.platform != "win32":
        try:
            os.kill(pid, 0)
            return True
        except OSError:
            return False
    import ctypes
    handle = ctypes.windll.kernel32.OpenProcess(0x1000, False, pid)
    if handle:
        ctypes.windll.kernel32.CloseHandle(handle)
        return True
    return False


def _origin_clear_stale_lock():
    """크래시 등으로 남은 .origin_update.lock 제거 (PID 없으면 stale)."""
    path = _origin_update_lock_path()
    if not os.path.isfile(path):
        return
    try:
        with open(path, encoding="ascii") as f:
            pid = int(f.read().strip())
    except (OSError, ValueError):
        try:
            os.unlink(path)
        except OSError:
            pass
        return
    if not _origin_lock_pid_alive(pid):
        try:
            os.unlink(path)
        except OSError:
            pass


def _origin_acquire_lock(wait_sec: int = 900):
    """Origin .opju 동시 열기 방지 — 다른 프로세스 Origin 작업이 끝날 때까지 대기.

    wait_sec 기본 15분: 메일 8건 연속 Origin 시 앞 작업이 길어져도 큐 대기.
    """
    path = _origin_update_lock_path()
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    deadline = time.time() + wait_sec
    while time.time() < deadline:
        _origin_clear_stale_lock()
        try:
            fd = os.open(path, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
            os.write(fd, str(os.getpid()).encode("ascii"))
            os.close(fd)
            return
        except FileExistsError:
            time.sleep(2)
    raise TimeoutError(f"Origin lock timeout ({wait_sec}s): {path}")


def _origin_release_lock():
    """update_origin finally 에서 호출 — 다음 메일/프로세스가 Origin 락 획득 가능."""
    path = _origin_update_lock_path()
    try:
        if os.path.isfile(path):
            os.unlink(path)
    except OSError:
        pass


def _origin_exit_quiet(op):
    """이전 originpro 외부 세션 정리 — op.open 전후·finally 에서 호출."""
    if not getattr(op, "oext", False):
        return
    try:
        op.exit()
    except Exception:
        pass


def _origin_window_texts(hwnd) -> str:
    """Win32: 최상위 창 + 자식 컨트롤 텍스트 수집 (Static 본문 포함)."""
    import ctypes
    from ctypes import wintypes

    user32 = ctypes.windll.user32
    parts: list[str] = []

    @ctypes.WINFUNCTYPE(ctypes.c_bool, wintypes.HWND, wintypes.LPARAM)
    def _enum_child(ch, _):
        buf = ctypes.create_unicode_buffer(2048)
        user32.GetWindowTextW(ch, buf, 2048)
        if buf.value:
            parts.append(buf.value)
        return True

    buf = ctypes.create_unicode_buffer(512)
    user32.GetWindowTextW(hwnd, buf, 512)
    if buf.value:
        parts.append(buf.value)
    user32.EnumChildWindows(hwnd, _enum_child, 0)
    return "\n".join(parts)


def _origin_click_readonly_yes() -> bool:
    """Origin Read-Only 확인창에서 Yes 버튼 SendMessage(BM_CLICK).

    본문은 창 제목이 아니라 자식 Static 에 있으므로 _origin_window_texts 로 검색.
    """
    if sys.platform != "win32":
        return False
    import ctypes
    from ctypes import wintypes

    user32 = ctypes.windll.user32
    BM_CLICK = 0x00F5
    clicked = False

    @ctypes.WINFUNCTYPE(ctypes.c_bool, wintypes.HWND, wintypes.LPARAM)
    def _enum_btn(hwnd, _):
        nonlocal clicked
        buf = ctypes.create_unicode_buffer(32)
        user32.GetClassNameW(hwnd, buf, 32)
        if buf.value != "Button":
            return True
        user32.GetWindowTextW(hwnd, buf, 32)
        label = buf.value.replace("&", "")
        if label.lower() == "yes":
            user32.SendMessageW(hwnd, BM_CLICK, 0, 0)
            clicked = True
            return False
        return True

    @ctypes.WINFUNCTYPE(ctypes.c_bool, wintypes.HWND, wintypes.LPARAM)
    def _enum_top(hwnd, _):
        if not user32.IsWindowVisible(hwnd):
            return True
        text = _origin_window_texts(hwnd).lower()
        if "read-only" not in text and "another instance" not in text:
            return True
        user32.EnumChildWindows(hwnd, _enum_btn, 0)
        return not clicked

    user32.EnumWindows(_enum_top, 0)
    return clicked


def _origin_dialog_watcher(stop_event: threading.Event) -> None:
    """op.open / op.save 블로킹 구간 동안 0.4초마다 Read-Only 창 Yes 시도."""
    while not stop_event.wait(0.4):
        if _origin_click_readonly_yes():
            _log_origin("[Origin] Read-Only 확인창 — Yes 자동 클릭")


def _log_origin(msg: str) -> None:
    """Origin 자동화 이벤트 (자동 Yes 등) — gc-runtime-temp 에만 기록."""
    try:
        log_dir = os.path.join(os.path.expanduser("~"), ".cursor", "gc-runtime-temp")
        os.makedirs(log_dir, exist_ok=True)
        with open(os.path.join(log_dir, "origin_automation.log"), "a", encoding="utf-8") as f:
            f.write(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} {msg}\n")
    except OSError:
        pass


def _open_opju_for_update(op, opju_path: str) -> None:
    """4단계 진입: 세션 정리 → 숨김 → watcher 기동 → op.open(asksave=False)."""
    _origin_exit_quiet(op)
    op.set_show(False)
    stop = threading.Event()
    watcher = threading.Thread(
        target=_origin_dialog_watcher,
        args=(stop,),
        name="origin-readonly-watcher",
        daemon=True,
    )
    watcher.start()
    try:
        if not op.open(opju_path, asksave=False):
            _origin_exit_quiet(op)
            if not op.open(opju_path, asksave=False):
                raise RuntimeError(f"Origin 프로젝트 열기 실패: {opju_path}")
    finally:
        stop.set()
        watcher.join(timeout=3)

# ==========================================
# ⚙️ 사용자 설정 (USER SETTINGS)
# ==========================================
# *** CALIB·TIME 은 해당 **장비**에서 실측. 다른 연구원/장비 값 복사 금지 ***
# 아래 GC2/GC3 블록 = 차헌이 GC2·GC3 **장비**에서 실측한 값 (차헌 PC 스크립트에 저장).
# GC1 블록 = 은규가 GC1 **장비**에서 실측 (은규 PC 스크립트에 저장).
#
# feed 초기 ppm — 파일명에 농도(%)가 없을 때만 사용 (fallback).
# 파일명에 (x)% 가 있으면 화공 양론으로 ppm 을 자동 산출 (resolve_feed_ppm 참고):
#   DRME x% → C2H6 x%, CH4 x%, CO2 3x%
#   DRE  x% → C2H6 x%, CO2 2x%
#   DRM  x% → CH4 x%, CO2 x%
#
# [1] GC2 **장비** 교정 (DRE) — 차헌 PC에서 사용. 값은 GC2 장비 PC 실측.
GC2_INITIAL_C2H6 = 15000
GC2_INITIAL_CO2  = 30000

# [DRM] GC2 **장비** 교정 (DRM)
GC2_DRM_INITIAL_CH4 = 50000 
GC2_DRM_INITIAL_CO2 = 50000

GC2_CALIB = {'H2': 9.9496, 'CO': 97.4074, 'CH4': 25.4261, 'CO2': 77.5254, 'C2H4': 29.8598, 'C2H6': 24.8321}
GC2_TIME = {'H2': (0.4, 0.55), 'CO': (1.3, 1.5), 'CH4': (3.0, 3.6), 'CO2': (5.2, 5.5), 'C2H4': (8.7, 8.9), 'C2H6': (9.5, 10.0)}

# [2] GC3 **장비** 교정 (DRE / DRME) — 차헌 PC에서 사용. 동일 CALIB·나눗셈 수식.
GC3_INITIAL_C2H6 = 15000
GC3_INITIAL_CO2  = 45000
GC3_YIELD_BASE_H2 = 75000   # C2H6_ppm × 5  (1.5% → 75000)
GC3_YIELD_BASE_CO = 90000   # CO2_ppm  × 2  (4.5% → 90000)

# 수율/전환율 교차검증 임계값 (%p)
YIELD_OVER_CONV_TOLERANCE = 2.0    # 수율 > 전환율 — 이론상 불가
CONV_OVER_H2_TOLERANCE = 40.0      # 주반응물 전환율 >> H2 수율 — feed 농도 오기재 전형 패턴
GC3_CALIB = {'H2': 0.12736, 'CO': 0.01504, 'CH4': 0.03004, 'CO2': 0.01839, 'C2H4': 0.18072, 'C2H6': 0.05911}
GC3_TIME_TCD = {'H2': (0.6, 0.8), 'CO': (1.8, 2.2), 'CO2': (6.0, 6.6)}
GC3_TIME_FID = {'CH4': (3.0, 3.8), 'C2H4': (5.0, 5.25), 'C2H6': (5.26, 5.6)}

# [3] GC1 **장비** 교정 (Autochro) — 은규 PC에서 사용. RT/CALIB는 GC1 장비 PC 실측.
#     TIME 1차값: gc_gc1.py DEFAULT_*_WINDOWS 와 동기화 (Step 7.2 — extract_gc1_rt_from_xlsx.py 로 검증)
#     CALIB: GC1 표준가스 교정곡선 (GC1_CALIB_READY=True 시 계산 활성)
GC1_INITIAL_C2H6 = 15000   # DRE fallback 1.5%
GC1_INITIAL_CO2 = 30000
GC1_DRM_INITIAL_CH4 = 50000
GC1_DRM_INITIAL_CO2 = 50000

# RT (분) — center ± half from gc_gc1.DEFAULT_FID/TCD_WINDOWS
GC1_TIME_TCD = {'H2': (1.65, 2.35), 'CO': (5.8, 7.4), 'CO2': (15.0, 17.4)}
GC1_TIME_FID = {'CH4': (1.05, 1.75), 'C2H6': (1.55, 2.25), 'C2H4': (1.95, 2.65)}

# GC3 와 동일: ppm = Area / CALIB
# 교정곡선 (GC1 표준가스, 2026-06 은규 제공): Area = k·ppm  →  CALIB[k] = k
#   CO2: y=0.0168x   H2: y=0.20661x   CO: y=0.01334x
#   CH4: y=0.14741x  C2H4: y=0.30084x  C2H6: y=0.29259x
# (y=Area, x=ppm 기준 — suggest_gc1_calib.py 와 동일 규약)
GC1_CALIB_READY = True
GC1_CALIB = {
    'H2': 0.20661,
    'CO': 0.01334,
    'CO2': 0.0168,
    'CH4': 0.14741,
    'C2H6': 0.29259,
    'C2H4': 0.30084,
}

ORIGIN_MAPPING = {
    'C2H6 Conversion (%)': 'C2H6 conversion',
    'CH4 Conversion (%)': 'CH4 conversion', # DRM 반응용 Origin 시트명 매핑
    'CO2 Conversion (%)': 'CO2 conversion',
    'H2 Yield (%)': 'H2 yield',
    'CO Yield (%)': 'CO yield',
    'CH4 (%)': 'CH4',
    'C2H4 (%)': 'C2H4',
    'C2H6 (%)': 'C2H6', # DRM에서는 C2H6가 부산물이므로 추가
}

# 네이버 IMAP (gc_automation.py 발송 메일 수신용 — gc_automation.env 와 동일 계정)
NAVER_IMAP_HOST = "imap.naver.com"
NAVER_IMAP_PORT = 993
EMAIL_SUBJECT_KEYWORD = "GC 분석 결과"
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))


def _data_pc_work_subdir():
    """
    [LLM] 데이터 PC inbox/processed 상위 폴더명 (script_dir 직하위).

    은규 PC: PEG = Park Eungyu Gyu (박은규 이니셜)
    차헌 PC: KCH = Kim Chaheon (차헌 이니셜, 장비 PC Desktop\\KCH 와 **다른 PC**)

    PEG → KCH 순으로 존재하는 폴더를 탐색. 없으면 KCH 기본(차헌 호환).
    """
    for name in ("PEG", "KCH"):
        if os.path.isdir(os.path.join(SCRIPT_DIR, name)):
            return name
    return "KCH"


_DATA_PC_WORK = _data_pc_work_subdir()
DATA_PC_INBOX_DIR = os.path.join(SCRIPT_DIR, _DATA_PC_WORK, "inbox")
DATA_PC_PROCESSED_DIR = os.path.join(SCRIPT_DIR, _DATA_PC_WORK, "processed")
PROCESSED_MAIL_LOG = os.path.join(DATA_PC_INBOX_DIR, ".processed_mail_ids.txt")


def _machine_profile_path():
    """[LLM] 로컬 PC 식별 파일. Git 미포함 (.gitignore). 장비 PC profile 과 별개."""
    return os.path.join(SCRIPT_DIR, _DATA_PC_WORK, "machine_profile.json")


def _load_machine_profile():
    """
    [LLM] machine_profile.json 로드.
    포함 가능: role, operator, reaction_roots, experiment_data_root, paths.*
  은규 PC 예: reaction_roots → Desktop\\새 폴더\\연구노트\\DRE (G: 미사용)
    """
    path = _machine_profile_path()
    if not os.path.isfile(path):
        return {}
    try:
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
        return data if isinstance(data, dict) else {}
    except (OSError, ValueError, TypeError):
        return {}


def _paths_from_machine_profile():
    """
    [LLM] machine_profile 에서 실험 저장 경로 오버라이드.
    repo REACTION_ROOTS 기본값(G:) 은 차헌 PC 예시 — 은규 PC는 profile 우선.
    """
    prof = _load_machine_profile()
    roots = {}

    raw_roots = prof.get("reaction_roots")
    if isinstance(raw_roots, dict):
        roots = {str(k).upper(): str(v).strip() for k, v in raw_roots.items() if v}

    if not roots:
        paths = prof.get("paths") or {}
        for rt_key, path_key in (
            ("DRE", "reaction_roots_dre"),
            ("DRM", "reaction_roots_drm"),
            ("DRME", "reaction_roots_drme"),
        ):
            val = str(paths.get(path_key, "")).strip()
            if val and "..." not in val:
                roots[rt_key] = val

    exp_root = prof.get("experiment_data_root")
    if not exp_root:
        exp_root = (prof.get("paths") or {}).get("experiment_data_root", "")
    exp_root = str(exp_root or "").strip()
    if "..." in exp_root:
        exp_root = ""

    return roots, exp_root or None


# ---------------------------------------------------------------------------
# 실험 데이터 저장 경로 (3~4단계: 폴더 생성 · Origin)
# ---------------------------------------------------------------------------
# [LLM] REACTION_ROOTS: 반응별 실험 폴더 **루트** — 그 안에 날짜별 하위 폴더 생성.
# EXPERIMENT_DATA_ROOT: 3~4단계 진입 전 이 경로가 os.path.isdir 이면 진행.
#
# 우선순위: machine_profile.json > 아래 repo 기본값
#   · 차헌 PC: G:\\연구소\\... (SecuYouSB 보안 USB)
#   · 은규 PC: C:\\Users\\User\\Desktop\\새 폴더\\연구노트\\DRE 등 (로컬, G: 없음)
#   · DRM/DRME 폴더는 은규 PC에서 아직 없을 수 있음 — 생성 후 profile 에 경로 유지
#
# 상세: docs/DATA_PC_PATHS.md, deploy/DATA_PC_HOME_LAYOUT.md
REACTION_ROOTS = {
    "DRE": r"G:\연구소\실험\실험데이터\촉매 반응\DRE 반응(C2H6)",
    "DRM": r"G:\연구소\실험\실험데이터\촉매 반응\DRM 반응 (CH4)",
    "DRME": r"G:\연구소\실험\실험데이터\촉매 반응\DRME 반응 (C2H6+CH4)",
}
EXPERIMENT_DATA_ROOT = r"G:\연구소\실험\실험데이터"

_profile_roots, _profile_exp_root = _paths_from_machine_profile()
if _profile_roots:
    REACTION_ROOTS = _profile_roots
if _profile_exp_root:
    EXPERIMENT_DATA_ROOT = _profile_exp_root
ENV_FILE_NAMES = (".env", "gc_automation.env")


class GDriveUnavailableError(Exception):
    """G: 실험데이터 경로 없음 — 보안 USB 미로그인/세션 만료. 사용자 직접 해제 필요."""


_INVALID_FOLDER_CHARS = re.compile(r'[<>:"/\\|?*]')


def _load_dotenv_files():
    """script_dir\\gc_automation.env 에서 네이버 IMAP 계정 로드 (NAVER_EMAIL, NAVER_APP_PASSWORD)."""
    try:
        from dotenv import load_dotenv
    except ImportError:
        return False
    for name in ENV_FILE_NAMES:
        for base in (SCRIPT_DIR, os.path.join(SCRIPT_DIR, _DATA_PC_WORK)):
            path = os.path.join(base, name)
            if os.path.isfile(path):
                load_dotenv(path)
    return True


def _g_drive_unavailable_message():
    """
    [LLM] 3~4단계 불가 시 안내. EXPERIMENT_DATA_ROOT 가 보이지 않을 때.
    은규 PC: 연구노트 로컬 경로 확인 | 차헌 PC: SecuYouSB G: 로그인.
    """
    return "\n".join([
        "❌ [실험데이터] EXPERIMENT_DATA_ROOT 경로에 접근할 수 없습니다.",
        "",
        f"  현재 설정: {EXPERIMENT_DATA_ROOT}",
        "",
        "차헌 PC(SecuYouSB): SecuYouSB 로그인 → G:\\연구소\\실험\\... 탐색기 확인",
        "은규 PC(로컬):     연구노트 등 실제 폴더가 있는지 탐색기에서 확인",
        "  machine_profile.json 의 experiment_data_root / reaction_roots 점검",
        "",
        f"※ 2단계 계산 결과는 이미 저장됨: {DATA_PC_PROCESSED_DIR}",
        "   경로 수정 후 같은 메일/파일로 재실행하면 3~4단계를 이어갈 수 있습니다.",
    ])


def _is_g_drive_available():
    """G: 실험데이터 루트 디렉터리 존재 여부만 확인 (잠금 해제 시도 없음)."""
    try:
        return os.path.isdir(EXPERIMENT_DATA_ROOT)
    except OSError:
        return False


def _require_g_drive_access(reaction_type=None):
    """3~4단계 진입 전 G: 접근 가능 여부 검사. 불가 시 GDriveUnavailableError."""
    if not _is_g_drive_available():
        raise GDriveUnavailableError(_g_drive_unavailable_message())
    if reaction_type:
        root = REACTION_ROOTS[reaction_type]
        if not os.path.isdir(root):
            if not _is_g_drive_available():
                raise GDriveUnavailableError(_g_drive_unavailable_message())
            raise FileNotFoundError(f"반응 폴더 없음: {root}")


def _sanitize_folder_name(name):
    """Windows 폴더/파일명 — / \\ : 등 Origin Comments 에 쓸 수 없는 문자 제거."""
    name = _INVALID_FOLDER_CHARS.sub("-", name)
    return re.sub(r"\s+", " ", name).strip(" .")

# ==========================================
# 기능 1: 반응 식별 · 시료명(Origin) · 실험 폴더명(G:) — DRM/DRE/DRME 공통
# ==========================================
# 파일명만으로 반응 종류·촉매·온도를 추출. 사용자가 파일명을 불완전하게 지어도
# generate_sample_name(Origin) 과 generate_experiment_basename(G:) 이 각각 정규화.
# Origin Comments (x) = 주반응물 feed 농도(%): ppm 설정값 ÷ 10000
#   DRE/DRME → C2H6 (15000 ppm → 1.5%)   DRM → CH4 (50000 ppm → 5%)
# Origin 시료명: 촉매 무게 제외 (Ni10/Al2O3 만). G: 폴더명: 무게 포함 가능 (촉매 0.25g).
def get_reaction_type_from_filename(filename):
    """파일 이름에 포함된 반응 종류(DRME, DRM, DRE)를 정확하게 파악합니다."""
    name_upper = os.path.basename(filename).upper()
    if "DRME" in name_upper: return "DRME"
    elif "DRM" in name_upper: return "DRM"
    else: return "DRE" # 기본값은 DRE

def _extract_concentration(name):
    """
    파일명에서 주반응물 feed 농도(%) 추출. 없으면 None.

    [LLM] Origin Comments (x) 및 resolve_feed_ppm 의 입력.
    (x)는 사이클 번호가 아니라 주반응물 mol% — DRE/DRME 는 C2H6, DRM 은 CH4.

    인식 순서 (먼저 매칭된 값 사용):
      1. (1.5)% / 1.5%           — 명시적 %
      2. dre@(3) / DRM@(5)        — gc_automation PDF·KCH stem: 반응@(농도)
         예: 「20260616 dre@(3) ni-ce」 → 3 (C2H6 3%, CO2 6% by stoichiometry)
      3. DRE(3) / DRE (3)        — 반응 토큰 바로 뒤 괄호 (온도 @600 과 별개)
      4. C2H6(1.5) / CH4(5)      — 레거시 화학식 괄호

    매칭 실패 시 _default_concentration() / USER SETTINGS fallback.
    """
    # 1) 명시적 %: (1.5)%, 1.5%
    conc_match = re.search(r'\(?(\d+\.?\d*)\)?\s*%', name)
    if conc_match:
        return conc_match.group(1)
    # 2) KCH/GC stem: dre@(3), DRM@(5) — @ 뒤 괄호 = 농도%, @650 처럼 숫자만 있으면 온도(여기서는 미매칭)
    at_conc = re.search(r'(?:DRE|DRM|DRME)@\((\d+\.?\d*)\)', name, re.I)
    if at_conc:
        return at_conc.group(1)
    # 3) 반응 바로 뒤: DRE(3), DRE (3), DRE(3)@600
    react_conc = re.search(r'(?:DRE|DRM|DRME)\s*\((\d+\.?\d*)\)', name, re.I)
    if react_conc:
        return react_conc.group(1)
    # 4) 레거시: C2H6(1.5), CH4(5)
    legacy = re.search(r'(?:C2H6|CH4)\((\d+\.?\d*)\)', name, re.I)
    if legacy:
        return legacy.group(1)
    return None

def _ppm_to_concentration_label(ppm):
    """ppm feed → Origin Comments 괄호 (x). 10000 ppm = 1% (15000→'1.5', 50000→'5')."""
    return f"{ppm / 10000:g}"

def _default_concentration(reaction):
    """
    파일명에 농도가 없을 때 Origin Comments (x) 기본값.
    (x) = 주반응물 feed 농도(%) — USER SETTINGS 의 ppm 초기값 ÷ 10000.
      DRE:  GC2/GC1_INITIAL_C2H6   (15000 ppm → 1.5%)
      DRME: GC3_INITIAL_C2H6      (15000 ppm → 1.5%)
      DRM:  GC2/GC1_DRM_INITIAL_CH4 (50000 ppm → 5%)
    """
    if reaction == "DRM":
        return _ppm_to_concentration_label(GC2_DRM_INITIAL_CH4)
    if reaction == "DRME":
        return _ppm_to_concentration_label(GC3_INITIAL_C2H6)
    return _ppm_to_concentration_label(GC2_INITIAL_C2H6)

def _default_feed_ppm_for_equipment(reaction, equipment):
    """장비별 feed fallback — GC1 은 GC1_INITIAL_* 사용."""
    if equipment == "GC1":
        if reaction == "DRM":
            return {
                "CH4": GC1_DRM_INITIAL_CH4,
                "CO2": GC1_DRM_INITIAL_CO2,
                "H2_yield_base": GC1_DRM_INITIAL_CH4 * 2,
                "CO_yield_base": GC1_DRM_INITIAL_CH4 + GC1_DRM_INITIAL_CO2,
            }
        if reaction == "DRME":
            return _default_feed_ppm("DRME")
        return {
            "C2H6": GC1_INITIAL_C2H6,
            "CO2": GC1_INITIAL_CO2,
            "H2_yield_base": GC1_INITIAL_C2H6 * 3,
            "CO_yield_base": GC1_INITIAL_C2H6 * 4,
        }
    return _default_feed_ppm(reaction)

def _percent_to_ppm(percent):
    """파일명 농도(%) → ppm. 1% = 10000 ppm."""
    return float(percent) * 10000

def _feed_ppm_from_concentration(reaction, conc_percent):
    """
    화공 양론: 엑셀 파일명의 주반응물 농도(%) → 각 반응물 feed 초기 ppm.

    conc_percent = 파일명 (x)% 값
      DRME: C2H6·CH4 각 x%, CO2 3x%  (예: 1.5% → 15000/15000/45000 ppm)
      DRE:  C2H6 x%, CO2 2x%         (예: 1.5% → 15000/30000 ppm)
      DRM:  CH4 x%, CO2 x%           (예: 1.5% → 15000/15000 ppm)
    """
    c2h6 = _percent_to_ppm(conc_percent)
    ch4 = _percent_to_ppm(conc_percent)
    if reaction == "DRME":
        co2 = _percent_to_ppm(conc_percent) * 3
        return {
            "C2H6": c2h6,
            "CH4": ch4,
            "CO2": co2,
            "H2_yield_base": c2h6 * 5,
            "CO_yield_base": co2 * 2,
        }
    if reaction == "DRE":
        co2 = _percent_to_ppm(conc_percent) * 2
        return {
            "C2H6": c2h6,
            "CO2": co2,
            "H2_yield_base": c2h6 * 3,
            "CO_yield_base": c2h6 * 4,
        }
    if reaction == "DRM":
        co2 = _percent_to_ppm(conc_percent)
        return {
            "CH4": ch4,
            "CO2": co2,
            "H2_yield_base": ch4 * 2,
            "CO_yield_base": ch4 + co2,
        }
    raise ValueError(f"알 수 없는 반응: {reaction}")

def _default_feed_ppm(reaction):
    """파일명에 농도가 없을 때 USER SETTINGS 기본 ppm (fallback)."""
    if reaction == "DRME":
        return {
            "C2H6": GC3_INITIAL_C2H6,
            "CH4": GC3_INITIAL_C2H6,
            "CO2": GC3_INITIAL_CO2,
            "H2_yield_base": GC3_YIELD_BASE_H2,
            "CO_yield_base": GC3_YIELD_BASE_CO,
        }
    if reaction == "DRM":
        return {
            "CH4": GC2_DRM_INITIAL_CH4,
            "CO2": GC2_DRM_INITIAL_CO2,
            "H2_yield_base": GC2_DRM_INITIAL_CH4 * 2,
            "CO_yield_base": GC2_DRM_INITIAL_CH4 + GC2_DRM_INITIAL_CO2,
        }
    return {
        "C2H6": GC2_INITIAL_C2H6,
        "CO2": GC2_INITIAL_CO2,
        "H2_yield_base": GC2_INITIAL_C2H6 * 3,
        "CO_yield_base": GC2_INITIAL_C2H6 * 4,
    }

def _format_feed_stoichiometry(reaction, conc_percent):
    """교차검증 메시지용 — 파일명 농도에 따른 feed 조성 요약."""
    pct = float(conc_percent)
    if reaction == "DRME":
        return f"C2H6 {pct:g}%, CH4 {pct:g}%, CO2 {pct * 3:g}%"
    if reaction == "DRE":
        return f"C2H6 {pct:g}%, CO2 {pct * 2:g}%"
    if reaction == "DRM":
        return f"CH4 {pct:g}%, CO2 {pct:g}%"
    return ""

def resolve_feed_ppm(input_file, reaction_type, equipment=None):
    """
    계산에 사용할 초기 feed ppm 결정.
    파일명 (x)% 우선 → 화공 양론 산출. 없으면 USER SETTINGS fallback.

    equipment: 'GC1'|'GC2'|'GC3' — fallback ppm 장비별 분기 (GC1 → GC1_INITIAL_*)

    반환: (feed_ppm dict, conc_label str|None, feed_source_desc str)
    """
    basename = os.path.basename(input_file)
    conc_str = _extract_concentration(basename)
    if conc_str:
        feed = _feed_ppm_from_concentration(reaction_type, conc_str)
        desc = (
            f"파일명 {conc_str}% 기준 {reaction_type} "
            f"({_format_feed_stoichiometry(reaction_type, conc_str)})"
        )
        return feed, conc_str, desc
    if equipment:
        feed = _default_feed_ppm_for_equipment(reaction_type, equipment)
    else:
        feed = _default_feed_ppm(reaction_type)
    default_pct = _default_concentration(reaction_type)
    desc = (
        f"파일명에 농도 없음 — USER SETTINGS 기본 {default_pct}% "
        f"({_format_feed_stoichiometry(reaction_type, default_pct)})"
    )
    return feed, None, desc

def _validate_yield_conversion(df_result, reaction_target, feed_source_desc):
    """
    수율/전환율 교차검증 — feed 농도(%) 오기재 시 나타나는 전형적 이상 패턴.

    1) H2/CO 수율 > 반응물 전환율 — 이론상 불가 (잘못된 ppm 기준)
    2) DRE/DRME: C2H6 전환율이 H2 수율보다 40%p 이상 큼
    3) DRM: CH4 전환율이 H2 수율보다 40%p 이상 큼
    위 패턴 발생 시 feed_source_desc(파일명 농도·화공 양론)와 함께 경고.
    """
    warnings = []
    conv_reactant_col = "CH4 Conversion (%)" if reaction_target == "DRM" else "C2H6 Conversion (%)"
    reactant_name = "CH4" if reaction_target == "DRM" else "C2H6"

    yield_over_conv_cycles = []
    conv_over_h2_cycles = []

    for c in df_result.index:
        reactant_conv = df_result.at[c, conv_reactant_col]
        co2_conv = df_result.at[c, "CO2 Conversion (%)"]
        max_conv = max(reactant_conv, co2_conv)
        h2_yield = df_result.at[c, "H2 Yield (%)"]
        co_yield = df_result.at[c, "CO Yield (%)"]

        if h2_yield > max_conv + YIELD_OVER_CONV_TOLERANCE or co_yield > max_conv + YIELD_OVER_CONV_TOLERANCE:
            yield_over_conv_cycles.append(str(c))
        if reactant_conv > h2_yield + CONV_OVER_H2_TOLERANCE:
            conv_over_h2_cycles.append(str(c))

    def _cycle_str(cycles):
        return ", ".join(cycles[:3]) + (" 등" if len(cycles) > 3 else "")

    if yield_over_conv_cycles:
        warnings.append(
            f"🚨 [교차검증] Cycle {_cycle_str(yield_over_conv_cycles)}: "
            f"H2/CO 수율이 반응물 전환율을 초과 (이론상 불가). "
            f"{feed_source_desc} — 파일명 농도(%) 또는 장비 실제 투여량을 확인하세요."
        )
    if conv_over_h2_cycles:
        warnings.append(
            f"🚨 [교차검증] Cycle {_cycle_str(conv_over_h2_cycles)}: "
            f"{reactant_name} 전환율이 H2 수율보다 {CONV_OVER_H2_TOLERANCE:g}%p 이상 큼. "
            f"{feed_source_desc} — 반응물 농도(%) 오기재 가능성."
        )
    return warnings

def generate_sample_name(filename):
    """
    Origin Comments 전용 — DRM / DRE / DRME 공통 엄격 규칙.

    (x) = 주반응물 feed 농도(%): DRE/DRME C2H6, DRM CH4 (ppm 설정값 기준).

    촉매 무게 규칙 (2026-06 적용, DRE/DRME/DRM 동일):
      · KCH 파일명의 "0.25g" 등은 _strip_catalyst_mass() 로 제거 후 Comments 에 기록
      · 슬래시(/) 뒤에 무게를 붙이지 않음
        OK: 20260612 DRM(5)@650°C Ni10/Al2O3
        NG: 20260612 DRM(5)@650°C Ni10/Al2O3/0.25g

    G: 폴더명(generate_experiment_basename)과 혼용하지 말 것 — 폴더에는 무게가 남을 수 있음.
    """
    name = _normalize_input_basename(filename)

    # gc_automation KCH 형식: "20260613 Ni10-Al2O3 0.25g DRM@650"
    # → Origin: "20260613 DRM(5)@650°C Ni10/Al2O3" (0.25g 는 Comments 에 미포함)
    kch_match = re.match(r'^(\d{8})\s+(.+?)\s+(DRE|DRM|DRME)@(\d+)\s*$', name, re.I)
    if kch_match:
        date, catalyst, reaction, temp = kch_match.groups()
        reaction = reaction.upper()
        conc = _extract_concentration(name) or _default_concentration(reaction)
        cat_fmt = _format_kch_catalyst(catalyst)  # 무게 제거 후 Ni10/Al2O3 형식
        return f"{date} {reaction}({conc})@{temp}°C {cat_fmt}"

    date_match = re.search(r'(\d{8})', name)
    date = date_match.group(1) if date_match else "00000000"
    reaction = get_reaction_type_from_filename(filename)
    conc = _extract_concentration(name) or _default_concentration(reaction)

    temp_match = re.search(r'@(\d+)', name)
    temp = temp_match.group(1) if temp_match else "600"

    cat_str = re.sub(r'\d{8}', '', name)
    cat_str = re.sub(r'\(GC3[^)]*\)', '', cat_str, flags=re.IGNORECASE)
    # 반응·부가 접미사 제거 후 촉매 토큰만 남김 (Origin Comments 촉매부)
    cat_str = re.sub(r'DRME|DRM|DRE|_원본|_GC.*|계산완료|\.xlsx|\.xls|C2H6|CH4', '', cat_str, flags=re.IGNORECASE)
    # dre@(3) — 농도 표기는 촉매명이 아니므로 제거 (@650 온도는 아래 @\d+ 에서 제거)
    cat_str = re.sub(r'@\([^)]*\)', '', cat_str)
    cat_str = re.sub(r'\(?\d+\.?\d*\)?\s*%', '', cat_str)
    cat_str = re.sub(r'\(\d+\.?\d*\)', '', cat_str)  # DRE(3) 농도 괄호
    cat_str = re.sub(r'@\d+', '', cat_str)  # @600 온도
    cat_str = _strip_catalyst_mass(cat_str)  # 비-KCH 파일명 fallback 도 무게 제외
    cat_str = _format_catalyst_string(cat_str)
    return f"{date} {reaction}({conc})@{temp}°C {cat_str}"

def _format_catalyst_string(cat_str):
    """촉매 문자열을 Origin용 포맷(Ni_CVD(...)/Ni5/Al2O3)으로 변환."""
    cat_str = cat_str.strip(' _-')

    def fix_cvd(m):
        # Ni_CVD(...) 안의 CVD(0.1g,8h) 재매칭 방지 → Ni_CVD_CVD 중복
        if m.group(1) == 'CVD' or (m.start() > 0 and m.string[m.start() - 1] == '_'):
            return m.group(0)
        metal, val1, val2 = m.group(1), m.group(2).strip(), m.group(3).strip()
        if val1 and not val1.endswith('g') and 'h' not in val1: val1 += 'g'
        return f"{metal}_CVD({val1},{val2})"

    cat_str = re.sub(r'([A-Za-z]+)\s*\(([^,]+),\s*([^)]+)\)', fix_cvd, cat_str)
    cat_str = cat_str.replace('-', '/')
    if cat_str.count(')') > cat_str.count('('): cat_str = cat_str.replace(')', '', 1)
    return re.sub(r'\s+', '', cat_str)

def _strip_catalyst_mass(catalyst_part):
    """
    Origin 시료명 전용 — 촉매 무게(0.25g, 0.5g 등) 제거. DRE/DRME/DRM 공통.

    입력 파일명·KCH 촉매 토큰에서 끝의 "\\d+g" 만 잘라냄.
      "Ni10-Al2O3 0.25g" → "Ni10-Al2O3"
    G: 폴더명 생성에는 사용하지 않음 (generate_experiment_basename 이 원본에서 무게 유지).
    """
    catalyst_part = (catalyst_part or "").strip()
    mass_match = re.search(r'(\d+\.?\d*)\s*g\s*$', catalyst_part, re.I)
    if mass_match:
        return catalyst_part[:mass_match.start()].strip()
    return catalyst_part

def _format_kch_catalyst(catalyst_part):
    """KCH 파일명 촉매 토큰 → Origin Comments 촉매부 (무게 제외, 슬래시 구분)."""
    return _format_catalyst_string(_strip_catalyst_mass(catalyst_part))

def _calc_output_path(input_file, suffix):
    """inbox 원본은 DATA_PC/processed/, 그 외는 입력 파일과 같은 폴더에 저장."""
    base = _normalize_input_basename(input_file)
    out_name = f"{base}{suffix}.xlsx"
    src_dir = os.path.normpath(os.path.dirname(os.path.abspath(input_file)))
    if src_dir == os.path.normpath(DATA_PC_INBOX_DIR):
        os.makedirs(DATA_PC_PROCESSED_DIR, exist_ok=True)
        return os.path.join(DATA_PC_PROCESSED_DIR, out_name)
    return os.path.join(src_dir, out_name)

def _strip_calc_suffix(name):
    return re.sub(r'_GC2_(DRE|DRM)_계산완료$|_GC3_(DRE|DRME)_계산완료$|_GC1_(DRE|DRM)_계산완료$', '', name)

def _strip_mail_dedup_suffix(name):
    """IMAP 첨부 중복 저장 시 붙는 _1781505851 같은 타임스탬프 접미사 제거."""
    return re.sub(r'_\d{10,}$', '', name)

def _normalize_input_basename(filename):
    """시료명·폴더명 파싱 전 — 계산완료 접미사·메일 dedup 접미사 제거."""
    name = os.path.splitext(os.path.basename(filename))[0]
    name = _strip_calc_suffix(name)
    return _strip_mail_dedup_suffix(name)

def _normalize_origin_key(text):
    """Origin 북명(H2yield) ↔ 매핑 키(H2 yield) 비교용 — 공백 제거 후 소문자."""
    return re.sub(r'\s+', '', (text or '').lower())

def _experiment_identity_key(source):
    """
    (YYYYMMDD, sample_key) — 메일·G: 폴더 중복 판별용.
    gc_automation KCH 파일명 기준: 날짜 + 시료(촉매·반응@온도).

    중복으로 묶이는 경우: 날짜·시료명이 모두 같은 메일 (재전송 등).
    별도 실험으로 처리: 시료명만 달라도 각각 반영
      · DRE + DRME 동시 수신 → 2건 모두 작업
      · 기존 DRE 연속 + 새 DRE (촉매/조건 다름) → 2건 모두 작업
    """
    if isinstance(source, tuple):
        return source
    if os.path.isdir(source):
        name = os.path.basename(source.rstrip("\\/"))
    else:
        name = _normalize_input_basename(source)
    match = re.match(r'^(\d{8})\s+(.+)$', name, re.I)
    if match:
        return (match.group(1), match.group(2).strip().lower())
    date_match = re.search(r'(\d{8})', name)
    return (date_match.group(1) if date_match else "00000000", name.lower())

def _identity_match_tokens(sample_key):
    """시료 문자열에서 G: 폴더 중복 비교용 토큰."""
    tokens = set(re.findall(r'@\d+|\d+\.?\d*g|dre|drm|drme', sample_key.lower()))
    tokens.update(re.findall(r'[a-z]+\d*|[a-z]{1,2}\d+', sample_key.lower()))
    return {t for t in tokens if len(t) >= 2 or t.endswith('g')}

def _folder_matches_experiment_identity(folder_name, identity_key):
    """같은 날짜·시료 실험의 잘못된 폴더명인지 판별."""
    date, sample = identity_key
    if not folder_name.startswith(date):
        return False
    tokens = _identity_match_tokens(sample)
    if not tokens:
        return False
    folder_lower = folder_name.lower()
    matched = sum(1 for token in tokens if token in folder_lower)
    return matched >= max(2, int(len(tokens) * 0.6))

def _is_likely_malformed_folder_name(name):
    """버그 등으로 생긴 의심 폴더명 — 템플릿 후보에서 제외."""
    return bool(re.search(r'[_-]\d{2,4}$', name)) and '촉매' not in name

def _folder_is_stale_duplicate(folder_name, keep_folder_name, identity_key):
    """정상 반영 폴더(keep) 외 같은 시료의 중복·오류 폴더인지 판별."""
    if folder_name == keep_folder_name:
        return False
    if not _folder_matches_experiment_identity(folder_name, identity_key):
        return False
    if _is_likely_malformed_folder_name(folder_name):
        return True
    # keep 이 정상 폴더면 같은 시료의 다른 이름 폴더는 중복으로 간주
    if not _is_likely_malformed_folder_name(keep_folder_name):
        return True
    return False

def _cleanup_duplicate_experiment_folders(reaction_type, keep_folder_name, identity_key):
    """정상 반영 폴더 외, 같은 날짜·시료의 중복 G: 폴더 자동 삭제."""
    if not _is_g_drive_available():
        return
    root = REACTION_ROOTS[reaction_type]
    deleted = []
    try:
        for name in os.listdir(root):
            if name == keep_folder_name:
                continue
            path = os.path.join(root, name)
            if not os.path.isdir(path) or name.startswith("."):
                continue
            if _folder_is_stale_duplicate(name, keep_folder_name, identity_key):
                shutil.rmtree(path)
                deleted.append(name)
    except OSError as exc:
        print(f"  [경고] 중복 폴더 정리 실패: {exc}")
        return
    for name in deleted:
        print(f"  → 중복 폴더 삭제: {name}")

# ---------------------------------------------------------------------------
# G: Canonical Chain — 날짜만 다른 동일 시료 중복 폴더 정리 (DRM/DRE/DRME 공통)
# ---------------------------------------------------------------------------
# 비유: 비트코인에서 누적 작업량(주입 수)이 가장 많은 체인을 정통(canonical) 체인으로 합의.
# 조건: 폴더 안 xlsx 의 주입 데이터가 prefix 로 일치할 때만 짧은 체인 폴더 삭제.
CHAIN_COMPARE_COLS = [
    "H2 Yield (%)",
    "CO Yield (%)",
    "C2H6 Conversion (%)",
    "CO2 Conversion (%)",
    "CH4 Conversion (%)",
]
CHAIN_COMPARE_RTOL = 1e-3
CHAIN_COMPARE_ATOL = 0.05

def _folder_sample_key(folder_name):
    """
    날짜·Windows 중복 접미사 (3) 제외 후 시료 동일성 비교 키.
    예) 20260611 DRME(1.5%) Ni(0.1g,8h)-Ni5-Ce5-Al2O3
        20260612 DRME(1.5%) Ni(0.1g,8h)-Ni5-Ce5-Al2O3 (3)  → 동일 키
    """
    key = re.sub(r"^\d{8}\s+", "", folder_name.strip())
    key = re.sub(r"\s+\(\d+\)\s*$", "", key)
    return re.sub(r"\s+", " ", key).lower()

def _folder_date_prefix(folder_name):
    match = re.match(r"^(\d{8})", folder_name)
    return match.group(1) if match else "00000000"

def _find_folder_archive_xlsx(folder_path):
    """실험 폴더 안 아카이브용 xlsx 1개 (임시 ~$ 제외, 가장 큰 파일 우선)."""
    candidates = []
    for name in os.listdir(folder_path):
        if name.startswith("~$"):
            continue
        if name.lower().endswith((".xlsx", ".xls")):
            candidates.append(os.path.join(folder_path, name))
    if not candidates:
        return None
    return max(candidates, key=os.path.getsize)

def _metric_label_to_column(label):
    """레거시 G: xlsx 헤더 셀 → 표준 지표 열 이름."""
    text = re.sub(r"\s+", " ", str(label).replace("\n", " ")).strip().lower()
    mapping = {
        "h2 yield": "H2 Yield (%)",
        "co yield": "CO Yield (%)",
        "c2h6 conversion": "C2H6 Conversion (%)",
        "co2 conversion": "CO2 Conversion (%)",
        "ch4 conversion": "CH4 Conversion (%)",
    }
    for key, col in mapping.items():
        if key in text:
            return col
    return None

def _try_parse_legacy_archive_excel(xlsx_path):
    """
    레거시 G: 아카이브 xlsx (행=주입, 열 12~15 부근에 전환율/수율).
    표준 계산완료 형식 이전에 수동 저장된 사본 호환.
    """
    try:
        raw = pd.read_excel(xlsx_path, header=None)
    except Exception:
        return None, 0
    if raw.shape[1] < 12 or raw.shape[0] < 3:
        return None, 0

    header_row = None
    col_map = {}
    for i in range(min(6, len(raw))):
        for j in range(raw.shape[1]):
            col_name = _metric_label_to_column(raw.iloc[i, j])
            if col_name:
                col_map[col_name] = j
        if len(col_map) >= 2:
            header_row = i
            break

    if not col_map:
        return None, 0

    rows = []
    for i in range(header_row + 1, len(raw)):
        record = {}
        valid = 0
        for metric, j in col_map.items():
            try:
                val = float(raw.iloc[i, j])
                if np.isfinite(val):
                    record[metric] = val
                    valid += 1
            except (TypeError, ValueError):
                continue
        if valid < max(2, len(col_map) // 2):
            break
        rows.append(record)

    if not rows:
        return None, 0

    metrics_df = pd.DataFrame(rows, index=range(1, len(rows) + 1))
    return metrics_df, len(metrics_df)

def _try_parse_calculated_archive_excel(xlsx_path):
    """본 스크립트 계산완료 xlsx — 행=Cycle(주입), 열=Area/전환율/수율."""
    try:
        df = pd.read_excel(xlsx_path)
    except Exception:
        return None, 0

    if "Cycle" in df.columns:
        cycles = pd.to_numeric(df["Cycle"], errors="coerce")
        df = df.drop(columns=["Cycle"])
    else:
        try:
            df = pd.read_excel(xlsx_path, index_col=0)
        except Exception:
            return None, 0
        cycles = pd.to_numeric(df.index, errors="coerce")

    valid = []
    for i, c in enumerate(cycles):
        if pd.isna(c) or not np.isfinite(c):
            continue
        if int(c) != c:
            continue
        valid.append(i)

    if not valid:
        return None, 0

    df = df.iloc[valid]
    available = [c for c in CHAIN_COMPARE_COLS if c in df.columns]
    if not available:
        return None, 0

    metrics_df = df[available].apply(pd.to_numeric, errors="coerce")
    metrics_df.index = range(1, len(metrics_df) + 1)
    return metrics_df, len(metrics_df)

def _extract_injection_metrics(xlsx_path):
    """
    G: 폴더 xlsx → (cycle-indexed metrics DataFrame, 주입 수).
    주입 수 = 사이클(주입) 횟수. (계산완료 xlsx: 데이터 행 수)
    """
    if not xlsx_path or not os.path.isfile(xlsx_path):
        return None, 0

    metrics_df, count = _try_parse_calculated_archive_excel(xlsx_path)
    if metrics_df is not None and count > 0:
        return metrics_df, count

    metrics_df, count = _try_parse_legacy_archive_excel(xlsx_path)
    if metrics_df is not None and count > 0:
        return metrics_df, count

    return None, 0

def _chains_are_compatible(metrics_a, metrics_b):
    """
    두 xlsx 체인이 동일 실험의 prefix 관계인지 (canonical chain 판별).
    길이가 다르면 짧은 쪽이 긴 쪽의 앞부분과 수치 일치해야 함.
    """
    if metrics_a is None or metrics_b is None or metrics_a.empty or metrics_b.empty:
        return False

    cols = [c for c in CHAIN_COMPARE_COLS if c in metrics_a.columns and c in metrics_b.columns]
    if len(cols) < 2:
        return False

    a = metrics_a[cols].apply(pd.to_numeric, errors="coerce")
    b = metrics_b[cols].apply(pd.to_numeric, errors="coerce")
    na, nb = len(a), len(b)
    if na == 0 or nb == 0:
        return False

    if na <= nb:
        shorter, longer = a, b.iloc[:na]
    else:
        shorter, longer = b, a.iloc[:nb]

    try:
        return np.allclose(
            shorter.values,
            longer.values,
            rtol=CHAIN_COMPARE_RTOL,
            atol=CHAIN_COMPARE_ATOL,
            equal_nan=True,
        )
    except (TypeError, ValueError):
        return False

def _canonical_folder_rank(folder_name, injection_count):
    """주입 수 최다 → 날짜 최신 → 이름 순으로 canonical 우선순위."""
    return (injection_count, _folder_date_prefix(folder_name), folder_name)

def _cleanup_canonical_experiment_folders(reaction_type, focus_sample_key=None):
    """
    [Canonical Chain] 동일 시료·다른 날짜 중복 G: 폴더 정리 — DRM/DRE/DRME 공통.

    1) 시료 키(날짜 제외)로 폴더 그룹화
    2) 그룹 내 xlsx 주입 데이터가 prefix 로 일치하면 같은 체인
    3) 주입 수가 가장 많은 폴더만 유지, 나머지 폴더 전체 삭제 (.opju/.pptx/.xlsx)
    4) 내용이 다르면 삭제하지 않음

    focus_sample_key: 지정 시 해당 시료 그룹만 검사 (3단계 직후 빠른 정리).
    """
    if not _is_g_drive_available():
        return

    root = REACTION_ROOTS[reaction_type]
    try:
        folder_names = [
            name for name in os.listdir(root)
            if os.path.isdir(os.path.join(root, name)) and not name.startswith(".")
        ]
    except OSError as exc:
        print(f"  [경고] canonical chain 정리 실패: {exc}")
        return

    groups = {}
    for name in folder_names:
        sample_key = _folder_sample_key(name)
        if focus_sample_key and sample_key != focus_sample_key:
            continue
        groups.setdefault(sample_key, []).append(name)

    deleted = []
    for sample_key, names in groups.items():
        if len(names) < 2:
            continue

        folder_metrics = []
        for name in names:
            folder_path = os.path.join(root, name)
            xlsx_path = _find_folder_archive_xlsx(folder_path)
            metrics_df, injection_count = _extract_injection_metrics(xlsx_path)
            if metrics_df is None or injection_count <= 0:
                continue
            folder_metrics.append((name, metrics_df, injection_count))

        if len(folder_metrics) < 2:
            continue

        folder_metrics.sort(key=lambda item: _canonical_folder_rank(item[0], item[2]), reverse=True)
        keep_name, keep_metrics, keep_count = folder_metrics[0]

        for name, metrics_df, injection_count in folder_metrics[1:]:
            if not _chains_are_compatible(keep_metrics, metrics_df):
                continue
            if injection_count >= keep_count:
                continue
            folder_path = os.path.join(root, name)
            try:
                shutil.rmtree(folder_path)
                deleted.append((name, keep_name, injection_count, keep_count))
            except OSError as exc:
                print(f"  [경고] canonical chain 폴더 삭제 실패 ({name}): {exc}")

    for name, keep_name, short_count, long_count in deleted:
        print(
            f"  → [canonical chain] 중복 폴더 삭제: {name} "
            f"(주입 {short_count}회) — 유지: {keep_name} (주입 {long_count}회)"
        )

def _cleanup_all_canonical_experiment_folders(focus_sample_key=None):
    """DRM/DRE/DRME 전 반응 루트에 canonical chain 정리 적용."""
    for reaction_type in REACTION_ROOTS:
        _cleanup_canonical_experiment_folders(reaction_type, focus_sample_key=focus_sample_key)

def _find_opju_in_folder(folder_path, preferred_stem):
    preferred = os.path.join(folder_path, f"{preferred_stem}.opju")
    if os.path.isfile(preferred):
        return preferred
    for name in os.listdir(folder_path):
        if name.lower().endswith(".opju") and "_Updated" not in name:
            return os.path.join(folder_path, name)
    return None

def generate_experiment_basename(filename):
    """
    G: 실험 폴더·파일 stem — DRM / DRE / DRME 공통.
    Origin Comments와 (x) 농도 규칙은 동일, 표기만 다름 (폴더: °C 없음, / → 하이픈).

    촉매 무게: G: 폴더명에는 유지 (DRM → "촉매 0.25g").
    Origin Comments(generate_sample_name)에는 무게를 넣지 않음 — 두 함수 결과가 다를 수 있음.

      폴더: 20260615 DRE(1.5)@600 Ni20-Al2O3
            20260613 DRM(5)@650C Ni10-Al2O3 촉매 0.25g
      Origin: 20260615 DRE(1.5)@600°C Ni20/Al2O3
              20260613 DRM(5)@650°C Ni10/Al2O3

    입력 파일명이 규칙과 달라도 유연하게 해석해 폴더명만 만듭니다.
    """
    name = _normalize_input_basename(filename)
    folder = _build_experiment_basename(name, filename)
    return _sanitize_folder_name(folder)

def _build_experiment_basename(name, filename):
    if re.match(r'^\d{8}\s+(DRE\s*\(|DRME\s*\(|DRM\s*\()', name, re.I):
        return re.sub(r'°C', '', name).strip()

    kch = re.match(r'^(\d{8})\s+(.+?)\s+(DRE|DRM|DRME)@(\d+)\s*$', name, re.I)
    if kch:
        date, catalyst, reaction, temp = kch.groups()
        reaction, catalyst = reaction.upper(), catalyst.strip()
        conc = _extract_concentration(name) or _default_concentration(reaction)
        if reaction == "DRM":
            # G: 폴더명 — 촉매 무게 유지 (Origin Comments 와 별도 규칙)
            mass = re.search(r'(\d+\.?\d*)\s*g\s*$', catalyst, re.I)
            if mass:
                cat_name = catalyst[:mass.start()].strip()
                return f"{date} DRM({conc})@{temp}C {cat_name} 촉매 {mass.group(0).strip()}"
            return f"{date} DRM({conc})@{temp}C {catalyst}"
        if reaction == "DRME":
            return f"{date} DRME({conc}%) {catalyst}"
        return f"{date} DRE({conc})@{temp} {catalyst}"

    drme = re.match(r'^(\d{8})\s+DRME\s+(\d+\.?\d*)\s*%\s*(.+)$', name, re.I)
    if drme:
        return f"{drme.group(1)} DRME({drme.group(2)}%) {drme.group(3).strip()}"

    sample = generate_sample_name(filename)
    head = re.match(r'^(\d{8})\s+(DRE|DRM|DRME)\(([^)]+)\)@(\d+)°C\s*(.*)$', sample)
    if head:
        date, reaction, conc, temp, cat = head.groups()
        reaction = reaction.upper()
        if reaction == "DRM":
            # Origin 시료명에는 무게 없음 → 폴더명용 무게는 원본 KCH 파일명에서 복원
            mass_m = re.search(r'(\d+\.?\d*)\s*g', name, re.I)
            cat_folder = cat.replace('/', '-')
            if mass_m:
                return f"{date} DRM({conc})@{temp}C {cat_folder} 촉매 {mass_m.group(0).strip()}"
            return f"{date} DRM({conc})@{temp}C {cat_folder}"
        if reaction == "DRME":
            return f"{date} DRME({conc}%) {cat.replace('/', '-')}"
        return f"{date} DRE({conc})@{temp} {cat.replace('/', '-')}"

    return re.sub(r'°C', '', sample).replace('/', '-').strip()

def reaction_type_from_output_file(saved_excel):
    base = os.path.basename(saved_excel)
    if "_GC2_DRM_" in base: return "DRM"
    if "_GC1_DRM_" in base: return "DRM"
    if "_GC3_DRE_" in base: return "DRE"
    if "_GC3_DRME_" in base: return "DRME"
    if "_GC2_DRE_" in base: return "DRE"
    if "_GC1_DRE_" in base: return "DRE"
    return get_reaction_type_from_filename(saved_excel)

def _find_latest_experiment_folder(reaction_type):
    """반응 루트 아래 폴더명(문자열) 기준 max → 최신 실험 템플릿."""
    _require_g_drive_access(reaction_type)
    root = REACTION_ROOTS[reaction_type]
    try:
        folders = [
            name for name in os.listdir(root)
            if os.path.isdir(os.path.join(root, name))
            and not name.startswith(".")
            and not _is_likely_malformed_folder_name(name)
        ]
    except OSError as exc:
        raise GDriveUnavailableError(_g_drive_unavailable_message()) from exc
    if not folders:
        raise FileNotFoundError(f"템플릿으로 쓸 실험 폴더 없음: {root}")
    latest_name = max(folders)
    return os.path.join(root, latest_name), latest_name

def _get_folder_file_stem(folder_path):
    for name in os.listdir(folder_path):
        if name.lower().endswith(".opju") and "_Updated" not in name:
            return os.path.splitext(name)[0]
    return os.path.basename(folder_path)

def setup_experiment_folder(source_excel, calculated_excel, reaction_type):
    """
    [3단계] G: 실험 폴더 생성.

    사용자 요구사항:
      · 반응별 REACTION_ROOTS 에서 폴더명(날짜…) 기준 최신 실험 폴더를 템플릿으로 복사
      · 새 폴더명 = generate_experiment_basename() (Origin Comments 와 별도 규칙)
      · 템플릿 .opju 에는 이전 시료 열이 누적 → 4단계에서 새 열 1개 추가
      · .pptx 이름 변경, 기존 .xlsx 삭제, 계산 xlsx 배치 (오류 검토용)
    """
    _require_g_drive_access(reaction_type)
    experiment_base = generate_experiment_basename(source_excel)
    identity_key = _experiment_identity_key(source_excel)
    root = REACTION_ROOTS[reaction_type]
    dest_dir = os.path.join(root, experiment_base)
    archive_xlsx = os.path.join(dest_dir, f"{experiment_base}.xlsx")

    if os.path.exists(dest_dir):
        print(f"\n[3단계] G: 기존 실험 폴더 갱신 ({reaction_type})")
        print(f"  폴더: {experiment_base}")
        opju_path = _find_opju_in_folder(dest_dir, experiment_base)
        if not opju_path:
            raise FileNotFoundError(f"기존 폴더에서 .opju 를 찾지 못함: {dest_dir}")
        shutil.copy2(calculated_excel, archive_xlsx)
        print(f"  → {archive_xlsx}")
        _cleanup_duplicate_experiment_folders(reaction_type, experiment_base, identity_key)
        _cleanup_canonical_experiment_folders(
            reaction_type, focus_sample_key=_folder_sample_key(experiment_base)
        )
        return dest_dir, opju_path, archive_xlsx

    template_dir, template_name = _find_latest_experiment_folder(reaction_type)
    template_stem = _get_folder_file_stem(template_dir)

    print(f"\n[3단계] G: 실험 폴더 생성 ({reaction_type})")
    print(f"  템플릿 (폴더명 최신): {template_name}")
    print(f"  새 폴더: {experiment_base}")

    try:
        shutil.copytree(template_dir, dest_dir)
    except OSError as exc:
        if not _is_g_drive_available():
            raise GDriveUnavailableError(_g_drive_unavailable_message()) from exc
        raise

    opju_path = None
    for fname in list(os.listdir(dest_dir)):
        lower = fname.lower()
        src = os.path.join(dest_dir, fname)
        if lower.endswith((".xlsx", ".xls")):
            os.remove(src)
            continue
        if lower.endswith(".opju"):
            opju_path = os.path.join(dest_dir, f"{experiment_base}.opju")
            if os.path.normcase(src) != os.path.normcase(opju_path):
                os.rename(src, opju_path)
            continue
        if lower.endswith(".pptx") and not fname.startswith("~$"):
            new_name = fname.replace(template_stem, experiment_base, 1)
            if new_name == fname:
                new_name = f"{experiment_base}.pptx"
            dest = os.path.join(dest_dir, new_name)
            if os.path.normcase(src) != os.path.normcase(dest):
                os.rename(src, dest)

    if not opju_path or not os.path.isfile(opju_path):
        raise FileNotFoundError(f"복사된 폴더에서 .opju 를 찾지 못함: {dest_dir}")

    shutil.copy2(calculated_excel, archive_xlsx)
    print(f"  → {archive_xlsx}")
    _cleanup_duplicate_experiment_folders(reaction_type, experiment_base, identity_key)
    _cleanup_canonical_experiment_folders(
        reaction_type, focus_sample_key=_folder_sample_key(experiment_base)
    )
    return dest_dir, opju_path, archive_xlsx

# ==========================================
# 기능 2: GC 시트 파싱 · 피크/RT 이상 감지
# ==========================================
# KCH 원본 엑셀: Time/Area 열, # 행으로 사이클 구분.
# GC2: H2 RT 구간으로 장비 판별. GC3: TCD+FID 시트 병합(DRME).
# GC3 갭: gc_chem32 가 FID/TCD 시트에 삽입한 ``#``+``중단`` 블록.
# N = parse_gap_missing_cycles (Time 또는 Symmetry GC_GAP:N=).
# gap_cycles → process_excel 에서 해당 Cycle NaN (Origin 시간축 정렬).
from gc_gap_contract import is_cycle_header_row, parse_gap_missing_cycles


def parse_gc_sheet(df_raw, detector_type, equipment, time_bounds):
    warnings = []
    gap_cycles = set()
    cycle_num, cycle_list, unassigned_list = 1, [], []  # 1주입 = Cycle 1 (KCH 첫 블록에 헤더 없음)

    rows = list(df_raw.iterrows())
    i = 0
    while i < len(rows):
        _index, row = rows[i]

        if is_cycle_header_row(row):
            # Chem32 레이아웃: [헤더 # Time …][중단 행 1줄] — N사이클 건너뛰기
            if i + 1 < len(rows) and parse_gap_missing_cycles(rows[i + 1][1]) is not None:
                missing = parse_gap_missing_cycles(rows[i + 1][1])
                last_cycle = max((c["Cycle"] for c in cycle_list), default=cycle_num - 1)
                start_gap = last_cycle + 1
                end_gap = last_cycle + missing
                for k in range(start_gap, end_gap + 1):
                    gap_cycles.add(k)
                warnings.append(
                    f"⚠️ [분석 공백] Cycle {start_gap}~{end_gap} 미수집 "
                    f"({missing}사이클, GC3 분석 중단 구간)"
                )
                cycle_num = last_cycle + missing
                i += 2
                continue
            cycle_num += 1
            i += 1
            continue

        if parse_gap_missing_cycles(row) is not None:
            i += 1
            continue

        if pd.notna(row.get("Time")) and pd.notna(row.get("Area")):
            try:
                t, a = float(row["Time"]), float(row["Area"])
            except (ValueError, TypeError):
                i += 1
                continue

            gas = None
            for gas_name, (t_min, t_max) in time_bounds.items():
                if t_min <= t <= t_max:
                    gas = f"{gas_name} Area"
                    break

            if gas:
                cycle_list.append({"Cycle": cycle_num, "Gas": gas, "Area": a, "Time": t})
            else:
                unassigned_list.append({"Cycle": cycle_num, "Time": t, "Area": a})
        i += 1

    df_extracted = pd.DataFrame(cycle_list)
    if df_extracted.empty:
        df_pivot = pd.DataFrame()
    else:
        # 🚨 [검증 1] 피크 쪼개짐(Split Peak) 감지
        gas_counts = df_extracted.groupby(['Cycle', 'Gas']).size().reset_index(name='Count')
        split_peaks = gas_counts[gas_counts['Count'] > 1]
        df_pivot = df_extracted.groupby(['Cycle', 'Gas'])['Area'].sum().unstack(fill_value=0)

        for _, sp in split_peaks.iterrows():
            c, g = sp['Cycle'], sp['Gas']
            sum_area = df_pivot.at[c, g]
            adj_area = df_pivot.at[c-1, g] if (c-1) in df_pivot.index and df_pivot.at[c-1, g] > 0 else (df_pivot.at[c+1, g] if (c+1) in df_pivot.index and df_pivot.at[c+1, g] > 0 else None)

            if adj_area:
                if abs(sum_area - adj_area) / adj_area < 0.2:
                    warnings.append(f"⚠️ [피크 보정] Cycle {c}에서 '{g}' 피크가 여러 개로 검출되어 합산 처리되었습니다.")
                else:
                    warnings.append(f"⚠️ [비정상 피크] Cycle {c}에서 '{g}' 피크가 비정상적으로 쪼개졌습니다. 합산 결과가 앞뒤 사이클과 크게 다릅니다!")

    if gap_cycles:
        all_idx = sorted(set(df_pivot.index) | gap_cycles) if not df_pivot.empty else sorted(gap_cycles)
        df_pivot = df_pivot.reindex(all_idx) if not df_pivot.empty else pd.DataFrame(index=all_idx)

    # 🚨 [검증 2] 검출 범위 미세 이탈(Out of Bounds) — 유효 피크 0개여도 unassigned 검사
    for un in unassigned_list:
        if un['Area'] < 10: continue
        for gas_name, (t_min, t_max) in time_bounds.items():
            if (t_min - 0.1 <= un['Time'] < t_min) or (t_max < un['Time'] <= t_max + 0.1):
                warnings.append(f"⚠️ [검출 어긋남] Cycle {un['Cycle']}에서 '{gas_name}' 피크가 설정 범위에서 0.1분 벗어난 위치({un['Time']}분)에서 검출되었습니다!")
                break

    return df_pivot, warnings, gap_cycles

# ==========================================
# 기능 3: 수율/전환율 계산 · 물질수지 이상 감지
# ==========================================
# GC2 곱셈 교정(DRE/DRM), GC3/GC1 나눗셈 교정(DRME / GC1 DRE·DRM).
# GC1: FID+TCD 2시트, H2 RT ~2분 (GC2 ~0.5분, GC3 ~0.7분 과 구분).
def _gc1_calib_ready():
    """GC1 CALIB 미입력 시 계산 중단 — GC2 숫자를 GC1에 쓰는 실수 방지.

    True 조건: GC1_CALIB_READY=True 이고 GC1_CALIB 모든 값이 양수.
    절차: deploy/STEP7_gc1_calib.md, scripts/suggest_gc1_calib.py
    """
    if not GC1_CALIB_READY:
        return False
    for val in GC1_CALIB.values():
        if val is None or val <= 0:
            return False
    return True

def process_excel(input_file):
    xls = pd.ExcelFile(input_file)
    eq = None
    df_gc2_raw = pd.DataFrame()
    df_gc3_tcd, df_gc3_fid = pd.DataFrame(), pd.DataFrame()
    df_gc1_tcd, df_gc1_fid = pd.DataFrame(), pd.DataFrame()

    reaction_target = get_reaction_type_from_filename(input_file)

    # 장비 자동 판별: 시트별 H2 RT 구간으로 GC2 → GC3 → GC1 순 검사.
    # GC2 H2 ~0.5분, GC3 ~0.7분, GC1 ~2.0분 — 구간이 겹치지 않도록 설계됨.
    # GC1 xlsx는 FID+TCD 2시트이므로 루프에서 tcd/fid 각각 채움.
    for sn in xls.sheet_names:
        df = pd.read_excel(xls, sheet_name=sn)
        if df.empty and len(df.columns) == 0:
            continue
        df.columns = df.columns.astype(str).str.strip()
        if 'Time' not in df.columns:
            continue
        times = pd.to_numeric(df['Time'], errors='coerce')
        if ((times >= GC2_TIME['H2'][0]) & (times <= GC2_TIME['H2'][1])).any():
            eq = 'GC2'
            df_gc2_raw = df
            break
        if ((times >= GC3_TIME_TCD['H2'][0]) & (times <= GC3_TIME_TCD['H2'][1])).any():
            eq = 'GC3'
            df_gc3_tcd = df
        elif ((times >= GC1_TIME_TCD['H2'][0]) & (times <= GC1_TIME_TCD['H2'][1])).any():
            eq = 'GC1'
            df_gc1_tcd = df
        elif ((times >= GC3_TIME_FID['CH4'][0]) & (times <= GC3_TIME_FID['C2H6'][1])).any() and not (
            (times >= GC3_TIME_TCD['CO2'][0]) & (times <= GC3_TIME_TCD['CO2'][1])
        ).any():
            df_gc3_fid = df
        elif ((times >= GC1_TIME_FID['CH4'][0]) & (times <= GC1_TIME_FID['C2H4'][1])).any():
            if eq is None:
                eq = 'GC1'
            df_gc1_fid = df

    if not eq:
        return None, None, [], ""
    df_result = pd.DataFrame()
    all_warnings = []
    df_p = pd.DataFrame()

    # 🚨 [교차 검증] 파일명 반응 타입이 최우선 — 장비·파일명 불일치는 경고만
    # GC3: DRE·DRME 모두 정상 조합 (동일 장비·교정, 2026-06-24). DRM 파일명만 경고.
    if eq == 'GC2' and reaction_target == 'DRME':
        all_warnings.append(
            f"⚠️ [교차 검증] 피크는 GC2인데 파일명은 DRME입니다. 파일명 기준으로 DRME 계산합니다."
        )
    elif eq == 'GC3' and reaction_target == 'DRM':
        all_warnings.append(
            f"⚠️ [교차 검증] 피크는 GC3인데 파일명은 DRM입니다. 파일명 기준으로 DRM 계산합니다."
        )
    elif eq == 'GC1' and reaction_target == 'DRME':
        all_warnings.append(
            f"⚠️ [교차 검증] 피크는 GC1인데 파일명은 DRME입니다. 파일명 기준으로 DRME 계산합니다."
        )

    if eq == 'GC1' and not _gc1_calib_ready():
        all_warnings.append(
            "❌ [GC1] CALIB 미설정 — deploy/STEP7_gc1_calib.md Step 7.3 표준가스 실측 후 "
            "GC1_CALIB 입력 및 GC1_CALIB_READY=True 설정 필요"
        )
        return None, None, all_warnings, ""

    # 파일명 농도(%) → 화공 양론 feed ppm (없으면 USER SETTINGS fallback)
    feed_ppm, conc_label, feed_source_desc = resolve_feed_ppm(input_file, reaction_target, equipment=eq)

    # [수식 적용 단계: GC2 (DRE / DRM)]
    if eq == 'GC2':
        df_p, warn, _gap = parse_gc_sheet(df_gc2_raw, None, 'GC2', GC2_TIME)
        all_warnings.extend(warn)
        for g in ['H2 Area', 'CO Area', 'CH4 Area', 'CO2 Area', 'C2H4 Area', 'C2H6 Area']:
            if g not in df_p.columns: df_p[g] = 0
            
        df_result['H2 ppm'] = df_p['H2 Area'] * GC2_CALIB['H2']
        df_result['CO ppm'] = df_p['CO Area'] * GC2_CALIB['CO']
        df_result['CO2 ppm'] = df_p['CO2 Area'] * GC2_CALIB['CO2']
        df_result['C2H6 ppm'] = df_p['C2H6 Area'] * GC2_CALIB['C2H6']
        df_result['CH4 ppm'] = df_p['CH4 Area'] * GC2_CALIB['CH4']
        df_result['C2H4 ppm'] = df_p['C2H4 Area'] * GC2_CALIB['C2H4']

        if reaction_target == 'DRM':
            df_result['CH4 Conversion (%)'] = ((feed_ppm['CH4'] - df_result['CH4 ppm']) / feed_ppm['CH4']) * 100
            df_result['CO2 Conversion (%)'] = ((feed_ppm['CO2'] - df_result['CO2 ppm']) / feed_ppm['CO2']) * 100
            
            df_result['H2 Yield (%)'] = (df_result['H2 ppm'] / feed_ppm['H2_yield_base']) * 100
            df_result['CO Yield (%)'] = (df_result['CO ppm'] / feed_ppm['CO_yield_base']) * 100
            
            df_result['C2H6 (%)'] = df_result['C2H6 ppm'] / 10000
            df_result['C2H4 (%)'] = df_result['C2H4 ppm'] / 10000
            
            cols = ['H2 Area', 'CO Area', 'CO2 Area', 'CH4 Area', 'C2H4 Area', 'C2H6 Area',
                    'CH4 Conversion (%)', 'CO2 Conversion (%)', 'H2 Yield (%)', 'CO Yield (%)', 'C2H6 (%)', 'C2H4 (%)']
            out_name = _calc_output_path(input_file, '_GC2_DRM_계산완료')
        else:
            df_result['C2H6 Conversion (%)'] = ((feed_ppm['C2H6'] - df_result['C2H6 ppm']) / feed_ppm['C2H6']) * 100
            df_result['CO2 Conversion (%)'] = ((feed_ppm['CO2'] - df_result['CO2 ppm']) / feed_ppm['CO2']) * 100
            
            df_result['H2 Yield (%)'] = (df_result['H2 ppm'] / feed_ppm['H2_yield_base']) * 100
            df_result['CO Yield (%)'] = (df_result['CO ppm'] / feed_ppm['CO_yield_base']) * 100
            
            df_result['CH4 (%)'] = df_result['CH4 ppm'] / 10000
            df_result['C2H4 (%)'] = df_result['C2H4 ppm'] / 10000
            
            cols = ['H2 Area', 'CO Area', 'CH4 Area', 'CO2 Area', 'C2H4 Area', 'C2H6 Area',
                    'C2H6 Conversion (%)', 'CO2 Conversion (%)', 'H2 Yield (%)', 'CO Yield (%)', 'CH4 (%)', 'C2H4 (%)']
            out_name = _calc_output_path(input_file, '_GC2_DRE_계산완료')

    # [수식 적용 단계: GC3 (DRE / DRME)] — reaction_target 으로 출력 접미사만 구분
    elif eq == 'GC3':
        df_t, warn_t, gap_t = parse_gc_sheet(df_gc3_tcd, 'TCD', 'GC3', GC3_TIME_TCD)
        df_f, warn_f, gap_f = parse_gc_sheet(df_gc3_fid, 'FID', 'GC3', GC3_TIME_FID)
        gap_cycles = gap_t | gap_f
        all_warnings.extend(warn_t); all_warnings.extend(warn_f)
        df_p = pd.concat([df_t, df_f], axis=1).fillna(0)
        
        for g in ['H2 Area', 'CO Area', 'CH4 Area', 'CO2 Area', 'C2H4 Area', 'C2H6 Area']:
            if g not in df_p.columns: df_p[g] = 0
            
        df_result['H2 ppm'] = df_p['H2 Area'] / GC3_CALIB['H2']
        df_result['CO ppm'] = df_p['CO Area'] / GC3_CALIB['CO']
        df_result['CO2 ppm'] = df_p['CO2 Area'] / GC3_CALIB['CO2']
        df_result['C2H6 ppm'] = df_p['C2H6 Area'] / GC3_CALIB['C2H6']
        df_result['CH4 (%)'] = (df_p['CH4 Area'] / GC3_CALIB['CH4']) / 10000
        df_result['C2H4 (%)'] = (df_p['C2H4 Area'] / GC3_CALIB['C2H4']) / 10000
        
        df_result['C2H6 Conversion (%)'] = ((feed_ppm['C2H6'] - df_result['C2H6 ppm']) / feed_ppm['C2H6']) * 100
        df_result['CO2 Conversion (%)'] = ((feed_ppm['CO2'] - df_result['CO2 ppm']) / feed_ppm['CO2']) * 100
        df_result['H2 Yield (%)'] = (df_result['H2 ppm'] / feed_ppm['H2_yield_base']) * 100
        df_result['CO Yield (%)'] = (df_result['CO ppm'] / feed_ppm['CO_yield_base']) * 100
        
        cols = ['H2 Area', 'CO Area', 'CO2 Area', 'CH4 Area', 'C2H4 Area', 'C2H6 Area',
                'C2H6 Conversion (%)', 'CO2 Conversion (%)', 'H2 Yield (%)', 'CO Yield (%)', 'CH4 (%)', 'C2H4 (%)']
        gc3_suffix = '_GC3_DRE_계산완료' if reaction_target == 'DRE' else '_GC3_DRME_계산완료'
        out_name = _calc_output_path(input_file, gc3_suffix)
        if gap_cycles:
            for cyc in gap_cycles:
                if cyc in df_p.index:
                    df_p.loc[cyc] = np.nan
                if cyc in df_result.index:
                    df_result.loc[cyc] = np.nan

    # [수식 적용 단계: GC1 (DRE / DRM) — GC3 와 동일 나눗셈 교정, FID+TCD 병합]
    elif eq == 'GC1':
        df_t, warn_t, _gap_t = parse_gc_sheet(df_gc1_tcd, 'TCD', 'GC1', GC1_TIME_TCD)
        df_f, warn_f, _gap_f = parse_gc_sheet(df_gc1_fid, 'FID', 'GC1', GC1_TIME_FID)
        all_warnings.extend(warn_t)
        all_warnings.extend(warn_f)
        df_p = pd.concat([df_t, df_f], axis=1).fillna(0)

        for g in ['H2 Area', 'CO Area', 'CH4 Area', 'CO2 Area', 'C2H4 Area', 'C2H6 Area']:
            if g not in df_p.columns:
                df_p[g] = 0

        df_result['H2 ppm'] = df_p['H2 Area'] / GC1_CALIB['H2']
        df_result['CO ppm'] = df_p['CO Area'] / GC1_CALIB['CO']
        df_result['CO2 ppm'] = df_p['CO2 Area'] / GC1_CALIB['CO2']
        df_result['C2H6 ppm'] = df_p['C2H6 Area'] / GC1_CALIB['C2H6']
        df_result['CH4 ppm'] = df_p['CH4 Area'] / GC1_CALIB['CH4']
        df_result['C2H4 ppm'] = df_p['C2H4 Area'] / GC1_CALIB['C2H4']

        if reaction_target == 'DRM':
            df_result['CH4 Conversion (%)'] = ((feed_ppm['CH4'] - df_result['CH4 ppm']) / feed_ppm['CH4']) * 100
            df_result['CO2 Conversion (%)'] = ((feed_ppm['CO2'] - df_result['CO2 ppm']) / feed_ppm['CO2']) * 100
            df_result['H2 Yield (%)'] = (df_result['H2 ppm'] / feed_ppm['H2_yield_base']) * 100
            df_result['CO Yield (%)'] = (df_result['CO ppm'] / feed_ppm['CO_yield_base']) * 100
            df_result['C2H6 (%)'] = df_result['C2H6 ppm'] / 10000
            df_result['C2H4 (%)'] = df_result['C2H4 ppm'] / 10000
            cols = ['H2 Area', 'CO Area', 'CO2 Area', 'CH4 Area', 'C2H4 Area', 'C2H6 Area',
                    'CH4 Conversion (%)', 'CO2 Conversion (%)', 'H2 Yield (%)', 'CO Yield (%)', 'C2H6 (%)', 'C2H4 (%)']
            out_name = _calc_output_path(input_file, '_GC1_DRM_계산완료')
        else:
            df_result['C2H6 Conversion (%)'] = ((feed_ppm['C2H6'] - df_result['C2H6 ppm']) / feed_ppm['C2H6']) * 100
            df_result['CO2 Conversion (%)'] = ((feed_ppm['CO2'] - df_result['CO2 ppm']) / feed_ppm['CO2']) * 100
            df_result['H2 Yield (%)'] = (df_result['H2 ppm'] / feed_ppm['H2_yield_base']) * 100
            df_result['CO Yield (%)'] = (df_result['CO ppm'] / feed_ppm['CO_yield_base']) * 100
            df_result['CH4 (%)'] = df_result['CH4 ppm'] / 10000
            df_result['C2H4 (%)'] = df_result['C2H4 ppm'] / 10000
            cols = ['H2 Area', 'CO Area', 'CH4 Area', 'CO2 Area', 'C2H4 Area', 'C2H6 Area',
                    'C2H6 Conversion (%)', 'CO2 Conversion (%)', 'H2 Yield (%)', 'CO Yield (%)', 'CH4 (%)', 'C2H4 (%)']
            out_name = _calc_output_path(input_file, '_GC1_DRE_계산완료')

    # 🚨 [검증 3] 수율/전환율 교차검증 — feed 농도(%) 오기재 패턴 감지
    all_warnings.extend(_validate_yield_conversion(df_result, reaction_target, feed_source_desc))

    if conc_label is None:
        all_warnings.append(
            f"⚠️ [feed 농도] 파일명에 농도(%)가 없어 USER SETTINGS 기본값으로 계산했습니다. "
            f"실제 투여 농도와 다르면 전환율/수율이 틀어집니다."
        )

    df_final = pd.concat([df_p, df_result], axis=1)[cols]
    df_final.to_excel(out_name, index=True)
    return df_final, out_name, all_warnings, feed_source_desc

# ==========================================
# 기능 4: Origin .opju 워크시트 연동 (originpro) — 그래프 plot 은 수동
# ==========================================
def _comment_matches_identity(comment, identity_key):
    """Origin Comments(기존 열)와 KCH identity (날짜·시료) 동일 실험 여부."""
    if not comment or not identity_key:
        return False
    date, sample = identity_key
    text = comment.strip().lower()
    if not text.startswith(date):
        return False
    tokens = _identity_match_tokens(sample)
    if not tokens:
        return False
    matched = sum(1 for token in tokens if token in text)
    return matched >= max(2, int(len(tokens) * 0.6))

def _comment_sort_date(text):
    """Origin Comments / 시료명 선두 YYYYMMDD — 열 날짜순 정렬용."""
    match = re.match(r"^(\d{8})", (text or "").strip())
    return match.group(1) if match else None

def _worksheet_dated_columns(wks):
    """(col_idx, sort_date) — Comments 에 날짜가 있는 열만, 왼쪽→오른쪽."""
    dated = []
    for i in range(1, wks.cols):
        sort_date = _comment_sort_date(wks.get_label(i, "C") or "")
        if sort_date:
            dated.append((i, sort_date))
    return dated

def _insert_worksheet_column_before(wks, col_idx):
    """0-based col_idx 앞에 빈 Y 열 1개 삽입 (기존 열 오른쪽으로 밀림)."""
    from originpro.config import po
    lt_col = col_idx + 1
    rng = wks.lt_range()
    po.LT_execute(f"page.xlcolname=0; {rng}.col={lt_col}; {rng}.insert(GCData);")

def _find_worksheet_column_for_sample(wks, sample_name, identity_key=None):
    """
    시료 데이터를 넣을 워크시트 열.
    · 동일 Comments → 해당 열 갱신
    · identity_key 일치(재전송) → 해당 열 갱신
    · 없으면 Comments 날짜(YYYYMMDD)순으로 삽입 — 맨 끝 무조건 추가 금지
    """
    for i in range(1, wks.cols):
        comment = wks.get_label(i, "C")
        if comment and comment.strip() == sample_name:
            return i
    if identity_key:
        for i in range(1, wks.cols):
            comment = wks.get_label(i, "C") or ""
            if _comment_matches_identity(comment, identity_key):
                return i

    new_date = _comment_sort_date(sample_name)
    dated_cols = _worksheet_dated_columns(wks)
    if not new_date:
        return dated_cols[-1][0] + 1 if dated_cols else 1

    insert_at = None
    for col_idx, sort_date in dated_cols:
        if new_date < sort_date:
            insert_at = col_idx
            break
    if insert_at is None:
        insert_at = dated_cols[-1][0] + 1 if dated_cols else 1

    if insert_at < wks.cols and (wks.get_label(insert_at, "C") or "").strip():
        _insert_worksheet_column_before(wks, insert_at)
    return insert_at

def update_origin(opju_path, df_data, sample_name, save_in_place=True, identity_key=None):
    """
    [4단계] Origin .opju 워크시트에 계산 데이터 열 추가 (그래프 plot 은 사용자가 수동).

    · sample_name 은 generate_sample_name() 결과만 사용 (폴더명과 혼용 금지)
    · Comments 형식: 날짜 반응(농도)@온도°C 촉매 — 촉매 무게 없음 (DRE/DRME/DRM 공통)
    · ORIGIN_MAPPING 으로 엑셀 열 → Origin 워크시트 키워드 매칭
    · Comments 행에 sample_name 기록 (from_list comments= 인자)
    · save_in_place=True: G: 아카이브 시 같은 .opju 에 덮어쓰기

    Origin 동시 열기 방지:
      · _origin_acquire_lock() 으로 4단계 전체 직렬화
      · Read-Only 확인창은 watcher 가 Yes 자동 클릭 (수동 개입 불필요)
      · finally 에서 op.exit() + 락 해제
    """
    print(f"\n[4단계] Origin 워크시트 — Comments: '{sample_name}'")
    op = _get_originpro()
    _origin_acquire_lock()
    try:
        _open_opju_for_update(op, opju_path)
        updated_count = 0
        n_rows = len(df_data)

        for df_col, origin_keyword in ORIGIN_MAPPING.items():
            if df_col not in df_data.columns:
                continue

            target_wks = None
            for book in op.pages('w'):
                for wks in book:
                    search_str = f"{book.name} {wks.name} {book.lname}"
                    if _normalize_origin_key(origin_keyword) in _normalize_origin_key(search_str):
                        target_wks = wks
                        break
                if target_wks:
                    break

            if not target_wks:
                continue

            col_idx = _find_worksheet_column_for_sample(target_wks, sample_name, identity_key)
            target_wks.from_list(col_idx, df_data[df_col].tolist(), comments=sample_name)
            updated_count += 1

        if updated_count > 0:
            print(f"  → 워크시트 {updated_count}개 · {n_rows}행 반영")
            stop = threading.Event()
            watcher = threading.Thread(
                target=_origin_dialog_watcher,
                args=(stop,),
                name="origin-readonly-watcher-save",
                daemon=True,
            )
            watcher.start()
            try:
                if save_in_place:
                    op.save(opju_path)
                    print(f" ✅ Origin 저장 완료: {opju_path}")
                else:
                    new_opju = opju_path.replace('.opju', '_Updated.opju')
                    op.save(new_opju)
                    print(f" ✅ Origin 파일 업데이트 완료! 저장 위치: {new_opju}")
            finally:
                stop.set()
                watcher.join(timeout=3)
        else:
            print(" ⚠️ Origin에서 일치하는 데이터 시트를 하나도 찾지 못했습니다.")
    finally:
        _origin_exit_quiet(op)
        _origin_release_lock()

# ==========================================
# 기능 5: 네이버 IMAP 메일 수신 (gc_automation.env 계정)
# ==========================================
def _get_mail_credentials():
    if not _load_dotenv_files():
        print("[오류] python-dotenv 미설치: pip install python-dotenv")
        return None, None
    addr = os.getenv("NAVER_EMAIL", "").strip()
    password = os.getenv("NAVER_APP_PASSWORD", "").strip()
    return addr, password

def _decode_mime_header(value):
    if not value: return ""
    parts = []
    for chunk, charset in decode_header(value):
        if isinstance(chunk, bytes): parts.append(chunk.decode(charset or "utf-8", errors="replace"))
        else: parts.append(str(chunk))
    return "".join(parts)

def _parse_mail_date(msg):
    try:
        return parsedate_to_datetime(msg.get("Date"))
    except (TypeError, ValueError, IndexError):
        return datetime.min.replace(tzinfo=None)

def _unique_save_path(directory, filename):
    os.makedirs(directory, exist_ok=True)
    safe_name = os.path.basename(filename.replace("\\", "_").replace("/", "_"))
    dest = os.path.join(directory, safe_name)
    if not os.path.exists(dest):
        return dest
    base, ext = os.path.splitext(safe_name)
    return os.path.join(directory, f"{base}_{int(time.time())}{ext}")

def _save_attachment_bytes(save_dir, filename, payload):
    """중복 시료는 최신 파일로 덮어쓰기 — 타임스탬프 접미사 없이 정규 파일명 저장."""
    os.makedirs(save_dir, exist_ok=True)
    safe_name = os.path.basename(filename.replace("\\", "_").replace("/", "_"))
    base, ext = os.path.splitext(safe_name)
    clean_base = _strip_mail_dedup_suffix(base)
    dest = os.path.join(save_dir, f"{clean_base}{ext}")
    with open(dest, "wb") as f:
        f.write(payload)
    return dest

def _extract_attachments_from_message(msg):
    attachments = []
    for part in msg.walk():
        if part.get_content_disposition() != "attachment":
            continue
        filename = _decode_mime_header(part.get_filename())
        if not filename or not filename.lower().endswith((".xlsx", ".xls")):
            continue
        payload = part.get_payload(decode=True)
        if not payload:
            continue
        attachments.append((filename, payload))
    return attachments

def _save_attachments_from_message(msg, save_dir):
    saved = []
    for filename, payload in _extract_attachments_from_message(msg):
        dest = _save_attachment_bytes(save_dir, filename, payload)
        saved.append(dest)
    return saved

def _cleanup_inbox_duplicate_files(keep_path, identity_key):
    """inbox 에 남은 같은 시료·날짜 중복 xlsx 정리."""
    keep_name = os.path.basename(keep_path)
    for fname in os.listdir(DATA_PC_INBOX_DIR):
        if fname == keep_name or fname.startswith("."):
            continue
        if not fname.lower().endswith((".xlsx", ".xls")):
            continue
        if _experiment_identity_key(fname) == identity_key:
            try:
                os.remove(os.path.join(DATA_PC_INBOX_DIR, fname))
                print(f"       → inbox 중복 파일 삭제: {fname}")
            except OSError:
                pass

def _is_gc_mail_subject(subject):
    text = subject or ""
    return EMAIL_SUBJECT_KEYWORD in text or ("GC" in text and "분석" in text and "결과" in text)

def _is_kch_gc_sample_name(text):
    """KCH/GC 원본 파일명·제목 — YYYYMMDD + DRM|DRE|DRME (내게쓴메일함 수동 발송)."""
    if not text:
        return False
    name = _strip_mail_dedup_suffix(os.path.splitext(str(text).strip())[0])
    if not re.match(r"^\d{8}\s+", name):
        return False
    return bool(re.search(r"\b(DRE|DRM|DRME)\b", name, re.I))

def _mail_qualifies_for_gc(subject, attachments, mail_source):
    if _is_gc_mail_subject(subject):
        return True
    if mail_source != "self":
        return False
    if _is_kch_gc_sample_name(subject):
        return True
    return any(_is_kch_gc_sample_name(fn) for fn, _ in attachments)

def _attachments_for_gc_workflow(subject, attachments, mail_source):
    if mail_source != "self" or _is_gc_mail_subject(subject):
        return attachments
    named = [(f, p) for f, p in attachments if _is_kch_gc_sample_name(f)]
    if named:
        return named
    if _is_kch_gc_sample_name(subject):
        return attachments
    return []

def _load_processed_mail_ids():
    if not os.path.isfile(PROCESSED_MAIL_LOG): return set()
    with open(PROCESSED_MAIL_LOG, encoding="utf-8") as f:
        return {line.strip() for line in f if line.strip()}

def _append_processed_mail_id(mail_key):
    os.makedirs(DATA_PC_INBOX_DIR, exist_ok=True)
    with open(PROCESSED_MAIL_LOG, "a", encoding="utf-8") as f: f.write(mail_key + "\n")

def _mail_unique_key(msg, msg_id):
    message_id = (msg.get("Message-ID") or "").strip()
    if message_id: return message_id
    uid = msg_id.decode() if isinstance(msg_id, bytes) else str(msg_id)
    return f"uid:{uid}"

def _fetch_message_peek(mail, msg_id):
    status, fetched = mail.fetch(msg_id, "(BODY.PEEK[])")
    if status != "OK" or not fetched: return None
    for part in fetched:
        if isinstance(part, tuple) and len(part) >= 2 and part[1]:
            return email.message_from_bytes(part[1])
    return None

def _parse_imap_list_entry(raw):
    """IMAP LIST 한 줄 → (flags, mailbox_name)."""
    line = raw.decode("utf-8", errors="replace") if isinstance(raw, bytes) else raw
    match = re.match(r"\(([^)]*)\)\s+\"[^\"]*\"\s+(.*)", line)
    if not match:
        return None
    flags = match.group(1).split()
    name_part = match.group(2).strip()
    if name_part.startswith('"') and name_part.endswith('"'):
        mailbox = name_part[1:-1].replace('\\"', '"')
    else:
        mailbox = name_part
    return flags, mailbox

def _decode_imap_mailbox_name(name):
    """IMAP modified UTF-7 → Unicode (네이버 한글 메일함명)."""
    if not name or "&" not in name:
        return name
    out, i = [], 0
    while i < len(name):
        if name[i] != "&":
            out.append(name[i])
            i += 1
            continue
        j = name.find("-", i)
        if j < 0:
            out.append(name[i:])
            break
        chunk = name[i + 1 : j]
        if chunk == "":
            out.append("&")
        else:
            pad = (-len(chunk)) % 4
            b64 = chunk.replace(",", "/").encode("ascii") + b"=" * pad
            try:
                out.append(base64.b64decode(b64).decode("utf-16-be"))
            except (ValueError, UnicodeDecodeError):
                out.append(name[i : j + 1])
        i = j + 1
    return "".join(out)

def _iter_imap_mailboxes(mail):
    status, data = mail.list()
    if status != "OK" or not data:
        return
    for raw in data:
        if not raw:
            continue
        parsed = _parse_imap_list_entry(raw)
        if parsed:
            yield parsed

def _find_sent_mailbox(mail):
    """네이버 보낸메일함 — \\Sent 속성 또는 이름(보낸/Sent)으로 탐색."""
    fallback = None
    for flags, mailbox in _iter_imap_mailboxes(mail):
        flags_lower = " ".join(flags).lower()
        mailbox_lower = mailbox.lower()
        decoded = _decode_imap_mailbox_name(mailbox)
        if "\\sent" in flags_lower:
            return mailbox
        if "보낸" in decoded or mailbox_lower in ("sent", "sent messages"):
            fallback = mailbox
    return fallback

def _find_self_mailbox(mail):
    """네이버 내게쓴메일함 — 디코딩된 이름에 '내게쓴' 포함."""
    for _, mailbox in _iter_imap_mailboxes(mail):
        if "내게쓴" in _decode_imap_mailbox_name(mailbox):
            return mailbox
    return None

def _folder_mail_source(folder):
    if folder.upper() == "INBOX":
        return "inbox"
    if "내게쓴" in _decode_imap_mailbox_name(folder):
        return "self"
    return "sent"

_MAIL_SOURCE_LABELS = {"inbox": "받은", "sent": "보낸", "self": "내게쓴"}

def _imap_quote_mailbox(folder):
    """IMAP SELECT용 mailbox 이름 — 공백·특수문자 포함 시 RFC 3501 quoted string."""
    if not folder:
        return folder
    if folder.startswith('"') and folder.endswith('"'):
        return folder
    if folder.upper() == "INBOX":
        return folder
    if re.search(r"[^\w&\-./]", folder):
        escaped = folder.replace("\\", "\\\\").replace('"', '\\"')
        return f'"{escaped}"'
    return folder

def _imap_select_folder(mail, folder):
    try:
        status, _ = mail.select(_imap_quote_mailbox(folder))
        return status == "OK"
    except imaplib.IMAP4.error:
        return False

def _list_recent_mail_ids(mail, days=30, unseen_only=False):
    if days is None:
        query = "UNSEEN" if unseen_only else "ALL"
    else:
        since = (datetime.now() - timedelta(days=days)).strftime("%d-%b-%Y")
        query = f"(UNSEEN SINCE {since})" if unseen_only else f"(SINCE {since})"
    status, data = mail.search(None, query)
    if status != "OK" or not data[0]:
        return []
    return data[0].split()

def _format_mail_datetime(dt):
    if dt.tzinfo is not None:
        dt = dt.replace(tzinfo=None)
    if dt == datetime.min.replace(tzinfo=None):
        return "시간 미상"
    return dt.strftime("%Y-%m-%d %H:%M")

def _collect_pending_gc_mails(mail, msg_ids, done_keys, folder):
    """미처리 GC 메일 수집. msg_ids 순서(보통 오래된→최신) 유지."""
    source = _folder_mail_source(folder)
    pending = []
    for msg_id in msg_ids:
        msg = _fetch_message_peek(mail, msg_id)
        if msg is None:
            continue
        subject = _decode_mime_header(msg.get("Subject", ""))
        attachments = _extract_attachments_from_message(msg)
        if not _mail_qualifies_for_gc(subject, attachments, source):
            continue
        attachments = _attachments_for_gc_workflow(subject, attachments, source)
        if not attachments:
            continue
        mail_key = _mail_unique_key(msg, msg_id)
        if mail_key in done_keys:
            continue
        pending.append({
            "msg_id": msg_id,
            "mail_key": mail_key,
            "subject": subject,
            "attachments": attachments,
            "folder": folder,
            "source": source,
            "date": _parse_mail_date(msg),
        })
    return pending

def _gather_pending_from_folder(mail, folder, done_keys, days=30, unseen_only=False):
    if not _imap_select_folder(mail, folder):
        print(f"       [경고] 메일함 접근 실패: {folder}")
        return []
    msg_ids = _list_recent_mail_ids(mail, days, unseen_only)
    if not msg_ids:
        return []
    return _collect_pending_gc_mails(mail, msg_ids, done_keys, folder)

def _merge_pending_by_date(*pending_lists):
    """여러 메일함 병합 — Message-ID 중복 제거, 수신/발송 시각 오래된 순."""
    merged = {}
    for pending in pending_lists:
        for item in pending:
            merged.setdefault(item["mail_key"], item)
    return sorted(merged.values(), key=lambda x: x["date"])

def _mark_mail_seen_and_logged(mail, item, done_keys):
    if item["mail_key"] in done_keys:
        return False
    if not _imap_select_folder(mail, item["folder"]):
        return False
    try:
        mail.store(item["msg_id"], "+FLAGS", "\\Seen")
        _append_processed_mail_id(item["mail_key"])
        done_keys.add(item["mail_key"])
        return True
    except imaplib.IMAP4.error:
        return False

def process_new_gc_emails(opju_path=None, auto_archive=True):
    """
    [1단계] 네이버 IMAP — KCH 원본 엑셀 수신 (받은·보낸·내게쓴 메일함).

    · 받은메일함(INBOX): gc_automation 봇 발송·수신 메일 — 미처리 건 전부
    · 보낸메일함: 미읽음 GC 결과 메일 (제목에 GC 분석 결과)
    · 내게쓴메일함: 미읽음 — 제목/첨부가 YYYYMMDD + DRM|DRE|DRME 형식이면 처리
    · 오래된 메일부터 최신 순으로 전건 2~4단계 반영 (같은 시료 재전송은 마지막이 Origin 최종값)
    · BODY.PEEK + .processed_mail_ids.txt 로 중복 처리 방지
    · G: 불가 시 2단계까지 완료, 3~4단계 실패 → 메일 미처리(재시도 가능)
    """
    email_addr, app_password = _get_mail_credentials()
    if not email_addr or not app_password:
        print("\n[오류] 메일 계정 설정 없음 — 바탕화면 gc_automation.env 확인")
        print("       NAVER_EMAIL, NAVER_APP_PASSWORD 필요")
        return PipelineRunResult(0)

    os.makedirs(DATA_PC_INBOX_DIR, exist_ok=True)
    print(f"\n[1단계] 네이버 메일 접속 — 받은·보낸·내게쓴 ({email_addr})")

    mail = imaplib.IMAP4_SSL(NAVER_IMAP_HOST, NAVER_IMAP_PORT)
    workflow_count = 0
    read_count = 0
    done_keys = _load_processed_mail_ids()
    try:
        mail.login(email_addr, app_password)

        inbox_pending = _gather_pending_from_folder(
            mail, "INBOX", done_keys, unseen_only=False
        )
        sent_mb = _find_sent_mailbox(mail)
        sent_pending = []
        if sent_mb:
            sent_pending = _gather_pending_from_folder(
                mail, sent_mb, done_keys, unseen_only=True
            )
        else:
            print("       [경고] 보낸메일함을 찾지 못했습니다 — 받은메일함만 확인합니다.")

        self_mb = _find_self_mailbox(mail)
        self_pending = []
        if self_mb:
            self_pending = _gather_pending_from_folder(
                mail, self_mb, done_keys, days=None, unseen_only=True
            )
        else:
            print("       [경고] 내게쓴메일함을 찾지 못했습니다.")

        if inbox_pending or sent_pending or self_pending:
            print(
                f"       → 받은메일함 {len(inbox_pending)}건 · "
                f"보낸메일함(미읽음) {len(sent_pending)}건 · "
                f"내게쓴메일함(미읽음) {len(self_pending)}건"
            )

        pending_all = _merge_pending_by_date(
            inbox_pending, sent_pending, self_pending
        )
        if not pending_all:
            print("\n       → 처리할 gc_automation 메일이 없습니다. (이미 처리됨 또는 미수신)")
            return PipelineRunResult(0)

        print(f"       → 처리 순서: 오래된 메일부터 {len(pending_all)}건")

        gdrive_retry_needed = False
        for item in pending_all:
            source_label = _MAIL_SOURCE_LABELS.get(item["source"], item["source"])
            print(f"\n       → 반영: {item['subject']}")
            print(
                f"       → 출처: {source_label}메일함 · "
                f"{_format_mail_datetime(item['date'])}"
            )

            mail_ok = True
            for filename, payload in item["attachments"]:
                print(f"       → KCH 원본 저장: {filename}")
                identity = _experiment_identity_key(filename)
                excel_path = _save_attachment_bytes(
                    DATA_PC_INBOX_DIR, filename, payload
                )
                _cleanup_inbox_duplicate_files(excel_path, identity)

                if run_workflow_for_file(
                    excel_path,
                    opju_path=opju_path,
                    auto_archive=auto_archive and opju_path is None,
                ):
                    workflow_count += 1
                else:
                    mail_ok = False
                    if auto_archive and opju_path is None and not _is_g_drive_available():
                        gdrive_retry_needed = True
                    print("       [경고] 워크플로 실패 — 같은 시료 메일은 재시도 가능")

            if mail_ok and _mark_mail_seen_and_logged(mail, item, done_keys):
                read_count += 1

        if workflow_count == 0 and read_count == 0:
            print("\n       → 처리할 gc_automation 메일이 없습니다. (이미 처리됨 또는 미수신)")
        elif workflow_count:
            print(f"\n[1단계 완료] {read_count}건 메일 읽음 · {workflow_count}건 시료 반영")
        else:
            print(f"\n[1단계 완료] {read_count}건 메일 읽음 · 반영 실패로 G: 재시도 필요")

        if gdrive_retry_needed:
            print(
                "       [G: 잠금] 3~4단계 보류 — watch 가 "
                f"{int(os.getenv('DATA_PC_GDRIVE_RETRY_SEC', '900')) // 60}분마다 재시도 "
                "(1시간 쿨다운 미적용, 미처리 메일 유지)"
            )

    except imaplib.IMAP4.error as exc:
        print(f"[오류] IMAP 인증/접속 실패: {exc}")
        return PipelineRunResult(0)
    finally:
        try:
            mail.logout()
        except Exception:
            pass

    return PipelineRunResult(workflow_count, gdrive_retry_needed)

def run_workflow_for_file(excel_path, opju_path=None, auto_archive=True):
    """
    단일 KCH 원본 엑셀에 대한 2→3→4 단계 오케스트레이션.

    opju_path 지정 시: G: 폴더 생성 없이 해당 .opju 만 _Updated.opju 로 저장 (--opju).
    auto_archive=False: 2단계 계산만 (--no-archive).
    G: 없으면 GDriveUnavailableError → 안내 출력, saved_excel 경로는 DATA_PC/processed.
    """
    if not os.path.exists(excel_path) or not excel_path.lower().endswith((".xlsx", ".xls")):
        print("❌ 올바른 엑셀 파일이 아닙니다.")
        return False

    saved_excel = None
    try:
        print(f"\n[2단계] KCH 원본 계산 중: {os.path.basename(excel_path)}")
        df_final, saved_excel, warnings, feed_source_desc = process_excel(excel_path)
        if df_final is None:
            print("❌ 장비를 판별할 수 없습니다. (수소 피크 유무 확인)")
            return False

        sample_name = generate_sample_name(excel_path)
        experiment_base = generate_experiment_basename(excel_path)
        reaction_type = reaction_type_from_output_file(saved_excel)
        identity_key = _experiment_identity_key(excel_path)
        print(f" ✅ 엑셀 계산 완료: {os.path.basename(saved_excel)}")
        if os.path.normpath(os.path.dirname(saved_excel)) == os.path.normpath(DATA_PC_PROCESSED_DIR):
            print(f"    검토용 사본: {_DATA_PC_WORK}\\processed\\")
        print(f" 📊 Feed ppm 기준: {feed_source_desc}")
        print(f" 🏷️ Origin 시료명: {sample_name}")
        print(f" 📁 실험 폴더명: {experiment_base} ({reaction_type})")

        if warnings:
            print("\n" + "!" * 65)
            print(" 🚨 [장비/데이터 상태 점검] 엑셀 처리 중 특이사항이 감지되었습니다!")
            for w in warnings: print(f"   - {w}")
            print("!" * 65)

        if opju_path:
            if opju_path.upper().startswith("G:"):
                _require_g_drive_access()
            if not os.path.exists(opju_path) or not opju_path.lower().endswith(".opju"):
                if opju_path.upper().startswith("G:") and not _is_g_drive_available():
                    print(_g_drive_unavailable_message())
                    print(f"    (계산 파일: {saved_excel})")
                    return False
                print("❌ 올바른 Origin 파일(.opju)이 아닙니다.")
                return False
            update_origin(opju_path, df_final, sample_name, save_in_place=False, identity_key=identity_key)
            return True

        if not auto_archive:
            print("\n[3~4단계] --no-archive: G: 폴더 생성 및 Origin 연동을 건너뜁니다.")
            return True

        _, target_opju, archive_xlsx = setup_experiment_folder(
            excel_path, saved_excel, reaction_type
        )
        update_origin(target_opju, df_final, sample_name, save_in_place=True, identity_key=identity_key)
        print(f"\n ✅ 전체 완료 — G: 실험 폴더 및 Origin 반영")
        print(f"    {archive_xlsx}")
        return True

    except GDriveUnavailableError:
        print(_g_drive_unavailable_message())
        if saved_excel:
            print(f"    (계산 파일: {saved_excel})")
        return False
    except FileNotFoundError as e:
        if not _is_g_drive_available():
            print(_g_drive_unavailable_message())
            if saved_excel:
                print(f"    (계산 파일: {saved_excel})")
        else:
            print(f"❌ 경로 오류: {e}")
        return False
    except OSError as e:
        if auto_archive and not _is_g_drive_available():
            print(_g_drive_unavailable_message())
            if saved_excel:
                print(f"    (계산 파일: {saved_excel})")
        else:
            print(f"❌ 파일 시스템 오류: {e}")
        return False
    except FileExistsError as e:
        print(f"❌ {e}")
        return False
    except Exception as e:
        print(f"❌ 분석 중 치명적 에러가 발생했습니다: {e}")
        try:
            if _originpro is not None:
                _originpro.exit()
        except Exception:
            pass
        return False

# ==========================================
# 🚀 메인 실행부 (Workflow Controller)
# ==========================================
def build_cli_parser() -> argparse.ArgumentParser:
    """CLI 인자 파서 — unittest(T81) 및 ``__main__`` 공용."""
    parser = argparse.ArgumentParser(
        description="GC KCH 원본(메일) → 수율/전환율 계산 → Origin",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
기본 흐름 (메일 → 계산 → G: 실험 폴더 → Origin):
  python "촉매 반응 계산.py"

수동 opju 지정 (G: 폴더 생성 없이 _Updated.opju 저장):
  python "촉매 반응 계산.py" --opju "G:\\...\\파일.opju"

계산만 (G: / Origin 건너뛰기):
  python "촉매 반응 계산.py" --no-archive

엑셀 직접 지정:
  python "촉매 반응 계산.py" --manual
        """,
    )
    parser.add_argument("--manual", action="store_true", help="1단계 메일 건너뛰고 엑셀 파일을 직접 지정")
    parser.add_argument("--opju", default=None, help="Origin .opju 직접 지정 (G: 자동 아카이브 비활성)")
    parser.add_argument("--no-archive", action="store_true", help="G: 실험 폴더 생성 및 Origin 연동 건너뛰기")
    parser.add_argument("--poll-once", action="store_true", help="메일 1회 확인 후 종료 (비대화형)")
    parser.add_argument(
        "--watch",
        action="store_true",
        help="Wi-Fi 감시 — 연결 유지 중 1시간 쿨다운으로 자동 파이프라인",
    )
    parser.add_argument(
        "--no-wifi-check",
        action="store_true",
        help="--watch 테스트용 — Wi-Fi SSID 검사 생략",
    )
    return parser


def cli_auto_archive(args: argparse.Namespace) -> bool:
    """``--no-archive`` / ``--opju`` → ``auto_archive`` 인자 (G:·Origin 3~4단계)."""
    return not args.no_archive and args.opju is None


if __name__ == "__main__":
    parser = build_cli_parser()
    args = parser.parse_args()

    print("=" * 60)
    print(" 🧪 GC 분석 & Origin 자동화 (메일 수신 → 계산 → Origin) 🧪")
    print("=" * 60)

    if args.watch:
        from data_pc_watch import run_data_pc_watch

        run_data_pc_watch(
            SCRIPT_DIR,
            opju_path=args.opju,
            auto_archive=cli_auto_archive(args),
            skip_wifi_check=args.no_wifi_check,
        )
        sys.exit(0)

    if args.manual:
        print("\n[수동 모드] 메일 건너뜀 — 엑셀 파일을 직접 지정합니다.")
        while True:
            excel_path = input("\n[1단계] KCH 원본 엑셀을 끌어다 놓으세요 (종료: q) ➔ ")
            if excel_path.strip().lower() == "q": break
            excel_path = excel_path.strip(' "\'')
            run_workflow_for_file(
                excel_path,
                opju_path=args.opju,
                auto_archive=cli_auto_archive(args),
            )
            print("-" * 60)
        sys.exit(0)

    if args.poll_once:
        result = process_new_gc_emails(
            opju_path=args.opju,
            auto_archive=cli_auto_archive(args),
        )
        sys.exit(0 if result.workflow_count >= 0 else 1)

    # 기본 모드: 1단계 = 네이버 메일 수신
    while True:
        process_new_gc_emails(
            opju_path=args.opju,
            auto_archive=cli_auto_archive(args),
        )
        print("-" * 60)
        again = input("메일 다시 확인: Enter / 종료: q ➔ ").strip().lower()
        if again == "q":
            print("프로그램을 종료합니다.")
            break