# Gate Leaf Template — O2~O9 복제 양식

> 한 L4 블록을 복사해 `design/catalog/O{n}-{L1}.md`에 채운다.

---

## `{GATE_ID}` — `{한 줄 설명}`

| Layer | ID | Kind | Spec |
|-------|-----|------|------|
| L4 | `{GATE_ID}` | — | `{assert 한 줄}` |
| L5 | `{GATE_ID}-Q1` | PRE | |
| L7 | `{GATE_ID}-Q1-L1` | DEP | `{parent gates}` |
| L7 | `{GATE_ID}-Q1-L2` | T | `{input contract}` |
| L7 | `{GATE_ID}-Q1-L3` | F | L8 `{GATE_ID}-FA` loaded |
| L5 | `{GATE_ID}-Q2` | EXEC | |
| L7 | `{GATE_ID}-Q2-L1` | C | `{call}` |
| L7 | `{GATE_ID}-Q2-L2` | `{T\|REG\|…}` | `{micro-op}` |
| L5 | `{GATE_ID}-Q3` | POST | |
| L7 | `{GATE_ID}-Q3-L1` | E | `{primary}` |
| L6 | `{GATE_ID}-FA` | — | positive |
| L8 | `{GATE_ID}-FA-B1` | in | `{literal}` |
| L8 | `{GATE_ID}-FA-B2` | out | `{literal}` |
| L6 | `{GATE_ID}-FB` | — | negative (optional) |
| L8 | `{GATE_ID}-FB-B1` | raises | `{Exc}` |

**YAML:** `gates/{L0}/{GATE_ID with _}.yaml` — `_SCHEMA.yaml` 동일 구조.

---

## O2~O9 L4 목록 (L7 미전개 — NANO 표에서 파생)

| L0 | L1 | L4 수 | 우선순위 |
|----|-----|-------|----------|
| O2 | E,L,G | 22 | Phase 3 |
| O3 | S,P | 12 | Phase 4 |
| O4 | V,O,S,R | 8 | Phase 4 |
| O5 | I,T,M,DBG,E2E,R | **117** | **Phase 5 ★ (설계 완)** |
| O6 | S,F,P,I,R | 12 | Phase 5 |
| O7 | P,W,G | 9 | Phase 5 |
| O8 | C,J | 11 | Phase 6 |
| O9 | F,E2E | 7 | Phase 6 |

★ = `O5-M.md` 선행 전개 완료; 나머지 O5-I/T는 본 템플릿으로 확장.
