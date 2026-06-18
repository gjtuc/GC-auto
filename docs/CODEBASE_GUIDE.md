# 코드베이스 가이드 — 다른 PC에서 처음 열 때

> **GitHub:** https://github.com/gjtuc/GC-auto  
> **로컬 clone 예:** `C:\Users\User\chemstation-gc-automation`  
> **Cursor/에이전트:** 이 문서 + `gc_architecture.py` + 해당 PC의 `machine_profile.json` 먼저 읽기

---

## 1. 연구실 자동화는 「두 종류 PC」

| 종류 | 누가 | 어디서 실행 | 스크립트 |
|------|------|-------------|----------|
| **장비 PC** | GC 옆 PC | GC1=은규, GC2/3=차헌 | repo 루트 `gc_automation.py` |
| **데이터 PC** | 업무 PC | 메일·Origin·G: | `data_pc/촉매 반응 계산.py` |

**장비 PC** = KCH **원본** 엑셀 만들고 **메일 발송**  
**데이터 PC** = 메일 **수신** → 수율/전환율 → **G:** → **Origin**

같은 repo에 코드가 **전부** 있지만, **실행 위치는 PC마다 다름.**

---

## 2. GC1 / GC2 / GC3 (장비 PC 분기)

| | GC1 | GC2 | GC3 |
|---|-----|-----|-----|
| 운영 | 은규 | 차헌 | 차헌 |
| 장비 | YL6500 Autochro | Agilent 8860 | Chem32 |
| 데이터 | PDF | `sequence.acam_` | `Report.txt` |
| env 폴더 | `Desktop\박은규` | `Desktop\KCH` | `Desktop\KCH` |
| 핫스팟 | iPhone | AndroidHotspot5841 | 동일 |
| 모듈 | `gc_autochro`, `gc_gc1` | `gc_chemstation` | `gc_chem32` |

**자동 판별:** `gc_profiles.py` → `resolve_profile()`  
env 파일 `GC_INSTANCE=gc1|gc2|gc3`, `CHEMSTATION_MODE=gc1|8860|chem32`

---

## 3. 「지금 이 PC가 누구인지」

| 파일 | 위치 | GitHub |
|------|------|--------|
| `machine_profile.json` | 장비: `Desktop\박은규\` 또는 데이터: `Desktop\.cursor\KCH\` | ❌ 로컬만 |
| `gc_automation.env` | 장비 PC Desktop 폴더 | ❌ 비밀번호 |
| 템플릿 | `deploy/machine_profile.template.*.json` | ✅ |

장비 PC는 **env + gc_profiles** 가 주 분기.  
데이터 PC는 **machine_profile + USER SETTINGS(CALIB/TIME)** 가 주 분기.

---

## 4. 파일 맵 (읽는 순서)

```
1. README.md                    — repo 개요
2. docs/CODEBASE_GUIDE.md       — 본 문서
3. gc_architecture.py           — 장비 PC 파이프라인 (실행 없음)
4. gc_profiles.py               — GC1/2/3 env 분기
5. gc_automation.py             — CLI 진입 (--watch, --force)
6. gc_pipeline.py               — gc1 / 8860 / chem32 처리
7. data_pc/촉매 반응 계산.py    — 데이터 PC (별도 실행)
```

### 장비 PC 전용 모듈

| 파일 | PC | 역할 |
|------|-----|------|
| `gc_autochro.py` | GC1만 | Autochro UI → PDF |
| `gc_gc1.py` | GC1만 | PDF 파싱·trim·엑셀 |
| `gc_chemstation.py` | GC2 | acam XML |
| `gc_chem32.py` | GC3 | Report.txt |
| `gc_work_job.py` | GC2/GC3 위주 | 핫스팟 끊김 시 단계별 재개 |
| `gc_watchdog.py` | GC2/GC3 위주 | watch 프로세스 자동 재시작 |
| `gc_error_handler.py` | GC1 추가 | 오류 시 watch 재시작·Cursor SDK |

### 공통

| 파일 | 역할 |
|------|------|
| `gc_watch.py` | 핫스팟 edge 감시 |
| `gc_state.py` | `.gc_send_state.json` |
| `gc_mailer.py` | 네이버 SMTP |
| `gc_wifi.py` | SSID·SMTP 게이트 |

---

## 5. 데이터 PC (`data_pc/`)

```
data_pc/
├── 촉매 반응 계산.py     ← 메인 (IMAP → 계산 → G: → Origin)
├── gc_automation.env.example
└── KCH/inbox, processed/
```

- **설치:** `deploy/STEP3_data_pc.md`
- **교정:** 파일 상단 `USER SETTINGS` — GC2/GC3는 차헌 실측값, **GC1은 `deploy/STEP7_gc1_calib.md`**
- **장비 PC에서 실행 금지** (Origin·G: 없음)

---

## 6. GitHub 동기화

### 필수: pull → 수정 → push

**다른 PC가 이미 push 했다면, 이 PC는 `gc_git_pull.bat`으로 최신본을 받은 뒤에만 수정·push 합니다.**  
pull 없이 push하면 다른 PC의 최신 수정이 **덮어씌워지거나 유실**될 수 있습니다.

```powershell
.\gc_git_pull.bat    # 작업 시작 — 반드시 먼저 (SYNC_STATUS [WARN] 이면 특히)
# ... 수정 ...
# Agent 종료 시 auto push 또는 gc_git_push.bat
.\gc_git_status.bat  # 누가 최신인지 확인
```

- **현황 표:** [`deploy/SYNC_STATUS.md`](../deploy/SYNC_STATUS.md)
- **상세:** [`docs/SYNC_TRACKING.md`](SYNC_TRACKING.md)
- `.cursor/hooks/auto_git_sync.ps1` — Agent 종료 시 commit+push+registry

---

## 7. PC별 첫 clone 후

### GC1 (은규)

```powershell
git clone https://github.com/gjtuc/GC-auto.git
# Desktop\박은규\gc_automation.env 유지
# Desktop\박은규\machine_profile.json 확인
python gc_automation.py --show-profile
```

### GC2/GC3 (차헌)

```powershell
git pull
# Desktop\KCH\gc_automation.env 유지
deploy\gc_automation.env.gc2 참고
```

### 데이터 PC

```powershell
git pull
# data_pc → Desktop\.cursor 복사 (STEP3)
```

---

## 8. 자주 하는 실수

| 실수 | 올바른 방법 |
|------|-------------|
| GC2 CALIB를 GC1에 복사 | `deploy/STEP7_gc1_calib.md` — GC1 표준가스 실측 |
| 장비 PC에서 촉매 반응 계산 실행 | 데이터 PC에서만 |
| env를 GitHub에 commit | 절대 금지 |
| zip만 배포 | `git pull` 로 통일 |
| **pull 없이 push** | **`gc_git_pull.bat` 먼저** — 다른 PC 최신본 받은 뒤 수정·push |

---

## 9. 상세 문서

| 문서 | 내용 |
|------|------|
| `docs/00_인수인계_설명.md` | 2-PC 파이프라인 (차헌→은규) |
| `deploy/GC1_Cursor_핸드오프.md` | GC1 통합 체크리스트 |
| `deploy/GC2_Cursor_핸드오프.md` | GC2 역배포 |
| `deploy/ROADMAP.md` | Step 6~9 남은 일 |
| `deploy/STEP8_e2e.md` | **E2E** GC1 메일 → 데이터 PC → G: → Origin |
| `deploy/STEP9_gc2_pc.md` | **차헌 GC2** git pull + 회귀 테스트 |
