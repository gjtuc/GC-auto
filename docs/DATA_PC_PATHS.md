# 데이터 PC — 실험 파일 저장 경로 (연구원별 개별 설정)

> **대상:** 은규 PC·차헌 PC의 Cursor / 에이전트  
> **핵심:** repo에 적힌 G: 경로는 **차헌 PC 기준 예시**일 수 있음. **은규 PC는 은규가 쓰는 폴더 위치를 직접 확인한 뒤** 맞춰야 함.

---

## 1. 왜 사람마다 다르나

| 이유 | 설명 |
|------|------|
| 연구원마다 PC·습관이 다름 | 실험 결과를 G:·로컬에 **각자 방식**으로 정리해 둠 |
| 차헌 ≠ 은규 | 차헌 PC에서 돌아가던 경로를 은규 PC에 **그대로 복사하면 안 됨** |
| 공용 G: USB | 드라이브 문자(`G:`)와 상위 `연구소\실험\...` 는 같을 수 있으나, **그 아래 실험 폴더 트리는 사용자마다 다를 수 있음** |

**Cursor/에이전트:** 코드·문서에 있는 `REACTION_ROOTS` 를 은규 PC에서 **확인 없이 신뢰하지 마세요.**  
탐색기에서 은규가 실제로 쓰는 경로를 먼저 물어보거나, SecuYouSB 로그인 후 직접 확인하세요.

---

## 2. 경로 종류 (무엇을 어디서 바꾸나)

| 경로 | 차헌 PC (참고) | 은규 PC에서 할 일 |
|------|----------------|-------------------|
| **스크립트·KCH** | `Desktop\.cursor\` | 동일 구조 권장 (`STEP6`) — **사용자명(`User`)만 다를 수 있음** |
| **메일 env** | `Desktop\.cursor\gc_automation.env` | 은규 **본인** 네이버 IMAP 계정 |
| **G: 실험 루트** | `촉매 반응 계산.py` 의 `REACTION_ROOTS` | **은규 PC 탐색기에서 확인 후 수정** (아래 §3) |
| **G: 접근 판별** | `EXPERIMENT_DATA_ROOT` | 은규 환경에서 보이는 최상위 실험 폴더로 맞출 것 |
| **Origin .opju** | G: 안 실험 폴더 | 은규가 쓰는 **템플릿 폴더** 기준 (차헌 폴더명과 다를 수 있음) |

**장비 PC 경로 (혼동 금지):**

| PC | 출력 폴더 |
|----|-----------|
| GC1 장비 (은규) | `Desktop\박은규\` |
| GC2/GC3 장비 (차헌) | `Desktop\KCH\` |
| 은규 PC / 차헌 PC | `Desktop\.cursor\KCH\inbox` — **장비 PC의 `KCH`와 다른 PC·다른 용도** |

---

## 3. 은규 PC — G: 경로 맞추기 (필수)

### 3.1 확인

1. SecuYouSB 로그인 → 탐색기에서 `G:` 열기  
2. 은규가 **지금까지 실험 파일을 저장해 온** DRE / DRM / DRME 폴더 위치 확인  
3. repo 기본값과 **다르면** 아래 수정

### 3.2 수정 위치

운영본 **`Desktop\.cursor\촉매 반응 계산.py`** (repo `data_pc/` 복사본) 상단:

```python
REACTION_ROOTS = {
    "DRE":  r"G:\...\은규가_쓰는_DRE_루트",
    "DRM":  r"G:\...\은규가_쓰는_DRM_루트",
    "DRME": r"G:\...\은규가_쓰는_DRME_루트",
}
EXPERIMENT_DATA_ROOT = r"G:\...\은규 환경에서 보이는 실험데이터 상위"
```

### 3.3 Git push 시 주의

- **CALIB·코드 로직** → repo에 push (팀 공유)  
- **은규만의 G: 하위 경로** → `machine_profile.json`의 `notes`에 기록하거나, 은규 PC **로컬 운영본만** 수정  
- 연구실 전체가 같은 G: 트리를 쓰기로 했을 때만 `REACTION_ROOTS` 변경을 repo에 push

### 3.4 machine_profile에 메모 (권장)

`Desktop\.cursor\KCH\machine_profile.json`:

```json
"paths": {
  "script_dir": "C:\\Users\\...\\Desktop\\.cursor",
  "reaction_roots_note": "DRE/DRM/DRME 실제 경로 — 촉매 반응 계산.py REACTION_ROOTS 와 동기화"
},
"notes": {
  "g_drive_layout": "차헌 PC와 폴더 구조 다름. 2026-06-xx 탐색기 확인 경로: ..."
}
```

---

## 4. 차헌 PC 참고값 (은규 PC 기본값 아님)

차헌이 쓰는 repo 기본 `REACTION_ROOTS` 예:

```
G:\연구소\실험\실험데이터\촉매 반응\DRE 반응(C2H6)
G:\연구소\실험\실험데이터\촉매 반응\DRM 반응 (CH4)
G:\연구소\실험\실험데이터\촉매 반응\DRME 반응 (C2H6+CH4)
```

은규 PC에서 위 경로가 **그대로 열리지 않으면** 정상일 수 있습니다. 은규 경로로 바꾼 뒤 `--no-archive` → G: 단계 순으로 테스트하세요.

---

## 5. Cursor 에이전트 체크리스트 (은규 PC)

작업 시작 전:

- [ ] `machine_profile.json` → `role=data_pc`, operator=은규  
- [ ] 이 PC가 **GC1 장비 PC가 아님** (`docs/PC_NAMING.md`)  
- [ ] `REACTION_ROOTS` 를 **은규 G: 실측 경로**와 일치시켰는지 (차헌 경로 무단 가정 금지)  
- [ ] 3~4단계 전 SecuYouSB·Origin(은규 PC) 확인  

관련 문서: `deploy/STEP6_data_pc_setup.md`, `deploy/STEP8_e2e.md`, `.cursor/rules/data-pc-custom-paths.mdc`
