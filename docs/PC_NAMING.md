# PC 명칭 규칙 (연구실 공통)

> **모든 문서·주석·machine_profile 에 이 표기를 사용합니다.**

## 실험실 자리 · GC 번호 (중요)

예전 배치: **GC1 · GC2 · GC3**  
은규 Autochro 장비를 **3번 오른쪽(4번 자리)** 으로 옮김 → 표기 **GC4**  
비운 **1번 자리**에는 나중에 **새 GC + 새 PC**가 들어와 **GC1**이 됩니다.

| 구분 | 내용 |
|------|------|
| **바뀐 것** | 부르는 이름만 (자리 번호) GC1 → **GC4** |
| **안 바뀐 것** | 같은 PC, 같은 Autochro 장비, 같은 `gc_automation.py` 파이프라인 |
| **코드** | 패키지 `gc1_runtime/`·모듈 `gc_gc1.py` 등 **파일명 유지**. 토큰 `gc1`/`gc4`·role `gc1_pc`/`gc4_pc` 는 **동의어** (`gc_identity.py`) |

## 연구원

| 이름 | 담당 GC | 역할 |
|------|---------|------|
| **은규** | **GC4** (구 GC1) | Autochro 장비 사용자 |
| **차헌** | GC2, GC3 | GC2/GC3 사용자 (메일 `kimcha0809@naver.com`) |
| **차완** | GC2 (공유) | GC2 장비 PC 공동 사용 (메일 `yangcw0103@kier.re.kr`) · **차완 PC** = 별도 데이터 PC |

GC2는 차헌·차완이 **같은 장비 PC**를 씀. Cursor「차완」「차헌」으로 작업자 전환 → `gc_operator.py` / `.gc_operator.json`.

**차완 PC** (`DESKTOP-N89C874`) = GC8860과 **별개** 업무 PC. Downloads xlsx → `Desktop\kier\촉매 반응 결과` → Origin. [`docs/차완PC_Cursor_시작.md`](차완PC_Cursor_시작.md)

## PC 종류 (4종)

