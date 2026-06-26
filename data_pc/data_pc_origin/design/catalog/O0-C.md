# O0-C — Comments (11 L4)

> module: `o0_comments`

---

## O0-C-01-a-1 — None date

| L7 | Q3-L1 E | `parse_comment_date(None) is None` |

## O0-C-01-b-1 — lead 8 digits

| L7 | Q2-L1 REG | `^(\d{8})` |
| L7 | Q3-L1 E | group == `"20260620"` |
| L8 | FA-B1 | `"20260620 DRE(1.5)@600°C Ni5"` |

## O0-C-01-c-1 — mid digits ignored

| L7 | Q3-L1 E | `"prefix20260620suffix"` → None or lead-only rule |
| L8 | FB-B1 | no lead 8 → None |

## O0-C-01-d-1 — 7 digits → None

| L7 | Q3-L1 E | `"2026062 x"` → None |

## O0-C-01-e-1 — strip before parse

| L7 | Q2-L1 C | strip input |
| L7 | Q3-L1 E | `"  20260620 …"` → `"20260620"` |

---

## O0-C-02-a-1 — comment None → False

| L7 | Q3-L1 E | `comment_matches_identity(None, key) is False` |

## O0-C-02-b-1 — key None → False

| L7 | Q3-L1 E | key None → False |

## O0-C-02-c-1 — date mismatch

| L7 | Q2-L1 E | dates differ |
| L7 | Q3-L1 E | False |
| L8 | FA-B1 comment | `"20260619 other"` |
| L8 | FA-B2 key | FX-IDENTITY-DRE |

## O0-C-02-d-1 — date+tokens match

| L7 | Q2-L1 E | same date |
| L7 | Q2-L2 B | token score ≥ thr |
| L7 | Q3-L1 E | True |
| L8 | FA-B1 | `"20260620 DRE(1.5)@600°C 600CNi5_Ce5_Al2O3"` |
| L8 | FA-B2 | FX-IDENTITY-DRE |

## O0-C-02-e-1 — case insensitive

| L7 | Q2-L1 C | casefold comment vs key |
| L7 | Q3-L1 E | DRE/dre equivalent |

---

## O0-C-03-a-1 — sort key tail

| L7 | Q3-L1 O | no date → sort key > any dated |
| L8 | FA-B1 | `"no date"` → large key |
