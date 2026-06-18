# PC 명칭 규칙 (연구실 공통)

> **모든 문서·주석·machine_profile 에 이 표기를 사용합니다.**

## 연구원

| 이름 | 담당 GC | 역할 |
|------|---------|------|
| **은규** | GC1 | GC1 사용자 |
| **차헌** | GC2, GC3 | GC2/GC3 사용자 |

## PC 종류 (4종)

| 표기 | 소유 | 역할 | env / 출력 | 실행 |
|------|------|------|------------|------|
| **GC1 장비 PC** | 은규 | Autochro 옆 장비 | `Desktop\박은규\gc_automation.env` | `gc_automation.py` |
| **은규 PC** | 은규 | 업무·계산·Origin | `Desktop\.cursor\gc_automation.env` | `촉매 반응 계산.py` |
| **GC2/GC3 장비 PC** | 차헌 | ChemStation 옆 장비 | `Desktop\KCH\gc_automation.env` | `gc_automation.py` |
| **차헌 PC** | 차헌 | 업무·계산·Origin | `Desktop\.cursor\gc_automation.env` | `촉매 반응 계산.py` |

## 오해 금지

| 잘못된 표기 | 올바른 표기 |
|-------------|-------------|
| 「차헌 PC」= ChemStation 장비 | **GC2/GC3 장비 PC** |
| 「은규 PC」= Autochro 장비 | **GC1 장비 PC** |
| 「데이터 PC-차헌」 | **차헌 PC** |
| 「데이터 PC-은규」 | **은규 PC** |
| `gc_profiles` gc2 주석의 「차헌 PC」 | **GC2 장비 PC** (코드 주석도 동일) |

## machine_profile / sync registry

| PC | `role` | 참고 템플릿 |
|----|--------|-------------|
| GC1 장비 PC | `gc1_pc` | `deploy/machine_profile.template.gc1.json` |
| 은규 PC | `data_pc` | `deploy/machine_profile.template.data_pc.json` |
| GC2/GC3 장비 PC | `gc2_pc` / `gc3_pc` | `deploy/machine_profile.template.gc2.json` |
| 차헌 PC | `data_pc` | `deploy/machine_profile.reference.chaheon.json` |

## EXPECTED_PCS (GitHub sync)

| pc_id (예) | label |
|------------|-------|
| `DESKTOP-MBGSSME` | 은규 — GC1 장비 PC |
| `(은규 PC COMPUTERNAME)` | 은규 PC |
| `GC8860` | 차헌 — GC2/GC3 장비 PC |
| `DESKTOP-BFMLJ9J` | 차헌 PC |

## 파이프라인 한 줄

- **장비 PC** → KCH 원본 엑셀 → 메일 **발송** (수신: 본인 **데이터 PC**)
- **은규 PC** / **차헌 PC** → 메일 **수신** → 계산 → G: → Origin

**GitHub:** 코드 수정 후 자동 push — [`GIT_AUTO_SYNC.md`](GIT_AUTO_SYNC.md)

---

## 자주 헷갈리는 것 (코드·경로)

### 1. `KCH` 폴더 이름이 두 군데

| 경로 | PC | 용도 |
|------|-----|------|
| `Desktop\KCH\` | GC2/GC3 **장비** PC | gc_automation.py 출력 xlsx·watch 상태 |
| `Desktop\.cursor\KCH\` | **은규 PC** 또는 **차헌 PC** | inbox/processed, machine_profile |

이름만 같을 뿐 **완전히 다른 PC·다른 스크립트**입니다.

### 2. `gc_automation.env` 도 두 종류

| 경로 | 실행 스크립트 |
|------|----------------|
| `Desktop\박은규\` 또는 `Desktop\KCH\` | `gc_automation.py` (**장비**) |
| `Desktop\.cursor\` | `촉매 반응 계산.py` (**은규/차헌 PC**) |

`gc_profiles.candidate_env_dirs()` 는 **장비 쪽만** 탐색합니다 (`.cursor` 는 보지 않음).

### 3. `gc_profiles` / `GC_INSTANCE`

- `gc1` / `gc2` / `gc3` = **어느 GC 장비**인지 (장비 PC 분기)
- `data_pc` = machine_profile `role` (은규 PC·차헌 PC)
- **혼동 금지:** `GC_INSTANCE=gc2` 인 PC가 「차헌 PC」라는 뜻이 **아님** → GC2 **장비** PC

### 4. 같은 사람이라도 PC는 최대 2대

은규: GC1 장비 PC + 은규 PC  
차헌: GC2/GC3 장비 PC + 차헌 PC  

한 대에 `박은규`와 `KCH` env를 **동시에** 두지 마세요 (프로필 자동 판별 오류).

### 5. 코드 기본값은 차헌 **장비** 쪽

`gc_config.py` 의 `EXCEL_OUTPUT_DIR`, `TARGET_EMAIL` 등은 GC2/GC3 장비 PC 기본값입니다.  
GC1 장비 PC는 env로 덮습니다. 은규 PC/차헌 PC는 이 모듈을 쓰지 않습니다.