| 표기 | 소유 | 역할 | env / 출력 | 실행 |
|------|------|------|------------|------|
| **GC4 장비 PC** (구 GC1) | 은규 | Autochro 옆 장비 | `Desktop\박은규\gc_automation.env` | `gc_automation.py` |
| **은규 PC** | 은규 | 업무·계산·Origin | `gc-data-pc\` 또는 `Desktop\.cursor\` | `촉매 반응 계산.py` |
| **GC2/GC3 장비 PC** | 차헌·차완 | ChemStation 옆 장비 | `Desktop\KCH\gc_automation.env` | `gc_automation.py` |
| **차헌 PC** | 차헌 | 업무·계산·Origin | `Desktop\.cursor\gc_automation.env` | `촉매 반응 계산.py` |
| **차완 PC** | 차완 | 업무·계산·Origin (KIER) | `gc-data-pc-chawan\` | `scripts/run_gc_chawan.py` |

## 오해 금지

| 잘못된 표기 | 올바른 표기 |
|-------------|-------------|
| 「차헌 PC」= ChemStation 장비 | **GC2/GC3 장비 PC** |
| 「은규 PC」= Autochro 장비 | **GC4 장비 PC** |
| 「GC1 장비 PC」(현재) | **GC4 장비 PC** (구칭이 GC1). 앞으로의 GC1 = **새** 장비용 |
| 「데이터 PC-차헌」 | **차헌 PC** |
| 「데이터 PC-은규」 | **은규 PC** |
| `gc_profiles` 의 「차헌 PC」 | **GC2 장비 PC** (코드 주석도 동일) |

## machine_profile / sync registry

| PC | `role` | 참고 템플릿 |
|----|--------|-------------|
| GC4 장비 PC | `gc4_pc` (레거시 `gc1_pc` 동의어) | `deploy/machine_profile.template.gc4.json` |
| 은규 PC | `data_pc` | `deploy/machine_profile.template.data_pc.json` |
| GC2/GC3 장비 PC | `gc2_pc` / `gc3_pc` | `deploy/machine_profile.template.gc2.json` |
| GC8860 (GC2 장비) | `gc2_pc` | `deploy/machine_profile.reference.gc8860.json` |
| 차헌 PC | `data_pc` | `deploy/machine_profile.reference.chaheon.json` · env: `deploy/gc_automation.env.chaheon.example` |
| **차완 PC** | `data_pc` | `deploy/machine_profile.reference.chawan.json` · `deploy/machine_profile.template.chawan_data_pc.json` |

## EXPECTED_PCS (GitHub sync)

| pc_id (예) | label |
|------------|-------|
| `DESKTOP-MBGSSME` | 은규 — **GC4** 장비 PC (구 GC1) |
| `(은규 PC COMPUTERNAME)` | 은규 PC |
| `GC8860` | 차헌 — GC2/GC3 장비 PC |
| `DESKTOP-BFMLJ9J` | 차헌 PC |
| `DESKTOP-N89C874` | **차완 PC** (Downloads → kier) |

## 파이프라인 한 줄

- **장비 PC** → KCH 원본 엑셀 → 메일 **발송** (수신: 본인 **데이터 PC**)
- **은규 PC** / **차헌 PC** → 메일 **수신** → 계산 → G: 또는 연구노트 → Origin
- **차완 PC** → Downloads xlsx → 계산 → `kier\촉매 반응 결과` → Origin

**GitHub:** 코드 수정 후 자동 push — [`GIT_AUTO_SYNC.md`](GIT_AUTO_SYNC.md)

---

## 자주 헷갈리는 것 (코드·경로)

### 1. `KCH` / `PEG` 폴더 이름

| 경로 | PC | 용도 |
|------|-----|------|
| `Desktop\KCH\` | GC2/GC3 **장비** PC | gc_automation.py 출력 xlsx·watch 상태 |
| `gc-data-pc\PEG\` | **은규 PC** (데이터) | inbox/processed, machine_profile — **PEG** = Park Eungyu Gyu |
| `Desktop\.cursor\KCH\` | **차헌 PC** (데이터) | inbox/processed, machine_profile |

은규 PC는 바탕화면 대신 `%USERPROFILE%\gc-data-pc\` 사용 (`deploy/DATA_PC_HOME_LAYOUT.md`).  
장비 PC `Desktop\KCH` 와 데이터 PC `gc-data-pc\PEG`·`Desktop\.cursor\KCH` 는 **완전히 다른 PC·다른 스크립트**입니다.

### 2. `gc_automation.env` 도 두 종류

| 경로 | 실행 스크립트 |
|------|----------------|
| `Desktop\박은규\` 또는 `Desktop\KCH\` | `gc_automation.py` (**장비**) |
| `gc-data-pc\` (은규) 또는 `Desktop\.cursor\` (차헌) | `촉매 반응 계산.py` (**데이터 PC**) |

`gc_profiles.candidate_env_dirs()` 는 **장비 쪽만** 탐색합니다 (`.cursor` 는 보지 않음).

### 3. `gc_profiles` / `GC_INSTANCE`

- `gc4` (또는 레거시 `gc1`) / `gc2` / `gc3` = **어느 GC 장비**인지 (장비 PC 분기)
- `data_pc` = machine_profile `role` (은규 PC·차헌 PC)
- **혼동 금지:** `GC_INSTANCE=gc2` 인 PC가 「차헌 PC」라는 뜻이 **아님** → GC2 **장비** PC

### 4. 같은 사람이라도 PC는 최대 2대

은규: **GC4** 장비 PC + 은규 PC  
차헌: GC2/GC3 장비 PC + 차헌 PC  

한 대에 `박은규`와 `KCH` env를 **동시에** 두지 마세요 (프로필 자동 판별 오류).

### 5. 코드 기본값은 차헌 **장비** 쪽

`gc_config.py` 의 `EXCEL_OUTPUT_DIR`, `TARGET_EMAIL` 등은 GC2/GC3 장비 PC 기본값입니다.  
GC4 장비 PC는 env로 덮습니다. 은규 PC/차헌 PC는 이 모듈을 쓰지 않습니다.

### 6. 내부 패키지명이 `gc1_*` 인 이유

자리 이름만 GC4로 바꿈. **대규모 폴더 rename 없음.**  
동작 판별은 `gc_identity.is_autochro_mode()` / `is_autochro_instance()` 가 `gc1`·`gc4` 둘 다 인정합니다.
