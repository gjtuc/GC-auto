# Step 8 — End-to-end (GC1 메일 → 은규 PC 계산 → G: → Origin)

> PC 명칭: [`docs/PC_NAMING.md`](../docs/PC_NAMING.md)

> **전제:** Step 7 실측 완료 (`GC1_CALIB_READY=True`)  
> **역할:** GC1 장비 PC = 메일 **발송** / **은규 PC** = 메일 **수신**·계산·G:·Origin  
> (같은 물리 PC여도 경로·스크립트는 역할별로 분리)

---

## 파이프라인 한눈에

```
[GC1 장비 PC]  gc_automation.py
    Autochro → PDF → KCH xlsx → SMTP 발송
              ↓ 네이버 메일
[은규 PC]      촉매 반응 계산.py
    1) IMAP → KCH/inbox
    2) 수율/전환율 → KCH/processed
    3) G: 실험 폴더 복사·정리
    4) Origin .opju 열 추가
```

---

## 8.0 — 사전 조건 (모두 PASS 여야 E2E)

```powershell
cd C:\Users\User\chemstation-gc-automation
gc_git_pull.bat
powershell -File scripts\verify_e2e_prerequisites.ps1
python scripts\test_e2e_mail_auth.py
```

| # | 항목 | 확인 |
|---|------|------|
| 0.1 | `GC1_CALIB_READY = True` | Step 7 |
| 0.2 | GC1·데이터 env (`NAVER_EMAIL`, 앱비밀번호) | 각 Desktop 폴더 |
| 0.3 | SMTP·IMAP 로그인 | `test_e2e_mail_auth.py` |
| 0.4 | G: `G:\연구소\실험\실험데이터` 보임 | SecuYouSB |
| 0.5 | `originpro` import | Origin 설치 PC |

---

## 8.1 — G: 드라이브 (SecuYouSB)

**은규 PC에서만 필요** (3~4단계).

1. SecuYouSB 실행 → 보안 USB **로그인(잠금 해제)**
2. 탐색기에서 확인:
   ```
   G:\연구소\실험\실험데이터\촉매 반응\DRE 반응(C2H6)
   G:\연구소\실험\실험데이터\촉매 반응\DRM 반응 (CH4)
   G:\연구소\실험\실험데이터\촉매 반응\DRME 반응 (C2H6+CH4)
   ```
3. `verify_e2e_prerequisites.ps1` → `G: experiment root: OK`

