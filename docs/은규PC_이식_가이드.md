# 은규 PC — 이식 가이드 (차헌 PC → gc-data-pc)

> **한 줄 요약:** GitHub `gjtuc/GC-auto` 의 `data_pc/` 를 `%USERPROFILE%\gc-data-pc\` 로 복사하고,  
> `uses_g_drive: false` 로 **G:/Wi‑Fi 게이트 없이** 15초 메일 폴링 supervisor 를 켠다.

**Cursor 트리거:** 사용자가 「**이식 작업해**」「이식해」「은규 PC에서 이식 작업해」만 말해도  
에이전트는 **본 문서 + `.cursor/rules/eungyu-pc-migration.mdc`** 를 읽고 아래를 **되묻지 않고** 진행한다.

---

## 0. 차헌 PC vs 은규 PC (혼동 금지)

| | **차헌 PC** (김차헌 데이터 PC) | **은규 PC** (박은규 데이터 PC) |
|--|-------------------------------|-------------------------------|
| script_dir | `Desktop\.cursor\` | `%USERPROFILE%\gc-data-pc\` |
| storage | `KCH\` | `PEG\` |
| 실험 저장 | G: (`SecuYouSB`) | 로컬 `연구노트` |
| supervisor 게이트 | **G: 열림** 때만 파이프라인 | **게이트 없음** (항상 인터넷) |
| Wi‑Fi 게이트 | 끔 | 끔 |
| 장비 스크립트 | — | `gc_automation.py` **실행 금지** (GC1 장비 PC) |

**이 문서는 은규 PC 이식 전용.** 차헌 PC `Desktop\.cursor\` 를 덮어쓰지 않는다.

---

## 1. 이식 후 목표 상태

```
%USERPROFILE%\gc-data-pc\
├── 촉매 반응 계산.py          ← 메일 → 계산 → 연구노트 → Origin
├── runtime_paths.py
├── data_pc_runtime\           ← supervisor (15초 폴링)
├── data_pc_origin\            ← Origin COM
├── data_pc_watch.py           ← (레거시 watch, supervisor 권장)
├── gc_automation.env          ← IMAP 계정 (Git 제외)
├── gc_data_pc_run.bat
└── PEG\
    ├── inbox\
    ├── processed\
    └── machine_profile.json   ← uses_g_drive: false 필수
```

supervisor 동작 (`python -m data_pc_runtime`):

1. 15초마다 `run_once`
2. Wi‑Fi / G: 게이트 **건너뜀** (`uses_g_drive: false`)
3. 쿨다운(기본 10분)만 적용 후 메일·파이프라인 실행

---

## 2. 자동 이식 (권장)

### 2.1 사전 조건

- [ ] Python 3.10+ (`python --version`)
- [ ] `pip install pandas openpyxl python-dotenv numpy`
- [ ] Git

### 2.2 명령 (에이전트가 실행)

```powershell
# repo
cd $env:USERPROFILE
if (-not (Test-Path chemstation-gc-automation)) {
  git clone https://github.com/gjtuc/GC-auto.git chemstation-gc-automation
}
cd chemstation-gc-automation
git pull origin main

# 이식
powershell -NoProfile -ExecutionPolicy Bypass -File scripts\port_eungyu_data_pc.ps1
```

### 2.3 스크립트가 하는 일

| 단계 | 내용 |
|------|------|
| 폴더 생성 | `gc-data-pc\PEG\inbox`, `processed` |
| 복사 | `data_pc\*.py`, `data_pc_runtime\`, `data_pc_origin\` |
| 배치 | `deploy\gc_data_pc_run.bat` → gc-data-pc |
| env | 없으면 `deploy/gc_automation.env.eungyu.template` → `gc_automation.env` |
| profile | 없으면 `deploy/machine_profile.eungyu.reference.json` → `PEG\machine_profile.json` |

---

## 3. 수동 설정 (반드시 로컬 확인)

### 3.1 `gc_automation.env`

템플릿: `deploy/gc_automation.env.eungyu.template`

```ini
NAVER_EMAIL=은규_네이버@naver.com
NAVER_APP_PASSWORD=16자리_앱비밀번호
MAIL_TO=은규_네이버@naver.com

