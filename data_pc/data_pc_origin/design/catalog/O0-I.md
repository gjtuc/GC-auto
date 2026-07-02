# O0-I — Identity tokens (14 L4)

> module: `o0_identity.identity_match_tokens` · regex: 촉매 L791–795 동일

---

## O0-I-01-a-1 — empty → ∅

| L7 | Kind | Spec |
|----|------|------|
| Q2-L1 | C | `identity_match_tokens("")` |
| Q3-L1 | L | `len(out)==0` |
| Q3-L2 | T | `isinstance(out, set)` |

---

## O0-I-01-b-1 — dre token

| L7 | Kind | Spec |
|----|------|------|
| Q3-L1 | IN | `"dre" in tokens` |
| FA-B1 | in | `"dre(1.5) 600c ni5_ce5_al2o3"` |

---

## O0-I-01-c-1 — drme token

| L7 | Kind | Spec |
|----|------|------|
| Q3-L1 | IN | `"drme" in tokens` |
| FA-B1 | in | `"20260620 DRME(0.5)@600°C"` |

---

## O0-I-01-d-1 — @600 temperature

| L7 | Kind | Spec |
|----|------|------|
| Q2-L1 | REG | find `@\d+` |
| Q3-L1 | IN | any t.startswith("@") |
| FA-B1 | token | `"@600"` |

---

## O0-I-01-e-1 — ni5 catalyst

| L7 | Kind | Spec |
|----|------|------|
| Q3-L1 | IN | `"ni5" in tokens` |
| Q3-L2 | IN | `"ce5" in tokens` (same sample) |
| FA-B1 | in | FX-SAMPLE-DRE |

---

## O0-I-01-f-1 — exclude 1-char

| L7 | Kind | Spec |
|----|------|------|
| Q3-L1 | NE | `"a" not in tokens` |
| Q3-L2 | ORD | all `len(t)>=2 or t.endswith('g')` |
| FB-B1 | forbid | `"a"` |

---

## O0-I-01-g-1 — 0.15g allowed

| L7 | Kind | Spec |
|----|------|------|
| Q3-L1 | IN | `"0.15g" in tokens` |
| FA-B1 | in | `"0.15g dre"` |

---

## O0-I-02-a-1 — match score ratio

| L7 | Kind | Spec |
|----|------|------|
| Q2-L1 | C | `score = len(ref & tokens)/len(ref)` |
| Q3-L1 | E | table cases |
| FA-B1 | ref | `{dre,@600,ni5}` |
| FA-B2 | tokens | `{dre,ni5,ce5}` → 2/3 |

---

## O0-I-02-b-1 — threshold max(2, 0.6*n)

| L7 | Kind | Spec |
|----|------|------|
| Q2-L1 | C | `thr = max(2, ceil(0.6*len(ref)))` |
| Q3-L1 | E | n=3→2, n=5→3, n=2→2 |
| FA-B1 | n | 3 |
| FA-B2 | thr | 2 |

---

## O0-I-03 — Task C (% · @ · / 촉매 · 장비 접미사)

> `identity_match_tokens` 확장 + `comment_matches_identity` 통합

## O0-I-03-a-1 — 농도 토큰 1.5

| L7 | Q3-L1 IN | `"1.5" in tokens` |
| FA-B1 | in | `dre(1.5) 600c ni5_ce5_al2o3` |

## O0-I-03-b-1 — 600C → @600

| L7 | Q3-L1 IN | `"@600" in tokens` |
| FA-B1 | in | 파일명 `600c` stem |

## O0-I-03-c-1 — 슬래시 촉매

| L7 | Q3-L1 IN | ni5 · al2o3 in `ni5/ce5/al2o3` |

## O0-I-03-d-1 — Task C Comments ↔ identity

| L7 | Q3-L1 E | `comment_matches_identity` True |
| FA-B1 | comment | `…Ni5/Ce5/Al2O3_OCM 장비` |
| FA-B2 | key | FX-IDENTITY-DRE |

## O0-I-03-e-1 — 장비 라벨 제외

| L7 | Q3-L1 NE | `"장비" not in tokens` |
