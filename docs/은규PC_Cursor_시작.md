# 은규 PC — Cursor 에이전트 온보딩 (마스터 체크리스트)

> **GitHub:** https://github.com/gjtuc/GC-auto  
> **이 문서 한 장으로 은규 PC 세팅 전체를 진행합니다.**  
> 차헌(김차헌)이 은규 PC Cursor에 「안녕, 너는 은규 PC야. 깃허브 자료 줄게」만 말해도, **에이전트는 본 문서를 읽고 아래 순서대로 진행**합니다.

---

## 0. 에이전트 정체성 (가장 먼저 이해)

| | **은규 PC (지금 이 PC)** | **GC1 장비 PC (다른 PC)** |
|--|--------------------------|---------------------------|
| **누가** | 은규 (연구원) | 은규 (같은 사람, **다른 컴퓨터**) |
| **역할** | 데이터 PC — 계산·**연구노트**·Origin | 장비 PC — Autochro→PDF→메일 |
| **실행 스크립트** | `gc-data-pc\촉매 반응 계산.py` | repo `gc_automation.py` |
| **env** | `gc-data-pc\gc_automation.env` (IMAP **수신**) | `Desktop\박은규\gc_automation.env` (SMTP **발송**) |
| **GC1 데이터** | ChemStation **아님** — GC1에서 온 **KCH xlsx 메일** 처리 | YL6500 **Autochro** PDF 파이프라인 |

**절대 하지 말 것 (은규 PC):**

- `gc_automation.py` 실행·수정·watch 설정 (GC1 **장비** PC 일)
- 차헌 PC의 **G: 드라이브** 경로를 은규 PC에 쓰지 않음 — 은규는 **로컬 연구노트** 사용
- `Desktop\KCH\` (GC2 **장비** PC 출력)와 `gc-data-pc\PEG\` (은규 PC inbox) 혼동

---

## 1. 전체 자동화 그림 (은규 관점)

```
[GC1 장비 PC]  iPhone 핫스팟 / GC1_동작해줘.bat
    gc_automation.py → gc_autochro → gc_gc1
    → Desktop\박은규\YYYYMMDD 시료.xlsx
    → 네이버 SMTP (MAIL_TO = 은규가 읽는 주소)
              ↓
[은규 PC]  ← 지금 여기
    촉매 반응 계산.py
    1) IMAP 수신 → gc-data-pc\PEG\inbox\
    2) GC1 CALIB로 수율/전환율 → PEG\processed\
    3) **연구노트** 실험 폴더 생성·갱신 (`Desktop\새 폴더\연구노트\DRE` 등)
    4) Origin .opju 새 시료 열
```

메일 첨부 = **KCH 원본** (계산 완료 파일 아님).

---

## 2. 진행 상태 판별 (어디부터 할지)

에이전트는 아래를 **실제로 확인**한 뒤, 첫 `[ ]` 항목부터 진행합니다.

| # | 확인 방법 | 완료 기준 |
|---|-----------|-----------|
| A | `Test-Path "$env:USERPROFILE\gc-data-pc\촉매 반응 계산.py"` | 파일 있음 |
| B | `Test-Path "$env:USERPROFILE\gc-data-pc\gc_automation.env"` | 있고 NAVER_* 채워짐 |
| C | `Test-Path "$env:USERPROFILE\gc-data-pc\PEG\machine_profile.json"` | role=data_pc |
| D | `python ...\촉매 반응 계산.py --help` | exit 0 |
| E | GC1 xlsx로 `--no-archive` | `*_GC1_DRE_계산완료.xlsx` 생성 |
| F | `Test-Path "...\Desktop\새 폴더\연구노트\DRE"` | 연구노트 DRE 폴더 보임 |
| G | `PEG\machine_profile.json` `reaction_roots` | 연구노트 실측 경로와 일치 |
| H | `import originpro` | OK + Origin 설치 |
| I | 메일→계산→연구노트→Origin 1건 | E2E PASS |

---

## 3. Phase 1 — GitHub repo 받기

```powershell
# 최초 1회
cd $env:USERPROFILE
git clone https://github.com/gjtuc/GC-auto.git chemstation-gc-automation

