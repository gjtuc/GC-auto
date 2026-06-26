# O5 — L4 전량 레지스트리 (120 gates)

> **형제 순서 = 구현 순서 = verify `--gate` 체인**  
> rollup: `O5-L2-*` → `O5-L1-*` → `O5`  
> L7/L8 상세: `O5-I.md` · `O5-T.md` · `O5-M.md`

| # | gate_id | L2 | assert 한 줄 |
|---|---------|-----|-------------|
| 1 | O5-I-01-a-1 | iter_pages_w | `hasattr(op,'pages')` |
| 2 | O5-I-01-b-1 | | `callable(op.pages)` |
| 3 | O5-I-01-c-1 | | `pages` 호출 인자 `('w',)` |
| 4 | O5-I-01-d-1 | | 첫 full consume 시 `pages` 1회 |
| 5 | O5-I-01-e-1 | | 반환값 `Iterable` (list 아님) |
| 6 | O5-I-01-f-1 | | `pages→[]` → yield 0 |
| 7 | O5-I-01-g-1 | | empty 시 예외 없음 |
| 8 | O5-I-01-h-1 | | lazy: partial next 후 pages 재호출 없음 |
| 9 | O5-I-01-i-1 | | `op is None` → TypeError |
| 10 | O5-I-01-j-1 | | `pages` 없음 → AttributeError |
| 11 | O5-I-01-k-1 | | stub 2 book → len==2 |
| 12 | O5-I-01-l-1 | | book 순서 FX stub ORD |
| 13 | O5-I-02-a-1 | iter_worksheets | 내부 `iter_pages_w` 1회 |
| 14 | O5-I-02-b-1 | | 각 yield `tuple(len=2)` |
| 15 | O5-I-02-c-1 | | `pair[0] is book` |
| 16 | O5-I-02-d-1 | | `pair[1] is wks` |
| 17 | O5-I-02-e-1 | | book 외부 · wks 내부 ORD |
| 18 | O5-I-02-f-1 | | empty book → 0 yield |
| 19 | O5-I-02-g-1 | | empty op → 0 pair |
| 20 | O5-I-02-h-1 | | Book1 8 wks → 8 pair |
| 21 | O5-I-02-i-1 | | total pairs = Σ\|wks\| |
| 22 | O5-I-02-j-1 | | duplicate (book,wks) 없음 |
| 23 | O5-I-02-k-1 | | wks `name` attr readable |
| 24 | O5-I-02-l-1 | | book `name`/`lname` readable |
| 25 | O5-T-01-a-1 | book_name | `out==book.name` str |
| 26 | O5-T-01-b-1 | | `name None` → `""` |
| 27 | O5-T-01-c-1 | | `name ""` → `""` |
| 28 | O5-T-01-d-1 | | strip 미적용 (raw) |
| 29 | O5-T-01-e-1 | | `"None"` 문자열 금지 |
| 30 | O5-T-02-a-1 | book_lname | `out==book.lname` |
| 31 | O5-T-02-b-1 | | empty lname → `""` |
| 32 | O5-T-02-c-1 | | `lname None` → `""` |
| 33 | O5-T-02-d-1 | | long lname `"DRM Data"` golden |
| 34 | O5-T-02-e-1 | | unicode lname ok |
| 35 | O5-T-03-a-1 | wks_name | `out==wks.name` |
| 36 | O5-T-03-b-1 | | empty → `""` |
| 37 | O5-T-03-c-1 | | `H2yield` golden |
| 38 | O5-T-03-d-1 | | `CO2conv` golden |
| 39 | O5-T-03-e-1 | | strip 미적용 |
| 40 | O5-T-04-a-1 | compose | CALL book_name |
| 41 | O5-T-04-b-1 | | CALL wks_name |
| 42 | O5-T-04-c-1 | | CALL book_lname |
| 43 | O5-T-04-d-1 | | `f"{n} {w} {l}"` 순서 |
| 44 | O5-T-04-e-1 | | 촉매 L1709 byte-equal |
| 45 | O5-T-04-f-1 | | golden sheet[0] |
| 46 | O5-T-04-g-1 | | golden sheet[4] CO2conv |
| 47 | O5-T-04-h-1 | | compose 내 normalize 금지 |
| 48 | O5-T-04-i-1 | | empty lname trailing space (촉매 raw) |
| 49 | O5-T-04-j-1 | | manual concat == compose |
| 50 | O5-T-04-k-1 | | out len > 0 when names set |
| 51 | O5-T-04-l-1 | | out 대소문자 보존 |
| 52 | O5-M-01-a-1 | kw guard | `kw==""` → False (normalize 전) |
| 53 | O5-M-01-b-1 | | `kw whitespace` → False |
| 54 | O5-M-01-c-1 | norm kw | CALL `normalize_origin_key(kw)` 1회 |
| 55 | O5-M-01-d-1 | norm text | CALL `normalize_origin_key(text)` 1회 |
| 56 | O5-M-01-e-1 | in check | `nk in nt` True happy |
| 57 | O5-M-01-f-1 | | reverse False |
| 58 | O5-M-01-g-1 | | FX C1 MATCH |
| 59 | O5-M-01-h-1 | | FX C2 MISS typo |
| 60 | O5-M-01-i-1 | | FX C3 MATCH space |
| 61 | O5-M-01-j-1 | | FX C4 MISS wrong kw |
| 62 | O5-M-01-k-1 | | FX C5 empty search MISS |
| 63 | O5-M-01-l-1 | delegate | import `o0_keys` only |
| 64 | O5-M-01-m-1 | | `text==""` + nonempty kw → False |
| 65 | O5-M-01-n-1 | | both empty → False |
| 66 | O5-M-02-a-1 | find_first | CALL iter_worksheets |
| 67 | O5-M-02-b-1 | | per pair CALL compose |
| 68 | O5-M-02-c-1 | | per pair CALL keyword_in_text |
| 69 | O5-M-02-d-1 | | first True → return wks |
| 70 | O5-M-02-e-1 | | exhaust → None |
| 71 | O5-M-02-f-1 | | hit 후 inner wks loop break |
| 72 | O5-M-02-g-1 | | hit 후 outer book loop break |
| 73 | O5-M-02-h-1 | | hit 후 compose 호출 0 |
| 74 | O5-M-02-i-1 | | first book wins dup wks name |
| 75 | O5-M-02-j-1 | | kw 인자 변형 없음 |
| 76 | O5-M-02-k-1 | | miss 시 wks None not raise |
| 77 | O5-M-02-l-1 | | H2 yield → wks.name H2yield |
| 78 | O5-M-02-m-1 | | CO2 conversion → CO2conv |
| 79 | O5-M-02-n-1 | | spy: pairs scanned until hit |
| 80 | O5-M-03-a-1 | resolve | mapping items 순회 |
| 81 | O5-M-03-b-1 | | df col 없으면 skip |
| 82 | O5-M-03-c-1 | | each: find_worksheet_for_keyword |
| 83 | O5-M-03-d-1 | | hit → dict[kw]=wks |
| 84 | O5-M-03-e-1 | | miss → misses append |
| 85 | O5-M-03-f-1 | | misses mapping key order |
| 86 | O5-M-03-g-1 | | hits ≤ 8 |
| 87 | O5-M-03-h-1 | | FX 8/8 full hit |
| 88 | O5-M-03-i-1 | | partial 2 col df → 2 hits max |
| 89 | O5-M-03-j-1 | | partial miss only in df cols |
| 90 | O5-M-03-k-1 | | partial hits + misses coexist |
| 91 | O5-M-03-l-1 | | empty op → all df cols miss |
| 92 | O5-M-03-m-1 | | symptom: 0 hits → misses len>0 |
| 93 | O5-M-03-n-1 | | same wks two kw ok (different sheets) |
| 94 | O5-M-03-o-1 | | duplicate kw in mapping N/A (O0-M) |
| 95 | O5-M-03-p-1 | | return `(hits, misses)` tuple |
| 96 | O5-M-03-q-1 | | hits dict key = origin keyword str |
| 97 | O5-M-03-r-1 | | misses list[str] type |
| 98 | O5-M-04-a-1 | report | code `WKS_MISS` |
| 99 | O5-M-04-b-1 | | detail contains each miss kw |
| 100 | O5-M-04-c-1 | | empty misses → `[]` |
| 101 | O5-M-04-d-1 | | single miss → 1 warning |
| 102 | O5-M-04-e-1 | | 8 miss → 1 aggregated warning |
| 103 | O5-M-04-f-1 | | warning immutable / hashable |
| 104 | O5-M-04-g-1 | | printable for 촉매 UX |
| 105 | O5-M-04-h-1 | | no warning when hits>0 and misses=0 |
| 106 | O5-DEBUG-01-a-1 | debug | log raw search_str per candidate |
| 107 | O5-DEBUG-02-a-1 | | log norm(kw)\|norm(search) |
| 108 | O5-DEBUG-03-a-1 | | log hit kw+book+wks |
| 109 | O5-DEBUG-04-a-1 | | log scan count at end |
| 110 | O5-DEBUG-05-a-1 | | log first miss reason C2/C4 |
| 111 | O5-E2E-01-a-1 | e2e mock | I→T→M chain FX 8/8 |
| 112 | O5-E2E-02-a-1 | | I→T→M chain FX 0/8 symptom |
| 113 | O5-E2E-03-a-1 | | partial 2/8 + WKS_MISS |
| 114 | O5-R-01-a-1 | rollup smoke | O5-L1-I 24 gate 논리 AND |
| 115 | O5-R-02-a-1 | | O5-L1-T 27 gate AND |
| 116 | O5-R-03-a-1 | | O5-L1-M 54 gate AND |
| 117 | O5-R-04-a-1 | | full O5 105 core AND |