# 은규 PC: 이더넷 상시 연결 — Wi‑Fi·G: 게이트 없음
DATA_PC_SKIP_WIFI_CHECK=1
DATA_PC_WATCH_INTERVAL_SEC=15
DATA_PC_AUTO_MAIL_COOLDOWN_MINUTES=10
DATA_PC_SKIP_ORIGIN=0
```

GC1 장비 PC `MAIL_TO` 가 위 `NAVER_EMAIL` 과 **같아야** 메일이 도착한다.

### 3.2 `PEG\machine_profile.json`

```json
{
  "role": "data_pc",
  "label": "은규 PC",
  "uses_g_drive": false,
  "experiment_data_root": "C:\\Users\\User\\Desktop\\새 폴더\\연구노트",
  "reaction_roots": {
    "DRE": "C:\\Users\\User\\Desktop\\새 폴더\\연구노트\\DRE"
  }
}
```

- **`uses_g_drive: false`** — supervisor 가 G: 대기(`waiting_gdrive`)하지 않음  
- 경로는 **탐색기 실측** — repo `REACTION_ROOTS` 기본값(G:) 복사 금지

---

## 4. 검증

```powershell
$home = "$env:USERPROFILE\gc-data-pc"

# 1) 스크립트
python "$home\촉매 반응 계산.py" --help

# 2) 게이트·경로
cd $home
python -m data_pc_runtime.verify --script-dir $home

# 3) supervisor
python -m data_pc_runtime --restart --script-dir $home
Start-Sleep -Seconds 20
Get-Content "$home\PEG\.data_pc_runtime_status.json"
```

**PASS 기준:**

| 항목 | 기대값 |
|------|--------|
| `--help` | exit 0 |
| verify | `check_gdrive: false` (uses_g_drive) |
| status | `alive: true`, `status_code: ready` 또는 `pipeline_done` |
| 게이트 | `waiting_gdrive` **아님** |

### 4.1 계산만 테스트 (연구노트·Origin 전)

```powershell
python "$home\촉매 반응 계산.py" --no-archive
```

---

## 5. 일상 운영 (이식 완료 후)

| 사용자 말 | 에이전트 |
|-----------|----------|
| `진행`, `시작`, `해봐` | `촉매 반응 계산.py` 1회 실행 — `eungyu-pc-initiation.mdc` |
| `이식 작업해` | 본 가이드 전체 — `eungyu-pc-migration.mdc` |
| 코드 업데이트 | `git pull` → `port_eungyu_data_pc.ps1` 재실행 |

---

## 6. 코드 참고 (게이트 분기)

| 파일 | 설명 |
|------|------|
| `data_pc_runtime/layer1_profile.py` | `machine_profile.uses_g_drive` → G: 게이트 on/off |
| `data_pc_runtime/layer2_gates.py` | L2-3.5 G: 게이트, L2-1 Wi‑Fi 게이트 |
| `data_pc_runtime/layer3_job.py` | `load_gate_config()` — env + profile |

은규 PC: `resolve_check_gdrive()` → `False` → 15초마다 메일만 확인.

---

## 7. 문제 해결

| 증상 | 확인 |
|------|------|
| `waiting_gdrive` 계속 | `machine_profile` 에 `uses_g_drive: false` 있는지 |
| Origin 실패 (0.3초) | supervisor 가 `pythonw` 인지 — `o9_facade.py` stdin 가드 포함 여부 (`git pull`) |
| 메일 반복 처리 | `.processed_mail_ids.txt` · `force_done_log` 수정본 이식 여부 |
| `ModuleNotFoundError: data_pc_runtime` | `port_eungyu_data_pc.ps1` 재실행 |

---

## 8. 체크리스트 (에이전트용)

```
[ ] git pull (main)
[ ] port_eungyu_data_pc.ps1
[ ] gc_automation.env (NAVER_*)
[ ] PEG\machine_profile.json (uses_g_drive: false, 연구노트 경로)
[ ] --help OK
[ ] data_pc_runtime.verify OK
[ ] supervisor restart OK
[ ] status alive, not waiting_gdrive
```

---

*작성: 차헌 PC — 은규 PC Cursor 이식용. GitHub `gjtuc/GC-auto`.*
