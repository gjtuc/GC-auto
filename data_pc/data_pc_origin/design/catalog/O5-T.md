# O5-T — Worksheet search text (27 L4)

> rollup: O5-L1-T · module: `o5_text.py`  
> **전량 ID:** [`O5-REGISTRY.md`](O5-REGISTRY.md) #25–51  
> **촉매:** `f"{book.name} {wks.name} {book.lname}"` (L1709)

---

## O5-T-01 — `book_name(book)` (5 L4)

| L4 | L7 POST | L8 |
|----|---------|-----|
| a-1 | E `out==book.name`, T str | `"Book1"` |
| b-1 | E None→`""` | `null` |
| c-1 | E `""`→`""` | `""` |
| d-1 | NE strip applied | padded name |
| e-1 | NE `"None"` in out | name=None |

---

## O5-T-02 — `book_lname(book)` (5 L4)

| L4 | L7 POST | L8 |
|----|---------|-----|
| a-1 | E `out==book.lname` | `"DRM Data"` |
| b-1 | E empty→`""` | `""` |
| c-1 | E None→`""` | `null` |
| d-1 | E long name preserved | `"DRM Data"` |
| e-1 | T unicode ok | `"反応データ"` |

---

## O5-T-03 — `wks_name(wks)` (5 L4)

| L4 | L7 POST | L8 |
|----|---------|-----|
| a-1 | E `out==wks.name` | str |
| b-1 | E empty→`""` | `""` |
| c-1 | E golden H2yield | `"H2yield"` |
| d-1 | E golden CO2conv | `"CO2conv"` |
| e-1 | NE strip | `" H2yield "` raw |

---

## O5-T-04 — `compose_search_text(book, wks)` (12 L4)

| L4 | L5 EXEC chain | L7 POST |
|----|---------------|---------|
| a-1 | CALL book_name | called once |
| b-1 | CALL wks_name | called once |
| c-1 | CALL book_lname | called once |
| d-1 | f-string order | `{name} {wks} {lname}` |
| e-1 | byte-equal 촉매 | == manual L1709 |
| f-1 | E golden sheet[0] | Book1 H2yield DRM Data |
| g-1 | E golden sheet[4] | CO2conv row |
| h-1 | NE normalize in compose | no o0_keys |
| i-1 | E empty lname trailing space | raw f-string policy |
| j-1 | E manual concat == compose | refactor-safe |
| k-1 | L len(out)>0 | names set |
| l-1 | NE forced lower | case preserved |

### O5-T-04-e-1 L7 (촉매 동형)

| Quark | Lepton | Kind | Spec |
|-------|--------|------|------|
| Q1 | L1 | DEP | O5-T-04-a..c PASS |
| Q2 | L1 | C | `manual = f"{book.name} {wks.name} {book.lname}"` |
| Q2 | L2 | C | `out = compose_search_text(book,wks)` |
| Q3 | L1 | E | `out == manual` |
| Q3 | L2 | E | `out == 촉매_L1709_replay` |

**API:**

```python
def book_name(book) -> str: ...
def book_lname(book) -> str: ...
def wks_name(wks) -> str: ...
def compose_search_text(book, wks) -> str: ...
```
