# O0-K — Keys (9 L4)

> rollup: O0-L1-K → O0 · module: `o0_keys.normalize_origin_key`

---

## O0-K-01-a-1 — None → ""

| L7 | Kind | Spec |
|----|------|------|
| Q1-L1 | DEP | O0 (none) |
| Q1-L2 | T | arg is None |
| Q2-L1 | C | `normalize_origin_key(None)` |
| Q3-L1 | E | `== ""` |
| FA-B1 | in | `null` |
| FA-B2 | out | `""` |

---

## O0-K-01-b-1 — "" → ""

| L7 | Kind | Spec |
|----|------|------|
| Q1-L2 | T | `isinstance("", str)` |
| Q3-L1 | E | `== ""` |

---

## O0-K-01-c-1 — whitespace only → ""

| L7 | Kind | Spec |
|----|------|------|
| Q1-L2 | T | str with only `\s` |
| Q2-L1 | REG | input matches `^\s+$` |
| Q2-L2 | C | normalize |
| Q3-L1 | E | `== ""` |
| FA-B1 | in | `"   \t  "` |

---

## O0-K-01-d-1 — "H2 yield" → "h2yield"

| L7 | Kind | Spec |
|----|------|------|
| Q1-L2 | T | non-empty str |
| Q2-L1 | C | `s = in.lower()` |
| Q2-L2 | C | `out = re.sub(r'\s+','', s)` |
| Q3-L1 | E | `out == "h2yield"` |
| Q3-L2 | BOOL | no upper in out |
| FA-B1/B2 | in/out | `"H2 yield"` / `"h2yield"` |
| FB-B1/B2 | in/out | `"H2yield"` / `"h2yield"` |
| FC-B1/B2 | in/out | `"h2 yield"` / `"h2yield"` |

---

## O0-K-01-e-1 — padded CO2

| L7 | Kind | Spec |
|----|------|------|
| Q2-L1..L2 | C | same pipeline as d-1 |
| Q3-L1 | E | `"co2conversion"` |
| FA-B1 | in | `"  CO2 conversion "` |

---

## O0-K-01-f-1 — no uppercase retained

| L7 | Kind | Spec |
|----|------|------|
| Q2-L1 | C | normalize `"DRM CH4"` |
| Q3-L1 | BOOL | `out == out.lower()` |
| Q3-L2 | NE | `"DRM" not in out` |
| FA-B1 | out | `"drmch4"` |

---

## O0-K-01-g-1 — tab/multispace

| L7 | Kind | Spec |
|----|------|------|
| Q2-L2 | REG | `\t+` collapsed |
| Q3-L1 | E | `"h2yield"` |
| FA-B1 | in | `"H2\t\tYield"` |
| FB-B1 | in | `"H2  \n  Yield"` |

---

## O0-K-02-a-1 — norm equality

| L7 | Kind | Spec |
|----|------|------|
| Q2-L1 | C | `na=normalize(a); nb=normalize(b)` |
| Q3-L1 | E | `na==nb → keys_match True` |
| FA-B1/B2 | in | `"H2 yield"` / `"h2yield"` |
| FB-B1/B2 | in | `"x"` / `"y"` → False |

---

## O0-K-02-b-1 — substring in search

| L7 | Kind | Spec |
|----|------|------|
| Q2-L1 | C | `nk=normalize(kw); ns=normalize(search)` |
| Q3-L1 | IN | `nk in ns` |
| Q3-L2 | IN | reverse False |
| FA-B1 | kw | `"H2 yield"` |
| FA-B2 | search | `"Book1 H2yield Sheet1"` |
| FB-B1 | kw | `"co2conversion"` |
| FB-B2 | search | `"Book1 H2yield"` → False |

**촉매 대응:** `_normalize_origin_key` — O5-M-01 전제.
