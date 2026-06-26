# O0-M — Mapping (10 L4)

> module: `o0_mapping` · 촉매 `ORIGIN_MAPPING` 8항목 동기

---

## O0-M-01 — DEFAULT_ORIGIN_MAPPING

| L4 | L7 | L8 |
|----|-----|-----|
| a-1 len 8 | Q3-L1 L | 8 |
| b-1 H2 key | Q3-L1 IN | `"H2 Yield (%)" in m` |
| c-1 CH4 DRM | Q3-L1 IN | `"CH4 Conversion (%)"` or DRM col name |

### 8키 L8 golden (B1–B8)

| B# | df_col | origin_kw |
|----|--------|-----------|
| B1 | H2 Yield (%) | H2 yield |
| B2 | CO2 Conversion (%) | CO2 conversion |
| B3 | CO Selectivity (%) | CO selectivity |
| B4 | CH4 Conversion (%) | CH4 conversion |
| B5 | H2/CO ratio | H2/CO |
| B6 | (… 나머지 3 — 촉매 ORIGIN_MAPPING 1:1) | |

---

## O0-M-02 — validate_mapping

| L4 | L7 | L8 |
|----|-----|-----|
| a-1 {} | Q3-L1 X MappingValidationError | `{}` |
| b-1 empty df_col | Q3-L1 X | `{"" : "kw"}` |
| c-1 empty kw | Q3-L1 X | `{"col": ""}` |
| d-1 dup kw | Q2-L1 C norm values Q3 dup detect | two cols → same norm |
| e-1 copy | Q3-L1 NE | `id(out)!=id(DEFAULT)` on success |

---

## O0-M-03 — mapping_for_df

| L4 | L7 | L8 |
|----|-----|-----|
| a-1 skip list | Q3-L1 IN | missing col in skipped |
| b-1 subset | Q3-L1 E | only cols in df.columns |

**O5 연결:** O5-M-03-c-1 — df에 없는 열은 miss list에서 제외.
