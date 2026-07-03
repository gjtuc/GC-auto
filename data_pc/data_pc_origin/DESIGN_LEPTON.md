# data_pc_origin — Lepton 설계 (L7 · L8)

> **8단계 분해:** L0 … L4 나노 → L5 쿼크 → L6 포톤 → **L7 레pton** → **L8 bit**  
> L4: `DESIGN_ATOMIC.md` · L5/L6: `DESIGN_NANO.md` · **리프 카탈로그: `design/catalog/`**  
> **설계 전용** — 코드·registry 미구현.

---

## ID 규칙 (L7 · L8)

```
O0-K-01-d-1              L4  — assert 1개 (= verify --gate)
O0-K-01-d-1-Q2           L5  — 쿼크 (PRE/EXEC/POST)
O0-K-01-d-1-Q2-L1        L7  — 레pton (단일 predicate, side-effect 없음)
O0-K-01-d-1-FA           L6  — 포톤 (픽스처 묶음)
O0-K-01-d-1-FA-B1        L8  — bit (리터럴 1값 + 타입 태그)
```

| L7 종류 | 코드 | 의미 | verify 실패 |
|---------|------|------|-------------|
| TYPE | `T` | isinstance / None 허용 | CONTRACT |
| EQ | `E` | `actual == expected` | ASSERT |
| NE | `N` | `actual != forbidden` | ASSERT |
| IN | `I` | membership / substring | ASSERT |
| REG | `R` | regex full/partial match | ASSERT |
| LEN | `L` | len / bounds | ASSERT |
| ORD | `O` | `<`, `<=` ordering | ASSERT |
| BOOL | `B` | truthiness 고정 | ASSERT |
| NAN | `A` | math.isnan / pd.isna | ASSERT |
| RAISE | `X` | raises ExcType | ASSERT |
| CALL | `C` | 1회 호출·인자 스�APSHOT | CONTRACT |
| FX | `F` | L8 bit 로드 성공 | CONTRACT |
| DEP | `D` | 선행 gate PASS (RG) | LOCKED |

**롤업:** L8 → L6 → L7 AND → L5 → L4 → … → L0.

**verify (목표 CLI):**

```bash
python -m data_pc_origin.verify --gate O0-K-01-d-1          # L4 (L7 전체)
python -m data_pc_origin.verify --gate O0-K-01-d-1 --quark  # L5 trace
python -m data_pc_origin.verify --lepton O0-K-01-d-1-Q2-L1  # L7 단독
python -m data_pc_origin.verify --bit O0-K-01-d-1-FA-B2   # L8 단독
```

---

## L8 bit 태그 (JSON/YAML 공통)

```yaml
# design/catalog/_SCHEMA.yaml — gate leaf 일부
gate: O0-K-01-d-1
fixture: FA
bits:
  - id: B1
    tag: in
    type: str
    value: "H2 yield"
  - id: B2
    tag: out
    type: str
    value: "h2yield"
  - id: B3
    tag: forbid_upper
    type: bool
    value: true   # out에 isupper() True 문자 없음
```

| tag | 용도 |
|-----|------|
| `in` | 함수 입력 |
| `out` | 기대 출력 |
| `env` | os.environ 키·값 |
| `path` | 파일·opju 경로 (live gate) |
| `raises` | 예외 타입명 |
| `before` / `after` | side-effect 스냅샷 |
| `golden` | E2E 기준 파일 hash 또는 row slice |

---

## RG 확장 (L7 registry)

| ID | L7 |
|----|-----|
| RG-L7-01 | gate_id → [Q1-L1, Q1-L2, …] ordered |
| RG-L7-02 | lepton_id → kind enum |
| RG-L7-03 | lepton fail → stderr `FAIL O0-K-01-d-1-Q2-L1 EQ` |
| RG-L8-01 | fixture_id → bits[] typed |
| RG-L8-02 | bit mismatch → diff unified 1-line |

---

## 수치 (설계)

| 레벨 | 개수 |
|------|------|
| L4 | ~320 |
| L5 | ~900 |
| L6 | ~450 |
| **L7** | **~2,400** (L5당 ≈2.7 lepton) |
| **L8** | **~1,200** (L6당 ≈2.7 bit) |

---

## 카탈로그 파일 (리프 전개)

| 파일 | L4 수 | 비고 |
|------|-------|------|
| [`design/catalog/O0-T.md`](design/catalog/O0-T.md) | 6 | types |
| [`design/catalog/O0-K.md`](design/catalog/O0-K.md) | 9 | keys |
| [`design/catalog/O0-I.md`](design/catalog/O0-I.md) | 9 | identity |
| [`design/catalog/O0-C.md`](design/catalog/O0-C.md) | 11 | comments |
| [`design/catalog/O0-S.md`](design/catalog/O0-S.md) | 16 | series/gap |
| [`design/catalog/O0-M.md`](design/catalog/O0-M.md) | 10 | mapping |
| [`design/catalog/O1-P.md`](design/catalog/O1-P.md) | 18 | opju probe 확장 |
| [`design/catalog/O5-REGISTRY.md`](design/catalog/O5-REGISTRY.md) | **117** | **마스터 #1–117** |
| [`design/catalog/O5-I.md`](design/catalog/O5-I.md) | 24 | iterate |
| [`design/catalog/O5-T.md`](design/catalog/O5-T.md) | 27 | search text |
| [`design/catalog/O5-M.md`](design/catalog/O5-M.md) | 66 | match+DBG+E2E |
| [`design/catalog/gates/O5/`](design/catalog/gates/O5/) | YAML | L4 leaf schema |
| [`design/catalog/_TEMPLATE.md`](design/catalog/_TEMPLATE.md) | — | O2–O9 복제 양식 |
| [`design/catalog/_INDEX.md`](design/catalog/_INDEX.md) | — | 전체 색인 |

O0 **61 L4** = 카탈로그 6파일에 L7/L8 **전량** 기재.  
O1–O9 나머지 = `_TEMPLATE.md` + `DESIGN_NANO.md` 표에서 L7/L8 파생.

---

## L7 템플릿 (모든 L4 공통 골격)

```
L4  {GATE_ID}
├─ Q1 PRE
│   ├─ L1 DEP  parents PASS
│   ├─ L2 T    input type contract
│   └─ L3 F    L8 bits loaded
├─ Q2 EXEC (0..n)
│   ├─ L1 C    call target once
│   └─ L2..    micro-ops (lower, regex, …)
└─ Qn POST
    ├─ L1 E    primary assert
    └─ L2..    secondary invariants
```

---

## 촉매 ↔ L7 추적 (운영 디버그)

| 증상 | 시작 gate | L7 체인 |
|------|-----------|---------|
| 시트 0개 | O5-M-03-a-1 | Q2-L2 IN kw⊄search → O5-DEBUG-02 |
| 열 못 찾음 | O6-R-01-a-1 | Q2-L3 exact → Q3-L1 identity |
| 갭 0으로 그림 | O7-G-01-a-1 | Q3-L1 E out[99]=="" |
| COM hang | O3-S-04-a-1 | Q2-L1 CALL op.exit once |

`DATA_PC_SKIP_ORIGIN=1` — E2E L7/L8 live Origin 제외.
