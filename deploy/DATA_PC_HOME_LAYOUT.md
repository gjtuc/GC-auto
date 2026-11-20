# 데이터 PC 운영 폴더 레이아웃 (LLM/에이전트 참고)

> **목적:** `촉매 반응 계산.py` 가 **어느 로컬 폴더**에 설치되는지 PC별로 정리.  
> **부가 파일(캐시·임시)** 은 `%USERPROFILE%\.cursor\gc-*` 아래 (실험 데이터·코드와 분리).

---

## 1. 왜 폴더 위치가 PC마다 다른가

| 요구 | 은규 PC | 차헌 PC | 차완 PC |
|------|---------|---------|---------|
| 바탕화면 정리 | 바탕화면에 폴더 안 보이게 | **repo 안**에 모아 IDE/레거시 `.cursor` 잔여와 분리 | `gc-data-pc-chawan` |
| 사용자 혼동 방지 | `gc-data-pc` 이름으로 목적 명확 | `repos\GC-auto\data_pc\` 한곳 | Downloads·kier 경로 문서화 |
| Python 캐시·임시 | `%USERPROFILE%\.cursor\gc-python-cache` 등 | 동일 | 동일 |
| Cursor IDE | `%USERPROFILE%\.cursor\` = IDE — GC 운영과 섞지 말 것 | 동일 | 동일 |

**차헌 (2026-11 합의):** `D:\.cursor\KCH`, `D:\.cursor\data_pc_origin` 처럼 **repo 밖 복제본**을 두지 않는다.  
코드·KCH·env 모두 **`GC-auto` clone 안 `data_pc\`** 로 정리. (`inbox`/`processed`/`env`/`machine_profile` 은 `.gitignore`)

---

## 2. PC별 권장 script_dir (운영 루트)

| PC | script_dir (절대경로 예) | storage (PEG/KCH) |
|----|--------------------------|-------------------|
| **은규 PC** | `%USERPROFILE%\gc-data-pc\` | `PEG\` (Park Eungyu Gyu) |
| **차헌 PC** | `{GC-auto clone}\data_pc\` 예: `D:\.cursor\repos\GC-auto\data_pc\` | `KCH\` (Kim Chaheon) |
| **차완 PC** | `%USERPROFILE%\gc-data-pc-chawan\` | `KCH\` (processed·profile) |

**script_dir** = `촉매 반응 계산.py` + `gc_automation.env` 가 있는 폴더.  
스크립트는 `SCRIPT_DIR = os.path.dirname(__file__)` 로 자동 인식.

### 차헌 — repo 안 레이아웃 (목표)

```
D:\.cursor\repos\GC-auto\          ← git clone (코드)
└── data_pc\                       ← script_dir
    ├── 촉매 반응 계산.py
    ├── runtime_paths.py
    ├── data_pc_origin\            ← 패키지 (git)
    ├── data_pc_runtime\           ← 패키지 (git)
    ├── gc_automation.env          ← 로컬만 (.gitignore)
    └── KCH\
        ├── inbox\                 ← 로컬 (.gitignore)
        ├── processed\             ← 로컬 (.gitignore)
        └── machine_profile.json   ← 로컬 (.gitignore)
```

레거시 (정리 대상, 신규 사용 금지): `D:\.cursor\KCH`, `D:\.cursor\gc-home`, `D:\.cursor\data_pc_origin` (repo 밖 복사본).

---

## 3. 공통 하위 구조 (script_dir 기준)

```
{script_dir}\
├── 촉매 반응 계산.py       ← 차헌: repo 안 파일 직접 실행 / 은규·차완: Copy-Item
├── runtime_paths.py
├── data_pc_origin\         ← (차헌 repo script_dir 에 이미 포함)
├── data_pc_runtime\
├── gc_automation.env       ← 네이버 IMAP (Git 제외)
└── PEG\  또는  KCH\
    ├── inbox\
    ├── processed\
    └── machine_profile.json