# 이후 매 작업 시작
cd $env:USERPROFILE\chemstation-gc-automation
git pull
```

**완료 기준:** `chemstation-gc-automation\data_pc\촉매 반응 계산.py` 존재, `git log -1` 최신.

**규칙:** 수정 전·후 `git pull` / push — [`docs/GIT_AUTO_SYNC.md`](GIT_AUTO_SYNC.md), [`deploy/SYNC_STATUS.md`](../deploy/SYNC_STATUS.md)

---

## 4. Phase 2 — `gc-data-pc\` 운영 폴더 (Step 6)

> **은규 PC:** 바탕화면 대신 `%USERPROFILE%\gc-data-pc\` 사용 — [`deploy/DATA_PC_HOME_LAYOUT.md`](../deploy/DATA_PC_HOME_LAYOUT.md)

상세: [`deploy/STEP6_data_pc_setup.md`](../deploy/STEP6_data_pc_setup.md)

### 4.1 폴더 생성

```powershell
$base = "$env:USERPROFILE\gc-data-pc"
New-Item -ItemType Directory -Path "$base\PEG\inbox" -Force
New-Item -ItemType Directory -Path "$base\PEG\processed" -Force
```

### 4.2 스크립트 복사 (git pull 후마다)

```powershell
cd $env:USERPROFILE\chemstation-gc-automation
git pull
Copy-Item -LiteralPath "data_pc\촉매 반응 계산.py" -Destination "$env:USERPROFILE\gc-data-pc\" -Force
Copy-Item -LiteralPath "data_pc\runtime_paths.py" -Destination "$env:USERPROFILE\gc-data-pc\" -Force
```

### 4.3 Python 패키지

```powershell
pip install pandas openpyxl python-dotenv numpy
python -c "import pandas, numpy, dotenv; print('core OK')"
```

**완료 기준:** `--help` 성공.

```powershell
python "$env:USERPROFILE\gc-data-pc\촉매 반응 계산.py" --help
```

---

## 5. Phase 3 — 네이버 메일 env (IMAP, 은규 PC 전용)

파일: **`gc-data-pc\gc_automation.env`** (Git에 **올리지 않음**)

템플릿: `data_pc\gc_automation.env.example`

```ini
NAVER_EMAIL=은규_네이버@naver.com
NAVER_APP_PASSWORD=16자리_앱비밀번호
MAIL_TO=은규_네이버@naver.com
```

| 항목 | 설명 |
|------|------|
| `NAVER_EMAIL` | 은규 PC에서 **IMAP으로 읽을** 계정 |
| `NAVER_APP_PASSWORD` | 네이버 메일 → POP3/IMAP → **앱 비밀번호** (로그인 비번 아님) |
| `MAIL_TO` | 수신 확인용 (보통 EMAIL과 동일) |

**GC1 장비 PC 연동:** `Desktop\박은규\gc_automation.env` 의 **`MAIL_TO`** 가 위 주소와 **같아야** 메일이 은규 PC에 도착합니다.  
(장비 env는 **은규 PC에서 수정하지 않음** — GC1 장비 PC에서 확인)

검증:

```powershell
cd $env:USERPROFILE\chemstation-gc-automation
python scripts\test_e2e_mail_auth.py
```

**완료 기준:** IMAP 로그인 PASS.

---

## 6. Phase 4 — `machine_profile.json` (은규 PC 식별)

```powershell
Copy-Item deploy\machine_profile.template.data_pc.json `
  "$env:USERPROFILE\gc-data-pc\PEG\machine_profile.json"
```

채울 필드:

```powershell
$env:COMPUTERNAME
(Get-CimInstance Win32_ComputerSystemProduct).UUID
(Get-ItemProperty 'HKLM:\SOFTWARE\Microsoft\Cryptography').MachineGuid
```

