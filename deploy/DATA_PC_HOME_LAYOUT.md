# 데이터 PC 운영 폴더 레이아웃 (LLM/에이전트 참고)

> **목적:** `촉매 반응 계산.py` 가 **어느 로컬 폴더**에 설치되는지 PC별로 정리.  
> 실험 데이터는 `gc-data-pc` / `Desktop\.cursor`, **부가 파일(캐시·임시)** 은 `%USERPROFILE%\.cursor\gc-*` 아래.

---

## 1. 왜 폴더 위치가 PC마다 다른가

| 요구 | 은규 PC | 차헌 PC |
|------|---------|---------|
| 바탕화면 정리 | 바탕화면에 폴더 안 보이게 | 기존 `Desktop\.cursor` 유지 가능 |
| 사용자 혼동 방지 | `gc-data-pc` 이름으로 목적 명확 | — |
| Python 캐시·임시 | `%USERPROFILE%\.cursor\gc-python-cache` 등 | 동일 |
| Cursor IDE | `.cursor\` 루트는 IDE 설정 — **gc-* 하위만** GC 부가 파일 |

---

## 2. PC별 권장 script_dir (운영 루트)

| PC | script_dir (절대경로 예) | storage (PEG/KCH) |
|----|--------------------------|-------------------|
| **은규 PC** | `C:\Users\User\gc-data-pc\` | `PEG\` (Park Eungyu Gyu) |
| **차헌 PC** | `C:\Users\User\Desktop\.cursor\` | `KCH\` (Kim Chaheon) |

**script_dir** = `촉매 반응 계산.py` + `gc_automation.env` 가 있는 폴더.  
스크립트는 `SCRIPT_DIR = os.path.dirname(__file__)` 로 자동 인식.

---

## 3. 공통 하위 구조 (script_dir 기준)

```
{script_dir}\
├── 촉매 반응 계산.py       ← repo data_pc/ 에서 Copy-Item (git pull 후 갱신)
├── runtime_paths.py        ← 위와 함께 복사 (__pycache__ 리다이렉트)
├── gc_automation.env       ← 네이버 IMAP (Git 제외, .gitignore)
└── PEG\  또는  KCH\        ← 연구원 이니셜 폴더 (둘 중 하나)
    ├── inbox\              ← [1단계] 메일 첨부 xlsx
    ├── processed\          ← [2단계] 계산 완료 사본
    └── machine_profile.json← PC 식별 + reaction_roots (Git 제외)

%USERPROFILE%\.cursor\       ← [LLM] 실험과 무관한 부가 파일만 (IDE 설정과 gc-* 로 분리)
├── gc-python-cache\        ← Python __pycache__ / .pyc (runtime_paths.py)
└── gc-runtime-temp\        ← 스크립트 임시 파일 (필요 시)
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
