# O5-I — Worksheet iterate (24 L4)

> rollup: O5-L1-I · module: `o5_iterate.py`  
> **전량 ID·순서:** [`O5-REGISTRY.md`](O5-REGISTRY.md) #1–24  
> **촉매:** `for book in op.pages('w'): for wks in book:` (L1707–1708)

---

## O5-I-01 — `iter_pages_w(op)` (12 L4)

| L4 | L5 EXEC | L7 POST | L8 FA |
|----|---------|---------|-------|
| a-1 | CALL `op.pages` | arg `('w',)` | `'w'` |
| b-1 | | `callable(pages)` | mock |
| c-1 | | `pages` called with `'w'` | spy |
| d-1 | | call_count==1 on full consume | spy |
| e-1 | | return is Iterable, not list | `iter([])` |
| f-1 | | `pages→[]` len 0 | `[]` |
| g-1 | | no raise on empty | `[]` |
| h-1 | | partial next: pages not recalled | lazy spy |
| i-1 | | `op=None` → TypeError | `null` |
| j-1 | | no pages → AttributeError | `{}` |
| k-1 | | stub 2 books len==2 | FX 2 books |
| l-1 | | ORD Book1 before Book2 | FX order |

### O5-I-01-a-1 L7 전개 (템플릿)

| Quark | Lepton | Kind | Spec |
|-------|--------|------|------|
| Q1 | L1 | DEP | O4-R-01-a-1 |
| Q1 | L2 | T | `op` has attr pages |
| Q1 | L3 | F | FX-O5-opju-mock op stub |
| Q2 | L1 | C | `iter_pages_w(op)` starts |
| Q2 | L2 | C | triggers `op.pages('w')` |
| Q3 | L1 | CALL | mock.assert_called_with('w') |
| Q3 | L2 | E | call_count >= 1 |

```yaml
# design/catalog/gates/O5/O5_I_01_a_1.yaml
gate: O5-I-01-a-1
depends: [O4-R-01-a-1]
symbol: iter_pages_w
assert: "mock_pages.assert_called_with('w')"
```

---

## O5-I-02 — `iter_worksheets(op)` (12 L4)

| L4 | L5 EXEC | L7 POST | L8 |
|----|---------|---------|-----|
| a-1 | CALL iter_pages_w once | inner I-01 invoked | spy |
| b-1 | nested for | each yield len==2 | tuple |
| c-1 | | pair[0] is book ref | identity |
| d-1 | | pair[1] is wks ref | identity |
| e-1 | | ORD book outer wks inner | FX table |
| f-1 | | empty book 0 yield | BookEmpty |
| g-1 | | empty op 0 pair | `pages→[]` |
| h-1 | | Book1 8 wks → 8 pairs | FX 8 sheets |
| i-1 | | total == Σ\|wks per book\| | count |
| j-1 | | no duplicate (book,wks) | set len |
| k-1 | | wks.name readable | attr |
| l-1 | | book.name/lname readable | attr |

**API:**

```python
def iter_pages_w(op) -> Iterator[Any]: ...
def iter_worksheets(op) -> Iterator[tuple[Any, Any]]: ...
```
