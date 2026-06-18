# -*- coding: utf-8 -*-
"""
gc_architecture.py — GC 자동화 코드베이스 개요 (실행 코드 없음, LLM·신규 개발자용)

이 파일은 import 되지 않아도 됩니다. **목적·원리·파일 관계**만 문서화합니다.
구현 세부는 각 모듈 상단 docstring 을 참고하세요.

=============================================================================
[한 줄 요약]
=============================================================================

  GC2/GC3: ChemStation 데이터 → KCH 엑셀 → (핫스pot 시) 네이버 메일
  GC1:     Autochro UI → PDF → gc_gc1 파싱/trim → 엑셀 → (iPhone 핫스pot 시) 메일

  공통 CLI: gc_automation.py
  설정:     Desktop\\박은규\\gc_automation.env (GC1) / Desktop\\KCH\\... (GC2/GC3)

=============================================================================
[PC / 프로필]  gc_profiles.py
=============================================================================

  GC1  박은규  Desktop\\박은규   REQUIRED_HOTSPOT=iPhone    CHEMSTATION_MODE=gc1
  GC2  kimcha  Desktop\\KCH      AndroidHotspot5841         8860 (acam)
  GC3  kimcha  Desktop\\KCH      AndroidHotspot5841         chem32 (Report)

=============================================================================
[실행 모드 3가지]
=============================================================================

  1) watch (--watch, GC1_감시시작.bat)
     · 핫스pot **연결 edge** 에서만 자동 처리
     · 연결 유지 중에는 반복 실행 없음
     · GC2: 새 acam + 오전/오후 메일 각 1회
     · GC1: **세션당 1회** PDF·엑셀·메일 (슬롯 한도 없음)
     · 순간 끊김(< GC1_HOTSPOT_RECONNECT_MIN_SEC) → 동일 세션, skip

  2) force (--force, gc_동작해줘.bat, --request)
     · 핫스pot·일일한도 무시
     · GC1: Autochro PDF 재내보내기 + 전체 pipeline

  3) Cursor 개시 (--user-message "진행" 등)  gc_request.py
     · message_is_initiation() == True → force 와 동일 + heartbeat 검증
     · exit 0/1/2 → Cursor 후속 행동

=============================================================================
[GC1 end-to-end 데이터 흐름]
=============================================================================

  [Autochro CRM 갱신]
         ↓
  gc_autochro.run_autochro_export()  ← pywinauto UI 5단계
         ↓
  Desktop\\박은규\\*.pdf  (125p 등)
         ↓
  gc_gc1.parse_gc1_pdf_path()
    · overflow 페이지 병합
    · maybe_drop_last_incomplete_gc1_cycle (B 채널 전압선 길이)
    · trim_reduction_and_first_reaction
         ↓
  YYYYMMDD 시료명.xlsx  (FID/TCD, 「분석된 원소」열)
         ↓
  gc_mailer.send_email_via_smtp()  (NAVER_EMAIL → MAIL_TO)

=============================================================================
[주요 모듈 맵]
=============================================================================

  gc_automation.py   CLI 진입, watch/force/user-message 분기
  gc_watch.py        핫스pot edge tick, GC1/GC2 분기
  gc_pipeline.py     run_processing_gc1 / chem32 / 8860
  gc_autochro.py     Autochro-3000 PDF UI 자동화
  gc_gc1.py          PDF 파싱, trim, cleanup, 엑셀
  gc_state.py        .gc_send_state.json (한도, pending 메일, mtime)
  gc_wifi.py         SSID, SMTP 게이트, check_runtime_gate
  gc_request.py      「시작」「go」 개시 문구 → force
  gc_mailer.py       네이버 SMTP
  gc_config.py       AppConfig, hotspot_reconnect_min_sec
  gc_profiles.py     GC1/GC2/GC3 env 탐색
  gc_status.py       MMDDHHmm.txt heartbeat

=============================================================================
[GC1 UI 자동화에서 자주 깨지는 경우]
=============================================================================

  · Autochro 창이 화면 밖 → AUTOCHRO_AUTO_POSITION, 상대 좌표 list/tree
  · Ctrl+A 실패 → 소유자 ID 열 드롭다운 → AUTOCHRO_LIST_NEUTRAL_X_FRAC
  · PDF 3페이지만 저장 → 위 Ctrl+A 문제
  · Hancom 창 잔류 → AUTOCHRO_HANCOM_WAIT_SEC
  · PDF 잠금 → GC1_PDF_READY_WAIT_SEC

=============================================================================
[상태 파일 위치]
=============================================================================

  Desktop\\박은규\\.gc_send_state.json
  Desktop\\박은규\\.gc_watch_status.json
  Desktop\\박은규\\GC_감시_상태.txt
  Desktop\\박은규\\MMDDHHmm.txt  (watch heartbeat, GC2/GC3 Desktop 루트도)

=============================================================================
[배포]
=============================================================================

  GC2 역배포 (통합 repo — GC1+GC2 코드 공존, GC1 삭제 금지):
    deploy\\GC2_baseline_chemstation-gc-automation.zip
    gc2_make_deploy_zip.bat
    deploy\\gc_automation.env.gc2  → Desktop\\KCH\\gc_automation.env (GC2 PC)
    deploy\\gc_automation.env.gc1  → Desktop\\박은규\\... (GC1 PC만)

  GC1 PC 설치: 동일 zip 또는 gc1_make_deploy_zip.bat, 32-bit Python 권장

  GC2 Cursor 핸드오프: deploy\\GC2_Cursor_핸드오프.md

"""

# 이 모듈은 문서 전용입니다. 실행할 함수가 없습니다.
