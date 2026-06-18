# GC-auto 통합 로드맵

## 완료

- [x] **Step 1** — GitHub `gjtuc/GC-auto` 연동 (GC1 장비 PC `DESKTOP-MBGSSME`)
- [x] **Step 2** — `Desktop\박은규\machine_profile.json` + deploy 템플릿
- [x] **Step 3** — `data_pc/` (촉매 반응 계산.py, KCH, env 예시)
- [x] **Step 4** — README·docs·Step 가이드 통합
- [x] **Step 5** — `.gitignore` 점검, auto-sync hook
- [x] **Step 6** — 은규 PC: `Desktop\.cursor\` 배치 + env + machine_profile (GC1 장비 PC에서 세팅, 2026-06-18)
- [x] **Step 7 (코드)** — GC1 TIME·판별·계산 분기 + 측정 스크립트 (`deploy/STEP7_gc1_calib.md`)
- [ ] **Step 7 (실측)** — GC1 CALIB 표준가스 실측 + `GC1_CALIB_READY=True` + `--no-archive` 검증

## 다음 (운영)

- [ ] **Step 6b** — (차헌 PC 등 별도 데이터 PC 생기면) 동일 절차 + `gc_git_pull.bat` 1회
- [ ] **Step 7** — GC1 CALIB 실측 → `GC1_CALIB_READY=True` ([`deploy/STEP7_gc1_calib.md`](STEP7_gc1_calib.md))
- [ ] **Step 8** — E2E: GC1 메일 → 은규 PC → G: → Origin ([`deploy/STEP8_e2e.md`](STEP8_e2e.md))
  - [x] 8.0 가이드 + `verify_e2e_prerequisites.ps1` + `test_e2e_mail_auth.py`
  - [x] 8.0b GC1 장비 PC: SMTP/IMAP 로그인 PASS (2026-06-18)
  - [ ] 8.1 G: (SecuYouSB) / 8.2 originpro
  - [ ] 8.3~8.8 full pipeline (Step 7 CALIB 선행)
- [ ] **Step 9** — 차헌 GC2/GC3 장비 PC git pull + 회귀 ([`deploy/STEP9_gc2_pc.md`](STEP9_gc2_pc.md))
  - [x] 9.0 가이드 + `verify_gc2_setup.ps1` + `run_gc2_regression.ps1` + GC2 machine_profile 템플릿
  - [x] 9.0b GC1 장비 PC: `verify_gc2_pull_ready.ps1` (인수인계 준비)
  - [ ] 9.1~9.11 **차헌 GC2 장비 PC**에서 실행

## PC별 git

```powershell
cd C:\Users\User\chemstation-gc-automation   # 또는 clone GC-auto
git pull    # 시작 — 다른 PC가 올린 최신본 먼저 받기 (필수)
git push    # 종료 (또는 Agent auto hook)
```

**규칙:** 한 PC가 push 한 뒤, 다른 PC는 **pull 없이 push 하지 않음** — [`docs/SYNC_TRACKING.md`](../docs/SYNC_TRACKING.md)