| 필드 | 값 |
|------|-----|
| `role` | `data_pc` |
| `gc_assignment.operator` | `은규` |
| `gc_assignment.equipment` | `GC1` |
| `paths.script_dir` | `C:\Users\User\gc-data-pc` |

**완료 기준:** Cursor가 「이 PC = 은규 데이터 PC」임을 파일로 구분 가능.

---

## 7. Phase 5 — 연구노트 실험 폴더 경로 (은규 PC · **G: 미사용**)

> **[LLM] 은규 PC는 G: 드라이브(SecuYouSB)를 쓰지 않습니다.**  
> 실험 결과는 로컬 **`C:\Users\User\Desktop\새 폴더\연구노트`** 아래에서 정리합니다.

상세: [`docs/DATA_PC_PATHS.md`](DATA_PC_PATHS.md), [`deploy/DATA_PC_HOME_LAYOUT.md`](../deploy/DATA_PC_HOME_LAYOUT.md)

### 7.1 은규 PC 실측 경로 (2026-06)

| 반응 | 경로 | 비고 |
|------|------|------|
| **DRE** | `C:\Users\User\Desktop\새 폴더\연구노트\DRE` | **현재 운영 중** |
| **DRM** | `...\연구노트\DRM` | 폴더 생기면 사용 |
| **DRME** | `...\연구노트\DRME` | 폴더 생기면 사용 |
| **상위** | `C:\Users\User\Desktop\새 폴더\연구노트` | `experiment_data_root` |

### 7.2 설정 위치 (스크립트 직접 수정 X)

**`gc-data-pc\PEG\machine_profile.json`** 에 저장 (Git 제외):

```json
"reaction_roots": {
  "DRE": "C:\\Users\\User\\Desktop\\새 폴더\\연구노트\\DRE",
  "DRM": "C:\\Users\\User\\Desktop\\새 폴더\\연구노트\\DRM",
  "DRME": "C:\\Users\\User\\Desktop\\새 폴더\\연구노트\\DRME"
},
"experiment_data_root": "C:\\Users\\User\\Desktop\\새 폴더\\연구노트",
"uses_g_drive": false
```

스크립트는 시작 시 이 값을 읽어 repo 기본값(G:)을 **덮어씀**.

### 7.3 에이전트가 할 일

- **G: / SecuYouSB 언급·설정 금지** (은규 PC)
- DRM/DRME 폴더가 생기면 `machine_profile.json` 에 경로만 추가
- repo `REACTION_ROOTS` 기본값(G:)을 은규 PC에 **무단 적용 금지**

**완료 기준:** 연구노트 `DRE` 아래에 스크립트 3단계가 새 실험 하위 폴더 생성 가능.

---

## 8. Phase 6 — GC1 CALIB (repo에 이미 반영됨)

`data_pc/촉매 반응 계산.py` (2026-06 은규 표준가스):

- `GC1_CALIB_READY = True`
- 교정곡선 `Area = k·ppm` → `GC1_CALIB[k] = k`

| 성분 | k |
|------|---|
| H2 | 0.20661 |
| CO | 0.01334 |
| CO2 | 0.0168 |
| CH4 | 0.14741 |
| C2H6 | 0.29259 |
| C2H4 | 0.30084 |

**은규 PC 할 일:** `git pull` → `Copy-Item` 으로 운영본 갱신. **CALIB 재입력 불필요** (값 변경 시에만 수정).

RT 검증(선택): [`deploy/STEP7_gc1_calib.md`](../deploy/STEP7_gc1_calib.md) §7.2 — `scripts/extract_gc1_rt_from_xlsx.py`

---

## 9. Phase 7 — 계산만 테스트 (`--no-archive`)

연구노트·Origin 없이 2단계만:

