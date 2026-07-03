# O1-P — Opju path probes (18 L4)

> L7/L8 전량 · O0 PASS + 승인 후 구현 · live bit는 `--live` only

---

## O1-P-01 — path_is_nonempty

| L4 | L7 | L8 |
|----|-----|-----|
| a-1 empty | Q3 E ok=False | `path=""` |
| b-1 whitespace | Q2 C strip Q3 fail | `"   "` |

---

## O1-P-02 — path_exists

| L4 | L7 | L8 |
|----|-----|-----|
| a-1 missing | Q2 BOOL not isfile Q3 fail | `/no/such.opju` |
| b-1 symlink | Q2 islink and not exists | mock tmp |

---

## O1-P-03-a-1 — directory

| L7 | Q2 BOOL isdir → fail |
| L8 | path=`G:\EXPERIMENT` (dir) |

---

## O1-P-04 — suffix

| L4 | L7 | L8 |
|----|-----|-----|
| a-1 .opju | Q2 suffix casefold | `.opju` |
| b-1 .OPJU | Q3 pass | |
| c-1 .opj | Q3 fail | |

---

## O1-P-05 — G: drive

| L4 | L7 | L8 |
|----|-----|-----|
| a-1 prefix | Q2 startswith `G:` | |
| b-1 lower g: | Q2 normalize upper | `g:\x.opju` |

---

## O1-P-06 — root accessible

| L4 | L7 | L8 |
|----|-----|-----|
| a-1 isdir | Q2 EXPERIMENT_DATA_ROOT | env from 촉매 |
| b-1 detail | Q3 IN path in detail string | root missing |

---

## O1-P-07 — aggregate

| L4 | L7 | L8 |
|----|-----|-----|
| a-1 all pass | Q2 chain P01..06 Q3 ok=True | golden opju path |
| b-1 first fail | Q3 detail starts with first fail code | table |
| c-1 frozen | Q3 ProbeResult immutable | |

### O1-P-07 L8 golden path bits

| B# | tag | example |
|----|-----|---------|
| B1 | path | `G:\공유\…\Ni5_Ce5_Al2O3.opju` |
| B2 | ok | true |
| B3 | detail | `""` |

---

## O1-P L7 체인 (공통 PRE)

```
Q1-L1 DEP O0
Q1-L2 T   path: str
Q1-L3 F   fixture loaded (dry) or skip (live)
Q2-L1 C   probe_*()
Q3-L1 E   ProbeResult.ok matches table
Q3-L2 E   detail matches on fail
```
