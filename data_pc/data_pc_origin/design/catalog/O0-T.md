# O0-T — Types (6 L4)

> [`DESIGN_LEPTON.md`](../../DESIGN_LEPTON.md) · rollup: O0-L1-T → O0

---

## O0-T-01-a-1 — IdentityKey 2-tuple

| Layer | ID | Kind | Spec |
|-------|-----|------|------|
| L4 | O0-T-01-a-1 | — | valid key is 2-str tuple |
| L5-Q1 | PRE | DEP O0 (none) |
| L7 | Q1-L1 | T | `isinstance(k, tuple)` |
| L7 | Q1-L2 | L | `len(k)==2` |
| L5-Q3 | POST | |
| L7 | Q3-L1 | T | `all(isinstance(x,str) for x in k)` |
| L6-FA | | FX-IDENTITY-DRE |
| L8 | FA-B1 | in | `("20260620","dre(1.5) 600c ni5_ce5_al2o3")` |
| L6-FB | | invalid |
| L8 | FB-B1 | in | `("20260620",)` |
| L8 | FB-B2 | tag | fail at Q1-L2 |

---

## O0-T-01-b-1 — date 8 digits

| Layer | ID | Kind | Spec |
|-------|-----|------|------|
| L4 | O0-T-01-b-1 | — | key[0] is 8 digit str |
| L7 | Q3-L1 | REG | `re.fullmatch(r"\d{8}", k[0])` |
| L8 | FA-B1 | in | `"20260620"` |
| L8 | FB-B1 | in | `"2026062"` → fail |

---

## O0-T-02-a-1 — GapPolicy enum 3

| Layer | ID | Kind | Spec |
|-------|-----|------|------|
| L4 | O0-T-02-a-1 | — | members AS_EMPTY, AS_NAN, SKIP_ROWS |
| L7 | Q2-L1 | IN | names ⊆ GapPolicy.__members__ |
| L7 | Q3-L1 | L | `len(GapPolicy)==3` |
| L8 | FA-B1 | golden | `{AS_EMPTY,AS_NAN,SKIP_ROWS}` |

---

## O0-T-02-b-1 — str Enum

| Layer | ID | Kind | Spec |
|-------|-----|------|------|
| L4 | O0-T-02-b-1 | — | issubclass(GapPolicy, str) |
| L7 | Q3-L1 | T | `issubclass(GapPolicy, str)` |
| L7 | Q3-L2 | E | `GapPolicy.AS_EMPTY == "empty"` |

---

## O0-T-03-a-1 — ProbeResult fields

| Layer | ID | Kind | Spec |
|-------|-----|------|------|
| L4 | O0-T-03-a-1 | — | frozen dataclass ok, detail |
| L7 | Q3-L1 | T | has attrs ok:bool, detail:str |
| L7 | Q3-L2 | BOOL | frozen=True |

---

## O0-T-04-a-1 — OriginPath alias

| Layer | ID | Kind | Spec |
|-------|-----|------|------|
| L4 | O0-T-04-a-1 | — | NewType or str alias |
| L7 | Q3-L1 | T | `isinstance(p, str)` for OriginPath value |
| L8 | FA-B1 | in | `"G:\\EXPERIMENT\\x.opju"` |
