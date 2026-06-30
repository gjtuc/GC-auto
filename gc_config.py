# -*- coding: utf-8 -*-
"""
gc_config.py — 경로·상수·실행 설정(AppConfig)

=============================================================================
[PC 명칭 — 오해 금지]  docs/PC_NAMING.md
=============================================================================

  이 파일 기본값은 **차헌의 GC2/GC3 장비 PC** 쪽(Desktop\\KCH, Wi-Fi 게이트 iptime 3종)입니다.
  **은규 PC / 차헌 PC** 에서는 gc_automation.py 를 돌리지 않으므로 이 기본값과 무관합니다.

  | PC 종류              | env 위치              | 이 파일 기본값 덮어씀? |
  |----------------------|-----------------------|------------------------|
  | GC1 장비 PC (은규)   | Desktop\\박은규\\...  | 예 (iPhone, gc1)       |
  | GC2/GC3 장비 (차헌)  | Desktop\\KCH\\...   | env 없으면 기본값 사용 |
  | 은규 PC / 차헌 PC    | Desktop\\.cursor\\... | (본 모듈 미사용)       |

=============================================================================
[env vs 코드]
=============================================================================

  GC1 장비 PC는 Desktop\\박은규\\gc_automation.env 가 로드되면 덮어씁니다:

    REQUIRED_HOTSPOT=iPhone
    CHEMSTATION_MODE=gc1
    MAIL_TO, NAVER_EMAIL … 은규 계정

  **TARGET_EMAIL 아래 상수**는 레거시 기본값 — 실제 발송은 env 우선.

=============================================================================
[AppConfig]
=============================================================================

  gc_automation CLI 인자 + gc_automation.env 가 합쳐진 **한 번의 실행** 설정.

  hotspot_reconnect_min_sec:
    GC1 30분 / GC2·3 45s — 순간 끊김 vs 재연결 구분 (gc_watch.py)
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import Optional


# ---------------------------------------------------------------------------
# ChemStation / KCH 경로
# ---------------------------------------------------------------------------

# Agilent ChemStation 기본 Data 루트 — GC2 장비 PC (8860 acam).
DEFAULT_CHEMSTATION_DATA = r"C:\Users\Public\Documents\ChemStation\1\Data"

# Chem32 / GC7890 — GC3 장비 PC (Report.TXT). env CHEMSTATION_DATA_PATH 로 덮어씀.
DEFAULT_GC3_DATA = r"C:\Chem32\1\Data"

# KCH 엑셀·상태 파일 — GC2/GC3 **장비** PC 기본 (Desktop\KCH).
# GC1 **장비** PC는 Desktop\박은규 (env EXCEL_OUTPUT_DIR).
# 「차헌 PC」데이터 PC도 inbox 경로에 KCH 라는 이름을 쓰지만 Desktop\.cursor\KCH 이며 별개.
EXCEL_OUTPUT_DIR = os.path.join(os.path.expanduser("~"), "Desktop", "KCH")


def default_send_state_path() -> str:
    """일일 자동 메일 횟수·마지막 처리 시각 기록 JSON."""
    return os.path.join(EXCEL_OUTPUT_DIR, ".gc_send_state.json")


def default_watch_status_json() -> str:
    return os.path.join(EXCEL_OUTPUT_DIR, ".gc_watch_status.json")


def default_watch_status_txt() -> str:
    return os.path.join(EXCEL_OUTPUT_DIR, "GC_감시_상태.txt")


# ---------------------------------------------------------------------------
# GC2/GC3 핫스팟 / 자동 메일 쿨다운 슬롯
# ---------------------------------------------------------------------------

# GC2/GC3 Wi-Fi 게이트 SSID (쉼표 구분). 구 AndroidHotspot5841 → 연구실 iptime 3종.
REQUIRED_HOTSPOT_SSID = "iptime,iptime 2,iptime_5G"

# 레거시 (am/pm 표시·구형 state 호환)
DAILY_SEND_LIMIT = 2
AFTERNOON_START_HOUR = 12

# watch: 순간 끊김(약한 신호) vs 사용자가 껐다 켠 재연결 구분(초)
DEFAULT_HOTSPOT_RECONNECT_MIN_SEC = 45
DEFAULT_GC1_HOTSPOT_RECONNECT_MIN_SEC = 1800  # 30분 — 순간 끊김·에이전트 재요청 쿨다운


def hotspot_reconnect_min_sec(chemstation_mode: str = "auto") -> int:
    """
    핫스pot 재연결 최소 간격(초).
    이보다 짧게 끊겼다 붙으면 '순간 끊김' — 동일 세션, 재처리·재발송 안 함.
    """
    if chemstation_mode == "gc1":
        raw = os.getenv("GC1_HOTSPOT_RECONNECT_MIN_SEC", "").strip()
        default = DEFAULT_GC1_HOTSPOT_RECONNECT_MIN_SEC
    else:
        raw = os.getenv("HOTSPOT_RECONNECT_MIN_SEC", "").strip()
        default = DEFAULT_HOTSPOT_RECONNECT_MIN_SEC
    if not raw:
        return default
    try:
        return max(5, int(raw))
    except ValueError:
        return default

# ---------------------------------------------------------------------------
# 메일 (네이버 SMTP)
# ---------------------------------------------------------------------------

# 레거시 기본 수신 주소 — **차헌 PC** 메일(kimcha). 실제 발송은 env MAIL_TO 우선.
# GC1 장비 PC 운영 시 MAIL_TO 는 **은규 PC** 네이버 주소로 바꿀 것 (장비 env에서 설정).
TARGET_EMAIL = "kimcha0809@naver.com"
NAVER_SMTP_HOST = "smtp.naver.com"
NAVER_SMTP_PORT = 587


def _env_int(name: str, default: int, minimum: int = 0) -> int:
    raw = os.getenv(name, "").strip()
    if not raw:
        return default
    try:
        return max(minimum, int(raw))
    except ValueError:
        return default


# GC2/GC3 — 자동 메일 쿨다운(시간). 성공 발송·SMTP 검증 후 N시간 동안 슬롯 0/1.
AUTO_MAIL_COOLDOWN_HOURS = _env_int("AUTO_MAIL_COOLDOWN_HOURS", 1, minimum=1)

# 핫스팟 직후 DNS·SMTP 준비 대기 (getaddrinfo failed 방지)
SMTP_INTERNET_WAIT_MAX_SEC = _env_int("SMTP_INTERNET_WAIT_MAX_SEC", 120)
SMTP_INTERNET_POLL_SEC = _env_int("SMTP_INTERNET_POLL_SEC", 5)
SMTP_SEND_RETRIES = _env_int("SMTP_SEND_RETRIES", 5, minimum=1)
SMTP_SEND_RETRY_DELAY_SEC = _env_int("SMTP_SEND_RETRY_DELAY_SEC", 15)
SMTP_SOCKET_TIMEOUT_SEC = _env_int("SMTP_SOCKET_TIMEOUT_SEC", 60)
# 핫스pot edge 직후 pipeline 전 SMTP 준비 대기 (초)
SMTP_POST_HOTSPOT_WAIT_MAX_SEC = _env_int("SMTP_POST_HOTSPOT_WAIT_MAX_SEC", 120)
# pending 메일 — 핫스pot 유지·순간 재연결 중 자동 재시도 간격 (초), 성공까지
PENDING_EMAIL_RETRY_INTERVAL_SEC = _env_int("PENDING_EMAIL_RETRY_INTERVAL_SEC", 30, minimum=15)
# watch tick 내 pending 재시도 — 짧은 SMTP 대기 (루프 멈춤 방지)
PENDING_EMAIL_SMTP_WAIT_MAX_SEC = _env_int("PENDING_EMAIL_SMTP_WAIT_MAX_SEC", 45, minimum=10)
PENDING_EMAIL_SEND_RETRIES = _env_int("PENDING_EMAIL_SEND_RETRIES", 2, minimum=1)
# watch heartbeat 이 시간(초) 이상 멈추면 watchdog 가 watch 프로세스 재시작
WATCH_HEARTBEAT_STALE_SEC = _env_int("WATCH_HEARTBEAT_STALE_SEC", 180, minimum=60)

# ---------------------------------------------------------------------------
# 시료 동일성 판별 (RT 지문)
# ---------------------------------------------------------------------------

COMPARE_CYCLES = 3
RT_TOLERANCE = 0.02

# GC3 — 인접 주입(sliding) Area 상대 허용 (0.12 ≈ ±12%). DRM 장시간 반응 drift 대응.
AREA_MATCH_TOLERANCE = 0.12

# ---------------------------------------------------------------------------
# KCH 엑셀 컬럼
# ---------------------------------------------------------------------------

# GC2 (8860 / acam) — Type 앞 공백
CHEMSTATION_COLUMNS = ["#", "Time", " Type", "Area", "Height", "Width", "Area%", "Symmetry"]

# GC3 (Chem32 / Report) — Type 열 없음
CHEM32_COLUMNS = ["#", "Time", "Area", "Height", "Width", "Area%", "Symmetry"]
CHEM32_HEADER_ROW = {
    "#": "#",
    "Time": "Time",
    "Area": "Area",
    "Height": "Height",
    "Width": "Width",
    "Area%": "Area%",
    "Symmetry": "Symmetry",
}
CHEM32_FID_SHEET = "FID"
CHEM32_TCD_SHEET = "TCD"
HEADER_ROW = {
    "#": "#",
    "Time": "Time",
    " Type": "Type",
    "Area": "Area",
    "Height": "Height",
    "Width": "Width",
    "Area%": "Area%",
    "Symmetry": "Symmetry",
}

# ---------------------------------------------------------------------------
# 바탕화면 heartbeat (MMDDHHmm.txt)
# ---------------------------------------------------------------------------
#
# --watch 가 15초마다 tick, 핫스팟 연결 중 바탕화면 06151513.txt 이름 갱신.
#   · 파일 **이름** = 마지막 핫스팟 연결 시각 (MM=월, DD=일, HH=시, mm=분)
#   · 지금 시각과 ±HEARTBEAT_TOLERANCE_MINUTES 이내면 "GC 자동화 정상"
#   · 5분 이상 밀리면 watch 멈춤 또는 핫스팟 미연결
#
# 검증: python gc_automation.py --verify  또는 gc_verify.bat
# Cursor: force 후 이 검증만 통과하면 추가 수리 불필요 (exit 0)

DESKTOP_STOPPED_PREFIX = "GC_중지_"

HEARTBEAT_TOLERANCE_MINUTES = 5


@dataclass
class AppConfig:
    """
    한 번의 실행(run)에 필요한 모든 설정.

    [필드 설명]
      data_path          : ChemStation Data 루트
      excel_output_dir   : KCH 엑셀·.env·상태 파일 폴더
      send_email         : False 면 엑셀만 (--no-email)
      sample_name        : CLI --sample-name — 새 날짜 시퀀스면 반드시 필요 (watch 자동 불가)
      sequence_date      : CLI --sequence-date (YYYYMMDD)
      sequence_folder    : CLI --sequence-folder (절대 경로, date 보다 우선)
      detector           : TCD | FID
      required_ssid      : --watch / 자동 메일에 필요한 Wi-Fi SSID
      skip_wifi_check    : 테스트용 핫스팟 검사 생략
      force              : 사용자 수동 --force (핫스팟·메일 쿨다운 무시)
      allow_prompt       : False 면 시료명 없을 때 input() 대신 실패 (--watch 용)
      send_state_file    : 처리·발송 기록 JSON 경로
      chemstation_mode   : auto | 8860 | chem32 (GC3 Chem32)
    """

    data_path: str = DEFAULT_CHEMSTATION_DATA
    chemstation_mode: str = "auto"
    excel_output_dir: str = field(default_factory=lambda: EXCEL_OUTPUT_DIR)
    send_email: bool = True
    sample_name: Optional[str] = None
    sequence_date: Optional[str] = None
    sequence_folder: Optional[str] = None
    detector: str = "TCD"
    required_ssid: str = REQUIRED_HOTSPOT_SSID
    skip_wifi_check: bool = False
    force: bool = False
    allow_prompt: bool = True
    send_state_file: str = field(default_factory=default_send_state_path)
