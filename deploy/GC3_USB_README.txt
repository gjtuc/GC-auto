GC3 Win7 PC - USB 배포 (차헌)
================================

1. 이 USB의 GC3_chem32-gc-automation.zip 을 GC3 PC에 복사
2. 압축 해제: C:\Users\User\GC3_chem32-gc-automation
   (기존 폴더 있으면 덮어쓰기, env 는 제외)
3. Desktop\KCH\gc_automation.env 는 절대 덮어쓰지 말 것
4. gc_run_force.bat 또는 gc_start_watch.bat 실행

이번 업데이트 핵심:
  - gc_chem32 sliding match (DRM 장주기 — 직전 주입 대비 Area 비교)
  - GC2/GC3 자동 메일 3시간 쿨다운 슬롯

설치 최초 1회만: gc3_setup.bat
  - requirements-gc3.txt 맨 위 한글 주석 있으면 삭제 후 재실행

문의/로그: Desktop\KCH\gc3_validate_log.txt (검증 시)
