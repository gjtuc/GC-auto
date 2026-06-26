# O0-S — Series / Gap (16 L4)

> module: `o0_series` · GC3 gap: Cycle 99–100 NaN · 107 rows

---

## O0-S-01 — _is_missing

| L4 | L7 POST | L8 |
|----|---------|-----|
| a-1 None | Q3-L1 E True | `null` |
| b-1 NaN | Q2-L1 A pd.isna/nan Q3 True | `float('nan')` |
| c-1 0.0 | Q3-L1 E False | `0.0` |
| d-1 "" | Q3-L1 E False (empty not missing) | `""` |

---

## O0-S-02 — AS_EMPTY

| L4 | L7 | L8 |
|----|-----|-----|
| a-1 len | Q3-L1 L len(out)==len(in) | len 4 |
| b-1 NaN→"" | Q3-L1 E out[i]=="" | idx 1,2 nan |
| c-1 keep | Q3-L1 E out[0]==1.0 | finite |

---

## O0-S-03 — AS_NAN

| L4 | L7 | L8 |
|----|-----|-----|
| a-1 len | Q3-L1 L len==2 | |
| b-1 isnan | Q3-L1 A math.isnan(out[1]) | |

---

## O0-S-04 — SKIP_ROWS

| L4 | L7 | L8 |
|----|-----|-----|
| a-1 len↓ | Q3-L1 L len(out)<len(in) | `[1,nan,3]` → 2 |
| b-1 gap only | Q3-L1 E out==[1.0,3.0] | order kept |

---

## O0-S-05 — column_to_origin_list input

| L4 | L7 | L8 |
|----|-----|-----|
| a-1 list | Q1-L2 T list | `[1.0,nan]` |
| b-1 Series | Q2-L1 C `.tolist()` then dispatch | pd.Series |
| c-1 empty | Q3-L1 E `== []` | `[]` |

---

## O0-S-06 — GC3 gap scenario

| L4 | L7 | L8 |
|----|-----|-----|
| a-1 107 rows | Q3-L1 L len==107 | FX-GC3-Ni5 row count |
| b-1 idx 99,100 | Q3-L1 E out[99]=="" Q3-L2 E out[100]=="" | not `0.0` |

### FX-GC3-Ni5 (L6 shared)

| L8 bit | tag | value |
|--------|-----|-------|
| B1 | sample | `20260620 DRE(1.5) 600C Ni5_Ce5_Al2O3` |
| B2 | rows | 107 |
| B3 | gap_idx | `[99,100]` |
| B4 | gap_in | `[nan,nan]` |
| B5 | gap_out_AS_EMPTY | `["",""]` |
| B6 | policy | `AS_EMPTY` |

**촉매 갭:** 현재 `tolist()` — O7에서 O0-S-06-b-1 적용 목표.
