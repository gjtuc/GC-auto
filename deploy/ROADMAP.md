# GC-auto 통합 로드맵

## 완료

- [x] **Step 1** — GitHub `gjtuc/GC-auto` 연동 (GC1 PC `DESKTOP-MBGSSME`)
- [x] **Step 2** — `Desktop\박은규\machine_profile.json` + deploy 템플릿
- [x] **Step 3** — `data_pc/` (촉매 반응 계산.py, KCH, env 예시)
- [x] **Step 4** — README·docs·Step 가이드 통합
- [x] **Step 5** — `.gitignore` 점검, auto-sync hook

## 다음 (운영)

- [ ] **Step 6** — 데이터 PC: `Desktop\.cursor\`에 `data_pc/` 배치 + env + machine_profile
- [ ] **Step 7** — GC1 CALIB/TIME 실측 → `촉매 반응 계산.py` USER SETTINGS
- [ ] **Step 8** — end-to-end: GC1 메일 → 데이터 PC 계산 → G: → Origin
- [ ] **Step 9** — 차헌 PC `git pull` + GC2 회귀 테스트

## PC별 git

```powershell
cd C:\Users\User\chemstation-gc-automation   # 또는 clone GC-auto
git pull    # 시작
git push    # 종료 (또는 Agent auto hook)
```