**수치:** L1-I=24 · L1-T=27 · L1-M=54 · **core=105** · DEBUG=5 · E2E=3 · R=4 → **총 117 gate IDs**

## Rollup map

| rollup_id | gates |
|-----------|-------|
| O5-L2-I01 | #1–12 |
| O5-L2-I02 | #13–24 |
| O5-L1-I | #1–24 |
| O5-L2-T01 | #25–29 |
| O5-L2-T02 | #30–34 |
| O5-L2-T03 | #35–39 |
| O5-L2-T04 | #40–51 |
| O5-L1-T | #25–51 |
| O5-L2-M01 | #52–65 |
| O5-L2-M02 | #66–79 |
| O5-L2-M03 | #80–97 |
| O5-L2-M04 | #98–105 |
| O5-L1-M | #52–105 |
| O5-DEBUG | #106–110 (optional) |
| O5-E2E | #111–113 (mock only) |
| O5-R | #114–117 |
| **O5** | #1–105 (+DEBUG #106–110 opt) |

## L5 골격 (모든 L4 공통)

```
Q1 PRE  → DEP + input T + FX load
Q2 EXEC → CALL chain (side-effect 없는 L7만)
Q3 POST → E / IN / LEN / ORD primary assert
Q4 POST → secondary invariants (optional)
```

## 모듈 분할 (L1)

| module | L2 functions |
|--------|--------------|
| `o5_iterate.py` | I-01, I-02 |
| `o5_text.py` | T-01..T-04 |
| `o5_match.py` | M-01..M-04 |
| `o5_debug.py` | DEBUG-* (optional) |

선행: **O4 PASS** (#1 DEP = O4-R-01-a-1) · **O0-K-02** (#52–65 DEP)
