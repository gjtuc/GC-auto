# Step 9 — 차헌 GC2/GC3 장비 PC (git pull + 회귀 테스트)

> **실행 위치:** **GC2/GC3 장비 PC** (ChemStation / Chem32 옆) — **차헌 PC(`DESKTOP-BFMLJ9J`) 아님**  
> **목표:** GitHub `GC-auto` 최신본 받기 + GC2/GC3 `gc_automation.py` 기존과 동일 동작 확인  
> **GC1 장비 PC(은규)에서 할 일:** repo push 후 이 문서·`EXPECTED_PCS.json` 전달

---

## 9.0a — Git 자동 동기화 (PC당 1회)

> [`docs/GIT_AUTO_SYNC.md`](../docs/GIT_AUTO_SYNC.md)

```powershell
cd C:\Users\User\chemstation-gc-automation
gc_git_init.bat       # .githooks
gc_git_begin.bat      # pull + SYNC_STATUS 확인
```

이후 Cursor Agent 사용 시: **시작=pull · 종료=push** 자동.

---

## 9.0 — 역할 구분 (오해 방지)

| PC | role | env | 스크립트 |
|----|------|-----|----------|
| **GC2/GC3 장비** (Step 9) | `gc2_pc` / `gc3_pc` | `Desktop\KCH\gc_automation.env` | `gc_automation.py` |
| 차헌 PC (`BFMLJ9J`) | `data_pc` | `Desktop\.cursor\` | `촉매 반응 계산.py` |
| GC1 장비 (은규) | `gc1_pc` | `Desktop\박은규\` | `gc_automation.py` |

Step 9는 **8860/Chem32 장비 PC**만 해당. **차헌 PC**(`BFMLJ9J`)는 Step 6·8 별도.

---

## 9.1 — Git 설치·clone (최초 1회)

```powershell
# Git for Windows 설치 후
cd C:\Users\User
git clone https://github.com/gjtuc/GC-auto.git chemstation-gc-automation
cd chemstation-gc-automation
```

이미 폴더가 있으면:

```powershell
cd C:\Users\User\chemstation-gc-automation
gc_git_pull.bat
```

**필수 규칙:** 다른 PC(은규 GC1)가 push 했으면 **수정·push 전에 반드시 pull** — [`docs/SYNC_TRACKING.md`](../docs/SYNC_TRACKING.md)

---

## 9.2 — `Desktop\KCH\gc_automation.env` (덮어쓰기 금지)

```powershell
# 최초만: 템플릿 참고
notepad deploy\gc_automation.env.gc2
# 실제 운영 파일 (Git 제외):
#   C:\Users\User\Desktop\KCH\gc_automation.env
```

| 키 | GC2 운영값 | GC1과 혼동 금지 |
|----|-----------|----------------|
| `GC_INSTANCE` | `gc2` (GC3: `gc3`) | `gc1` 아님 |
| `EXCEL_OUTPUT_DIR` | `Desktop\KCH` | `박은규` 아님 |
| `CHEMSTATION_MODE` | `8860` (GC3: `chem32`) | `gc1` 아님 |
| `REQUIRED_HOTSPOT` | `iptime` (구 `AndroidHotspot5841`) | `iPhone` 아님 |
| `NAVER_EMAIL` | `kimcha0809@...` | `john3556@...` 아님 |

**repo의 `deploy/gc_automation.env.gc2` 를 그대로 덮어쓰지 말 것** — 기존 앱비밀번호 유지.

### 9.2a — 사무실 Wi-Fi vs 핫스팟 (GC8860, 2026-06~)

| 구분 | SSID | 비고 |
|------|------|------|
| **PC 사무실** | `iptime`, `iptime 2`, `iptime_5G` | **세 개 모두 연결 가능** — git, Cursor OK |
| **본 공유기** | `iptime` | 휴대폰 Wi-Fi·공유기 |
| **증폭기** | `iptime 2`, `iptime_5G` | PC가 자동 연결될 수 있음 |
| **핫스팟** (`REQUIRED_HOTSPOT`) | `iptime` | 구 `AndroidHotspot5841` 에서 이름 변경 |

- `Desktop\KCH\gc_automation.env` 에 `REQUIRED_HOTSPOT=iptime` 반영.
- **SSID 주의:** 공유기·핫스팟 모두 `iptime` 이라 PC가 사무실 `iptime`(공유기)에 붙어 있어도 watch가 “핫스팟 연결”로 볼 수 있음(사무실 인터넷 SMTP). `iptime_5G`·`iptime 2` 에선 SSID 불일치 — 메일 시 휴대폰 핫스팟 `iptime` 연결.
- 참고: `deploy/machine_profile.reference.gc8860.json`

---

## 9.3 — `machine_profile.json` (로컬, Git 제외)

```powershell
Copy-Item deploy\machine_profile.template.gc2.json "$env:USERPROFILE\Desktop\KCH\machine_profile.json"
# identifiers 채우기 (Step 2 와 동일)
```

`role` = `gc2_pc` (또는 GC3 전용 PC면 `gc3_pc`로 명시)

---

## 9.4 — sync registry 1회 등록

```powershell
gc_git_pull.bat
gc_git_status.bat
# deploy\SYNC_STATUS.md 에 이 PC 행이 생기고 [OK] 또는 pull 기록 확인
```

`deploy\sync_registry\EXPECTED_PCS.json` 의 `DESKTOP-XXXXXXX` 를 **실제 `$env:COMPUTERNAME`** 으로 수정 후 commit (차헌 PC에서):

```powershell
# pc_id 수정 후
gc_git_push.bat
```

---

## 9.5 — 프로필 자동 판별

```powershell
cd C:\Users\User\chemstation-gc-automation
python gc_automation.py --show-profile
```

**PASS (GC2):**

- `GC_INSTANCE` / 인스턴스: **gc2**
- 출력 폴더: `Desktop\KCH`
- env: `Desktop\KCH\gc_automation.env`
- 핫스팟: **AndroidHotspot5841**
- ChemStation 모드: **8860**

또는:

```powershell
powershell -File scripts\verify_gc2_setup.ps1
```

---

## 9.6 — GC1 설정 유입 검사 (회귀 9.6)

`verify_gc2_setup.ps1` 이 다음을 **FAIL** 처리해야 함:

| GC1 전용 | GC2/GC3 장비 PC에 있으면 안 됨 |
|----------|----------------------|
| `REQUIRED_HOTSPOT=iPhone` | FAIL |
| `john3556@naver.com` in env | FAIL |
| `CHEMSTATION_MODE=gc1` | FAIL |
| `AUTOCHRO_ENABLED=1` in KCH env | FAIL (GC1 전용) |

GC1 모듈(`gc_autochro`, `gc_gc1`)은 repo에 **있어도** GC2 실행 경로에서 호출되지 않음 — `gc_profiles` 분기.

---

## 9.7 — `--verify` (heartbeat·경로)

```powershell
python gc_automation.py --verify
# 또는
gc_verify.bat
```

watch 가 한 번이라도 돌았으면 `Desktop\KCH\MMDDHHmm.txt` heartbeat ±5분 검사.

---

## 9.8 — 파이프라인 dry-run (메일 없이)

```powershell
# Android 핫스팟 연결 후
python gc_automation.py --force --no-email
```

**PASS:** ChemStation `sequence.acam_` → KCH xlsx 생성 (`Desktop\KCH`)

GC3 PC면 `GC_INSTANCE=gc3`, `CHEMSTATION_MODE=chem32` 확인 후 동일.

---

## 9.9 — watch 스모크 (선택, 운영 전)

```powershell
gc_start_watch.bat
# 또는
python gc_automation.py --watch
```

- 핫스팟 **연결 edge** 에서만 1회 처리 (GC2: am/pm 슬롯 규칙은 통합 repo에서 session 기반으로 변경됐을 수 있음 — `gc_watch.py` 주석 확인)
- `gc_watch_status.bat` 로 상태 확인
- 종료: `gc_stop_watch.bat`

---

## 9.10 — 메일 회귀 (선택)

```powershell
python gc_automation.py --force
```

`kimcha0809@naver.com` 수신·보낸메일함에 `GC 분석 결과` + xlsx 첨부.

---

## 9.11 — GitHub push (차헌 PC에서 수정 시)

```powershell
gc_git_pull.bat
# ... 수정 ...
gc_git_push.bat
```

은규 GC1 장비 PC는 **pull 후** 작업 (`SYNC_STATUS.md` 확인).

---

## Step 9 체크리스트

- [ ] 9.1 clone / `gc_git_pull.bat`
- [ ] 9.2 `Desktop\KCH\gc_automation.env` GC2 값 유지
- [ ] 9.3 `machine_profile.json` (`gc2_pc`)
- [ ] 9.4 `SYNC_STATUS.md` PC 등록
- [ ] 9.5 `--show-profile` → gc2, KCH, AndroidHotspot5841
- [ ] 9.6 GC1 설정 유입 없음 (`verify_gc2_setup.ps1`)
- [ ] 9.7 `--verify`
- [ ] 9.8 `--force --no-email` → xlsx
- [ ] 9.9 watch 스모크 (선택)
- [ ] 9.10 메일 (선택)
- [ ] 9.11 `EXPECTED_PCS.json` 실제 PC 이름 반영

---

## GC1 장비 PC(은규) — 차헌에게 넘기기 전

```powershell
gc_git_pull.bat
powershell -File scripts\verify_gc2_pull_ready.ps1
```

PASS 후 차헌에게 전달:

1. `https://github.com/gjtuc/GC-auto`
2. `deploy/STEP9_gc2_pc.md`
3. `deploy/GC2_Cursor_핸드오프.md` (상세 회귀 표)

---

## 다음

- **차헌 PC** `BFMLJ9J`: Step 6 + Step 8 (별도)
- GC1: Step 7 CALIB + Step 8 E2E