```powershell
# GC1 KCH xlsx를 inbox에 넣거나
python "$env:USERPROFILE\gc-data-pc\촉매 반응 계산.py" --manual
# 경로 입력

# 또는 inbox에 xlsx + 메일 연동 테스트
python "$env:USERPROFILE\gc-data-pc\촉매 반응 계산.py" --no-archive
```

**PASS 기준:**

- 장비 판별 `GC1` (GC2/GC3 혼동 없음)
- `gc-data-pc\PEG\processed\*_GC1_DRE_계산완료.xlsx` (또는 DRM) 생성
- 수율/전환율 수치가 수동 계산과 대략 일치

**연구노트 경로 없을 때:** 2단계까지는 됨. `PEG\processed\`에 사본 남음.

---

## 10. Phase 8 — Origin + 연구노트 전체 파이프라인 (E2E)

상세: [`deploy/STEP8_e2e.md`](../deploy/STEP8_e2e.md)

### 10.1 사전 점검

```powershell
cd $env:USERPROFILE\chemstation-gc-automation
powershell -File scripts\verify_e2e_prerequisites.ps1
```

| 항목 | 은규 PC |
|------|---------|
| `Desktop\새 폴더\연구노트\DRE` | 필수 (3~4단계) — **G: / SecuYouSB 불필요** |
| `pip install originpro` | Origin 연동 시 |
| Origin GUI 1회 실행 | COM/라이선스 |

### 10.2 전체 실행

```powershell
python "$env:USERPROFILE\gc-data-pc\촉매 반응 계산.py"
```

또는 Cursor 규칙: 「진행」「시작」「해봐」→ 위 스크립트 실행.

**PASS:** inbox → processed → **연구노트** 새 폴더 → `.opju` 시료 열 추가.

---

## 11. 일상 운영 (세팅 완료 후)

### 11.1 은규 사용자 말버릇 → 작업 시작 (LLM/에이전트)

은규 사용자는 기술 맥락 없이 **짧게만** 말함. 아래는 모두 **작업 시작**으로 해석:

| 사용자가 말함 | 에이전트 동작 |
|---------------|----------------|
| `진행`, `시작`, `해봐`, `작업`, `돌려`, `go` … | **되묻지 않고** 전체 파이프라인 실행 |
| (명시 없음) | 아래 python 명령과 동일 |

판별: `data_pc/data_pc_request.py` · 규칙 `.cursor/rules/eungyu-pc-initiation.mdc`

```powershell
python "$env:USERPROFILE\gc-data-pc\촉매 반응 계산.py"
```

또는 `deploy\gc_data_pc_run.bat` (동일)

**파이프라인:** 메일(IMAP) → 수율/전환율 계산 → 연구노트 실험 폴더 → Origin

실증·세부 확인은 **사용자가 직접** 함. 에이전트는 실행 + 결과 요약만.

### 11.2 기타 상황

| 상황 | 은규 PC에서 |
|------|-------------|
| GC1 실험 후 데이터 반영 | GC1 장비가 메일 발송 → Cursor에 「진행」 등 또는 위 스크립트 |
| 메일 없이 xlsx만 | `--manual` |
| 계산만 (Origin 건너뛰기) | `--no-archive` |
| 코드 업데이트 | `git pull` → `Copy-Item` 운영본 |
| repo 수정 후 | `git pull` 먼저 → 수정 → push |

**은규 PC에서 돌리지 않음:** `gc_automation.py`, `GC1_감시시작.bat` (장비 PC)

---

## 12. 파일·경로 치트시트

| 용도 | 은규 PC 경로 |
|------|----------------|
| 메인 스크립트 | `%USERPROFILE%\gc-data-pc\촉매 반응 계산.py` |
| IMAP env | `%USERPROFILE%\gc-data-pc\gc_automation.env` |
| 메일 xlsx 수신 | `%USERPROFILE%\gc-data-pc\PEG\inbox\` |
| 계산 완료 사본 | `%USERPROFILE%\gc-data-pc\PEG\processed\` |
| PC 식별 | `%USERPROFILE%\gc-data-pc\PEG\machine_profile.json` |
| 일상 시작 배치 | `deploy\gc_data_pc_run.bat` → gc-data-pc 에 복사 가능 |
| Git repo | `%USERPROFILE%\chemstation-gc-automation\` |

| 용도 | GC1 **장비** PC (참고만) |
|------|-------------------------|
| Autochro 출력·메일 | `%USERPROFILE%\Desktop\박은규\` |
| 장비 env | `%USERPROFILE%\Desktop\박은규\gc_automation.env` |

---

## 13. 에이전트 행동 규칙 (요약)

### 온보딩 (최초)

사용자가 **「은규 PC야」「깃허브 줄게」** 만 말했을 때:

1. **되묻지 말고** 본 문서 Phase 1부터 상태 확인  
2. 미완료 Phase를 **순서대로** 진행 (명령 실행·파일 생성·검증)  
3. 실험 경로 — **연구노트** (`machine_profile.json`), G: **사용 안 함**  
4. 비밀번호를 Git에 commit **금지**  
5. `gc_automation.py` 는 이 PC에서 **실행·설정하지 않음**  
6. 막히면 **어느 Phase 몇 번**인지 보고하고, 필요한 사용자 입력(경로·앱비밀번호)만 질문  

### 일상 작업 (은규 사용자 말버릇)

사용자가 **「진행」「시작」「해봐」「작업」「돌려」「go」** 등 **맥락 없는 짧은 말**만 할 때:

1. **작업 시작**으로 해석 (`data_pc/data_pc_request.py`, `eungyu-pc-initiation.mdc`)  
2. **되묻지 말고** 즉시 실행:
   ```powershell
   python "$env:USERPROFILE\gc-data-pc\촉매 반응 계산.py"
   ```
3. 메일 → 계산 → 연구노트 → Origin 결과만 요약 보고  
4. 실증·세부 확인은 사용자가 직접 — 에이전트는 실행 담당
7. **일상 개시** — 「진행」「시작」「해봐」 등 짧은 말 → `eungyu-pc-initiation.mdc` 즉시 실행  

---

## 14. 관련 문서 색인

| 문서 | 내용 |
|------|------|
| **본 문서** | 은규 PC 마스터 체크리스트 |
| [`docs/DATA_PC_PATHS.md`](DATA_PC_PATHS.md) | 연구노트·경로 개별 설정 |
| [`docs/PC_NAMING.md`](PC_NAMING.md) | PC 명칭 |
| [`deploy/STEP6_data_pc_setup.md`](../deploy/STEP6_data_pc_setup.md) | .cursor 설치 |
| [`deploy/STEP7_gc1_calib.md`](../deploy/STEP7_gc1_calib.md) | GC1 CALIB·RT |
| [`deploy/STEP8_e2e.md`](../deploy/STEP8_e2e.md) | E2E |
| [`docs/GC1_장비PC_README.md`](GC1_장비PC_README.md) | 장비 PC (은규 PC 아님) |
| [`deploy/GC1_Cursor_핸드오프.md`](../deploy/GC1_Cursor_핸드오프.md) | GC1 장비 통합 |

---

## 15. 체크리스트 (인쇄·복사용)

```
[ ] Phase 1  git clone + pull
[ ] Phase 2  Desktop\.cursor\ + 촉매 반응 계산.py + --help
[ ] Phase 3  gc_automation.env (IMAP) + test_e2e_mail_auth.py
[ ] Phase 4  machine_profile.json (data_pc, 은규)
[ ] Phase 5  machine_profile 연구노트 경로 (G: 아님)
[ ] Phase 6  git pull → GC1_CALIB 운영본 동기화
[ ] Phase 7  --no-archive 계산 PASS
[ ] Phase 8  연구노트 + originpro + full pipeline E2E
[ ] 일상     GC1 메일 → 촉매 반응 계산.py
```

---

*작성: 차헌 PC — 은규 PC Cursor 인수인계용. GitHub `gjtuc/GC-auto` main.*
