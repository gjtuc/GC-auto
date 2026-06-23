GC3 Win7 PC - USB 배포 (차헌)
================================

1. 이 USB의 GC3_chem32-gc-automation.zip 을 GC3 PC에 복사
2. 압축 해제: C:\Users\User\GC3_chem32-gc-automation
   (기존 폴더 있으면 gc_*.py / gc_*.bat 덮어쓰기)
3. Desktop\KCH\gc_automation.env 는 절대 덮어쓰지 말 것
   - AUTO_MAIL_COOLDOWN_HOURS=3 이 있으면 삭제하거나 =1 로 변경 (기본 1시간)
4. gc_stop_watch.bat 후 gc_start_watch.bat (또는 gc_install_autostart 재로그인)

이번 zip 포함 수정 (2026-06-23)
--------------------------------
  [gc_chem32] sliding match — DRM 장주기, 직전 주입 대비 Area 비교
  [gc_chem32] FID/TCD 1:1 쌍, Area% 1.000e2 파싱, 미완료 Report 제외
  [gc_watch]  Wi-Fi 유지 중 15초 poll (핫스pot 껐다 켤 필요 없음)
  [메일]      1시간 쿨다운만 (SMTP 검증 성공 후 0/1), 쿨다운 중에도 엑셀 생성
  [검증]      gc_chem32_validate.py --audit --compare-xlsx

설치 최초 1회만: gc3_setup.bat
  - requirements-gc3.txt 맨 위 한글 주석 있으면 삭제 후 재실행

반영 확인:
  python gc_automation.py --show-profile  → gc3, chem32
  python gc_chem32_validate.py --data-path C:\Chem32\1\Data --audit
  Desktop\KCH\MMDDHHmm.txt 가 5분 이내면 watch 정상

문의/로그: Desktop\KCH\gc3_validate_log.txt
