# Step 6 — 은규 PC `Desktop\.cursor\` 설치

> PC 명칭: [`docs/PC_NAMING.md`](../docs/PC_NAMING.md) — **은규 PC** = 은규의 데이터 PC (GC1 장비 PC와 별개)

> **목표:** `data_pc/` 내용을 운영 경로에 배치하고, env·machine_profile·KCH 폴더를 준비한다.  
> **Step 6 범위:** 설치·검증까지만. CALIB/TIME(Step 7), E2E(Step 8)은 다음 단계.

---

## PC 역할 구분 (같은 물리 PC여도 OK)

| 역할 | machine_profile | env | 실행 스크립트 |
|------|-----------------|-----|---------------|
| GC1 장비 | `Desktop\박은규\machine_profile.json` (`gc1_pc`) | `Desktop\박은규\gc_automation.env` | repo `gc_automation.py --watch` |
| 은규 PC | `Desktop\.cursor\KCH\machine_profile.json` (`data_pc`) | `Desktop\.cursor\gc_automation.env` | `Desktop\.cursor\촉매 반응 계산.py` |

**GC1 장비 PC에서 `촉매 반응 계산.py` 실행 금지** (Origin·G: 환경 다름).

---

## 6.1 — 디렉터리 생성

```powershell
$base = "$env:USERPROFILE\Desktop\.cursor"
New-Item -ItemType Directory -Path "$base\KCH\inbox" -Force
New-Item -ItemType Directory -Path "$base\KCH\processed" -Force
```

**완료 기준:** `KCH\inbox`, `KCH\processed` 폴더 존재.

---

## 6.2 — repo → Desktop 복사

```powershell
cd C:\Users\User\chemstation-gc-automation
git pull

Copy-Item -LiteralPath "data_pc\촉매 반응 계산.py" -Destination "$env:USERPROFILE\Desktop\.cursor\" -Force
Copy-Item "data_pc\gc_automation.env.example" -Destination "$env:USERPROFILE\Desktop\.cursor\gc_automation.env.template" -Force
```

**완료 기준:** `Desktop\.cursor\촉매 반응 계산.py` 존재, repo `data_pc/` 와 동일 버전.

**업데이트 루틴:** repo에서 `data_pc/촉매 반응 계산.py` 가 바뀌면 `git pull` 후 위 Copy-Item 재실행.

---

## 6.3 — `gc_automation.env` (IMAP 전용)

`Desktop\.cursor\gc_automation.env` 생성 (Git 제외):

```ini
NAVER_EMAIL=은규_네이버메일@naver.com
NAVER_APP_PASSWORD=16자리_앱비밀번호
MAIL_TO=은규_네이버메일@naver.com
```

- GC1 장비 env(`Desktop\박은규\`)와 **같은 네이버 계정** 사용 가능 (발송·수신 동일).
- `GC_INSTANCE`, `CHEMSTATION_MODE` 등 장비용 키는 **넣지 않음**.

**완료 기준:** `NAVER_EMAIL`, `NAVER_APP_PASSWORD` 비어 있지 않음.

---

## 6.4 — `KCH\machine_profile.json`

템플릿: `deploy/machine_profile.template.data_pc.json`

```powershell
Copy-Item deploy\machine_profile.template.data_pc.json "$env:USERPROFILE\Desktop\.cursor\KCH\machine_profile.json"
# identifiers + paths 채우기 (Step 2 와 동일 UUID/MachineGuid)
```

필수 필드:

| 필드 | 값 예 (은규 PC) |
|------|----------------|
| `role` | `data_pc` |
| `identifiers.computer_name` | 은규 PC의 COMPUTERNAME (GC1 장비 PC와 다름) |
| `identifiers.smbios_uuid` | 은규 PC에서 조회한 UUID (GC1 장비 PC와 다름) |
| `paths.script_dir` | `C:\Users\User\Desktop\.cursor` |

**완료 기준:** `role` = `data_pc`, identifiers 채워짐.

---

## 6.5 — Python·스크립트 검증

```powershell
python -c "import pandas, numpy, dotenv"
python "$env:USERPROFILE\Desktop\.cursor\촉매 반응 계산.py" --help
powershell -File C:\Users\User\chemstation-gc-automation\scripts\verify_data_pc_setup.ps1
```

| 항목 | Step 6 필수 | Step 8 전 추가 |
|------|-------------|----------------|
| pandas, numpy, python-dotenv | ✅ | |
| `--help` 기동 | ✅ | |
| G: 드라이브 | — | SecuYouSB 로그인 |
| originpro | — | Origin 연동 시 |

**현재 GC1 장비 PC (2026-06-18):** core PASS, G: 미연결, originpro 미설치 → Step 6 OK, Step 8 전 해결.

---

## 6.6 — repo 스크립트·문서 (선택)

- `scripts/verify_data_pc_setup.ps1` — 위 점검 자동화
- `deploy/ROADMAP.md` Step 6 체크

---

## 6.7 — sync registry

은규 PC에서 repo pull/push 시:

```powershell
gc_git_pull.bat    # 시작
gc_git_status.bat  # deploy/SYNC_STATUS.md
```

동일 물리 PC(`DESKTOP-MBGSSME`)는 sync json 하나(`gc1_pc`)로 추적.  
차헌 PC 등 차헌 PC 등 별도 데이터 PC가 생기면 그 PC에서 `gc_git_pull.bat` 1회 → `DESKTOP-XXXX.json` 생성.

---

## Step 6 완료 체크리스트

- [x] `Desktop\.cursor\촉매 반응 계산.py`
- [x] `Desktop\.cursor\gc_automation.env` (IMAP)
- [x] `Desktop\.cursor\KCH\machine_profile.json` (`data_pc`)
- [x] `Desktop\.cursor\KCH\inbox\`, `processed\`
- [x] `python ... --help` 성공
- [ ] G: + originpro (Step 8)
- [ ] GC1 CALIB/TIME (Step 7)

---

## 다음: Step 7

`촉매 반응 계산.py` USER SETTINGS — GC1: [`deploy/STEP7_gc1_calib.md`](deploy/STEP7_gc1_calib.md)