%USERPROFILE%\.cursor\gc-python-cache\   ← __pycache__
%USERPROFILE%\.cursor\gc-runtime-temp\   ← 임시
```

### 차헌 — 레거시 → repo 이전 (한 번)

```powershell
$repo = "D:\.cursor\repos\GC-auto"   # 또는 이 PC의 GC-auto clone
$dst  = Join-Path $repo "data_pc\KCH"
New-Item -ItemType Directory -Path "$dst\inbox","$dst\processed" -Force | Out-Null
# 데이터만 복사 (코드 패키지 루트 복제본은 복사하지 않음)
Copy-Item -Force "D:\.cursor\KCH\machine_profile.json" "$dst\" -ErrorAction SilentlyContinue
Copy-Item -Force "D:\.cursor\KCH\inbox\*" "$dst\inbox\" -ErrorAction SilentlyContinue
Copy-Item -Force "D:\.cursor\KCH\processed\*" "$dst\processed\" -ErrorAction SilentlyContinue
Copy-Item -Force "D:\.cursor\gc_automation.env" (Join-Path $repo "data_pc\gc_automation.env") -ErrorAction SilentlyContinue
# 이후 실행: python "$repo\data_pc\촉매 반응 계산.py"
# 확인 후 D:\.cursor\KCH · gc-home · 루트 data_pc_* 복제본 삭제 가능
```

### [LLM] 파일 역할

| 파일/폴더 | Git | 역할 |
|-----------|-----|------|
| `촉매 반응 계산.py` | ✅ repo | 메일→계산→실험폴더→Origin 파이프라인 |
| `gc_automation.env` | ❌ | `NAVER_EMAIL`, `NAVER_APP_PASSWORD` |
| `PEG/inbox` | ❌ | GC1 등 장비 PC가 보낸 KCH **원본** xlsx |
| `PEG/processed` | ❌ | 수율/전환율 계산 완료 xlsx (검토용) |
| `machine_profile.json` | ❌ | `role=data_pc`, `reaction_roots`, `experiment_data_root` |
| `.cursor/gc-python-cache` | ❌ | Python 캐시 — **gc-data-pc에 __pycache__ 생성 안 함** |
| `.cursor/gc-runtime-temp` | ❌ | 런타임 임시 — 실험 데이터 아님 |

---

## 4. 은규 PC — gc-data-pc 최초 설치 (PowerShell)

```powershell
# 1) 운영 폴더 생성
$home = "$env:USERPROFILE\gc-data-pc"
New-Item -ItemType Directory -Path "$home\PEG\inbox" -Force
New-Item -ItemType Directory -Path "$home\PEG\processed" -Force

# 2) repo에서 스크립트 복사 (pull 후)
cd $env:USERPROFILE\chemstation-gc-automation
git pull
Copy-Item -LiteralPath "data_pc\촉매 반응 계산.py" -Destination $home -Force
Copy-Item -LiteralPath "data_pc\runtime_paths.py" -Destination $home -Force

# 3) env — deploy 참고, 값은 로컬만
Copy-Item "data_pc\gc_automation.env.example" "$home\gc_automation.env"

# 4) machine_profile — deploy/machine_profile.eungyu.reference.json 참고
Copy-Item deploy\machine_profile.eungyu.reference.json "$home\PEG\machine_profile.json"
# → reaction_roots 를 은규 PC 탐색기 실측 경로로 수정
```

### 바탕화면 `.cursor` 에 있던 파일 이전

```powershell
# 기존 Desktop\.cursor → gc-data-pc 로 한 번만 이전
if (Test-Path "$env:USERPROFILE\Desktop\.cursor") {
  New-Item -ItemType Directory -Path "$env:USERPROFILE\gc-data-pc" -Force
  Move-Item -LiteralPath "$env:USERPROFILE\Desktop\.cursor\*" -Destination "$env:USERPROFILE\gc-data-pc\" -Force
  Remove-Item -LiteralPath "$env:USERPROFILE\Desktop\.cursor" -Recurse -Force
}
```

---

## 5. 은규 PC 실험 저장 경로 (연구노트)

은규 PC는 G: USB 대신 **로컬 연구노트** 사용 (2026-06 기준 DRE만 운영, DRM/DRME 추후).

`PEG\machine_profile.json` 예:

```json
{
  "reaction_roots": {
    "DRE": "C:\\Users\\User\\Desktop\\새 폴더\\연구노트\\DRE",
    "DRM": "C:\\Users\\User\\Desktop\\새 폴더\\연구노트\\DRM",
    "DRME": "C:\\Users\\User\\Desktop\\새 폴더\\연구노트\\DRME"
  },
  "experiment_data_root": "C:\\Users\\User\\Desktop\\새 폴더\\연구노트"
}
```

스크립트는 시작 시 이 값을 읽어 repo 기본값(G:)을 **오버라이드**합니다.

---

## 6. 장비 PC 폴더와 혼동 금지 (LLM 체크리스트)

| 경로 | PC | 스크립트 |
|------|-----|----------|
| `Desktop\박은규\` | GC1 **장비** | gc_automation.py |
| `Desktop\KCH\` | GC2/GC3 **장비** | gc_automation.py |
| `gc-data-pc\PEG\` | **은규** 데이터 PC | 촉매 반응 계산.py |
| `Desktop\.cursor\KCH\` | **차헌** 데이터 PC | 촉매 반응 계산.py |

---

## 7. 관련 문서

- `docs/은규PC_Cursor_시작.md` — 은규 PC 마스터 체크리스트  
- `docs/DATA_PC_PATHS.md` — reaction_roots 상세  
- `docs/PC_NAMING.md` — PC 명칭  
- `deploy/STEP6_data_pc_setup.md` — 차헌 PC (Desktop\.cursor) 설치
