# O5-M — Worksheet keyword match (54 L4 + 5 DEBUG)

> rollup: O5-L1-M · module: `o5_match.py` · debug: `o5_debug.py`  
> **전량 ID:** [`O5-REGISTRY.md`](O5-REGISTRY.md) #52–110  
> **증상:** `일치하는 데이터 시트를 하나도 찾지 못했습니다` → #92 `O5-M-03-l-1` / #112 E2E-02

---

## O5-M-01 — `keyword_in_text(text, kw)` (14 L4)

| L4 | L5 micro-step | L7 POST | L8 |
|----|---------------|---------|-----|
| a-1 | guard kw empty | E False before norm | `""` |
| b-1 | guard kw whitespace | E False | `"   "` |
| c-1 | CALL normalize(kw) | once | spy |
| d-1 | CALL normalize(text) | once | spy |
| e-1 | `nk in nt` | IN True | H2 yield / Book1 H2yield |
| f-1 | reverse | IN False | co2 / h2yield |
| g-1 | FX C1 | E True | miss_matrix |
| h-1 | FX C2 typo | E False | miss_matrix |
| i-1 | FX C3 space | E True | miss_matrix |
| j-1 | FX C4 wrong kw | E False | miss_matrix |
| k-1 | FX C5 empty search | E False | `"   "` |
| l-1 | delegate | CALL o0_keys only | import audit |
| m-1 | text empty | E False | text=`""` |
| n-1 | both empty | E False | |

### O5-M-01-e-1 L7 전개

| Quark | Lepton | Kind | Spec |
|-------|--------|------|------|
| Q1 | L1 | DEP | O5-M-01-c-1, O5-M-01-d-1 |
| Q2 | L1 | C | `nk = normalize_origin_key(kw)` |
| Q2 | L2 | C | `nt = normalize_origin_key(text)` |
| Q2 | L3 | C | `return nk in nt` |
| Q3 | L1 | IN | result is True |
| FA-B1 | kw | H2 yield |
| FA-B2 | text | Book1 H2yield Sheet1 |

---

## O5-M-02 — `find_worksheet_for_keyword(op, kw)` (14 L4)

| L4 | L5 chain | L7 POST |
|----|----------|---------|
| a-1 | iter_worksheets | CALL once |
| b-1 | per pair compose | CALL compose |
| c-1 | per pair keyword_in_text | CALL M-01 |
| d-1 | first True | return wks ref |
| e-1 | exhaust | return None |
| f-1 | inner break | spy inner stop |
| g-1 | outer break | spy outer stop (L1713) |
| h-1 | after hit no compose | compose count frozen |
| i-1 | dup wks name | first book wins |
| j-1 | kw unchanged | same str to M-01 |
| k-1 | miss no raise | None type |
| l-1 | H2 yield hit | wks.name H2yield |
| m-1 | CO2 conv hit | wks.name CO2conv |
| n-1 | scan count | == index of hit + 1 |

---

## O5-M-03 — `resolve_worksheets(op, mapping, df)` (18 L4)

| L4 | L7 POST |
|----|---------|
| a-1 | iterate mapping.items order |
| b-1 | df col missing → continue (no miss) |
| c-1 | each present col: find_worksheet |
| d-1 | hit → hits[kw]=wks |
| e-1 | miss → misses.append(kw) |
| f-1 | misses preserve mapping order |
| g-1 | LEN hits ≤ 8 |
| h-1 | FX 8/8 full |
| i-1 | partial df 2 cols → hits≤2 |
| j-1 | partial miss ⊆ df cols |
| k-1 | partial hits+misses both |
| l-1 | empty op → all present cols miss (**symptom**) |
| m-1 | 0 hits → len(misses)>0 |
| n-1 | two kw → two wks ok |
| o-1 | mapping dup keys N/A (O0-M) |
| p-1 | return `(hits, misses)` tuple |
| q-1 | hits keys are origin kw str |
| r-1 | misses is list[str] |

---

## O5-M-04 — `report_missing(misses)` (8 L4)

| L4 | L7 POST |
|----|---------|
| a-1 | code `WKS_MISS` |
| b-1 | detail has each kw |
| c-1 | empty → `[]` |
| d-1 | 1 miss → 1 warn |
| e-1 | 8 miss → 1 aggregated warn |
| f-1 | warn frozen dataclass |
| g-1 | str(w) printable |
| h-1 | hits>0 misses=0 → no warn |

---

## § DEBUG (5 L4, optional `--o5-debug`)

| L4 | L7 |
|----|-----|
| O5-DEBUG-01-a-1 | log raw search_str each candidate |
| O5-DEBUG-02-a-1 | log norm(kw) \| norm(search) |
| O5-DEBUG-03-a-1 | log hit kw+book+wks |
| O5-DEBUG-04-a-1 | log total pairs scanned |
| O5-DEBUG-05-a-1 | log first miss FX id C2/C4 |

---

## § E2E mock (3 L4, `--rollup O5-E2E`)

| L4 | Spec |
|----|------|
| O5-E2E-01-a-1 | I→T→M FX 8/8 hits |
| O5-E2E-02-a-1 | empty op 0 hits symptom string path |
| O5-E2E-03-a-1 | partial 2/8 + WKS_MISS |

**API:**

```python
def keyword_in_text(text: str, kw: str) -> bool: ...
def find_worksheet_for_keyword(op, kw: str) -> Any | None: ...
def resolve_worksheets(op, mapping, df) -> tuple[dict[str, Any], list[str]]: ...
def report_missing(misses: list[str]) -> list[Any]: ...
```