**실패 시:** 2단계까지는 가능 (`KCH\processed\`에 계산본 저장). G: 로그인 후 **같은 메일/파일로 재실행**.

---

## 8.2 — Origin + originpro (은규 PC)

1. Origin이 이 PC에 설치되어 있어야 함
2. Python 패키지:
   ```powershell
   pip install originpro
   python -c "import originpro; print('OK')"
   ```
3. Origin이 한 번이라도 GUI로 실행된 적 있어야 라이선스·COM 연동이 잡히는 경우가 많음

**8.2b 단계적 검증:** `--no-archive` 로 2단계만 먼저 (Origin 불필요)

---

## 8.3 — GC1 장비: KCH xlsx + 메일 발송

**GC1 장비 PC** (`Desktop\박은규\`):

```powershell
cd C:\Users\User\chemstation-gc-automation
python gc_automation.py --show-profile   # gc1, iPhone 확인
```

### 8.3a 엑셀만 (메일 없이)

```powershell
python gc_automation.py --force --no-email
```

→ `Desktop\박은규\YYYYMMDD ... DRE@600.xlsx` 생성 확인 (FID/TCD 2시트)

### 8.3b 메일 발송 (iPhone 핫스팟 필요)

```powershell
# iPhone 핫스팟 연결 후
python gc_automation.py --force
```

**PASS:** 네이버 **보낸메일함**에 제목 `GC 분석 결과` 메일, KCH xlsx 첨부

### 8.3c watch 운영 (일상)

```powershell
python gc_automation.py --watch
```

---

## 8.4 — 은규 PC: IMAP 수신 (1단계)

**은규 PC** (`Desktop\.cursor\`):

```powershell
python scripts\test_e2e_mail_auth.py --imap-only
```

전체 파이프라인 1단계만:

```powershell
python "$env:USERPROFILE\Desktop\.cursor\촉매 반응 계산.py"
# G: 없으면 2단계 후 중단 가능 — inbox에 xlsx 저장됐는지 먼저 확인
```

**PASS:** `Desktop\.cursor\KCH\inbox\` 에 GC1 KCH xlsx

---

## 8.5 — 2단계: 계산만 (`--no-archive`)

G:·Origin 없이 수율/전환율 검증:

```powershell
python "$env:USERPROFILE\Desktop\.cursor\촉매 반응 계산.py" --no-archive
```

또는 수동:

```powershell
python "$env:USERPROFILE\Desktop\.cursor\촉매 반응 계산.py" --manual --no-archive
```

**PASS:** `KCH\processed\*_GC1_DRE_계산완료.xlsx` (또는 `_GC1_DRM_`)

---

## 8.6 — 3단계: G: 실험 폴더

**8.1 G: 로그인 후**, `--no-archive` **없이**:

```powershell
python "$env:USERPROFILE\Desktop\.cursor\촉매 반응 계산.py" --no-archive
# 아니 — 3단계만 하려면 전체 실행에서 4단계 전까지; 또는 inbox 파일로:
python "$env:USERPROFILE\Desktop\.cursor\촉매 반응 계산.py" --manual
# (G: 필요 — auto_archive=True 기본)
```

실제로는 **기본 실행**이 2→3→4 연속. G: 확인 후:

```powershell
python "$env:USERPROFILE\Desktop\.cursor\촉매 반응 계산.py"
```

**PASS:** `G:\...\YYYYMMDD DRE(...)\` 새 폴더, 계산 xlsx·opju·pptx 배치

---

## 8.7 — 4단계: Origin `.opju`

3단계와 동일 실행에 포함 (`update_origin`). Origin GUI에서 새 시료 **Comments** 열 확인.

**수동 opju 지정 (G: 폴더 생성 생략):**

```powershell
python "...\촉매 반응 계산.py" --manual --opju "G:\...\기존.opju"
```

---

## 8.8 — Full E2E 체크리스트 (1회 통합 테스트)

| 순서 | PC | 동작 | PASS 기준 |
|------|-----|------|-----------|
| 1 | GC1 | `gc_git_pull.bat` | 최신 코드 |
| 2 | 데이터 | `verify_e2e_prerequisites.ps1` | 0.1~0.5 |
| 3 | 데이터 | SecuYouSB → G: | 경로 보임 |
| 4 | GC1 | iPhone + `--force` | KCH xlsx + 메일 발송 |
| 5 | 데이터 | `촉매 반응 계산.py` | inbox → processed → G: → Origin |
| 6 | 데이터 | Origin 열기 | 새 시료 열·수치 일치 |
| 7 | 공통 | `gc_git_push.bat` | 다른 PC에 기록 |

---

## 8.9 — 장애 분기

| 증상 | 원인 | 조치 |
|------|------|------|
| 메일 안 옴 | GC1 핫스팟/SMTP | iPhone 연결, `test_e2e_mail_auth.py --smtp-only` |
| inbox 비어 있음 | IMAP 계정 불일치 | GC1·데이터 env 동일 네이버 계정인지 |
| `GC1 CALIB 미설정` | Step 7 미완 | `STEP7_gc1_calib.md` |
| G: 오류 후 중단 | SecuYouSB | 로그인 후 재실행 (processed 사본 있음) |
| originpro 오류 | 미설치/Origin 없음 | Step 8.2 |
| 수율 이상 | CALIB/feed | `extract_gc1_rt` / 표준가스 재교정 |

---

## Step 8 완료 정의

- [ ] 8.0 사전 조건 PASS
- [ ] 8.1 G: 접근
- [ ] 8.2 originpro
- [ ] 8.3 GC1 → 메일 발송 1건
- [ ] 8.4~8.7 은규 PC full pipeline 1건
- [ ] 8.8 체크리스트 전부 체크

---

## 다음: Step 9

[`deploy/STEP9_gc2_pc.md`](STEP9_gc2_pc.md) — 차헌 GC2/GC3 장비 PC git pull + 회귀 (**차헌 PC** `BFMLJ9J` 와 별도)
