# data_pc_origin — 구현 순서 (기초 → 상위)

> **규칙:** 아래 번호 **1개만** 구현 → `verify --gate` PASS → 다음 번호.  
> 매 단계 후 **`--o0`** · **`--o1`** · O2 이후 **`--o2`** 합본 PASS 유지.

---

## Phase 0 — Registry (originpro 불필요)

| # | ID | 산출물 | verify |
|---|-----|--------|--------|
| 0.1 | RG-F-01 | `gates/registry.py` — gate DAG·순서 | **PASS** |
| 0.2 | RG-V-01 | `verify --gate ID` | **PASS** |
| 0.3 | RG-V-03 | LOCKED (exit 2) | **PASS** |
| 0.4 | RG-V-05 | `verify --rollup O0-L1-K` | **PASS** |

---

## Phase 1 — O0 Pure (L4 리프, 형제 순서)

| # | rollup | L4 | module | 상태 |
|---|--------|-----|--------|------|
| 1 | O0-L1-K | O0-K-01-a-1 … O0-K-02-b-1 (9) | `o0_keys.py` | **PASS** |
| 2 | O0-L1-I | O0-I-01-a-1 … O0-I-02-b-1 (9) | `o0_identity.py` | **PASS** |
| 3 | O0-L1-C | O0-C-01-a-1 … O0-C-03-a-1 (11) | `o0_comments.py` | **PASS** |
| 4 | O0-L1-S | O0-S-01-a-1 … O0-S-06-b-1 (16) | `o0_series.py` | **PASS** |
| 5 | O0-L1-M | O0-M-01-a-1 … O0-M-03-b-1 (10) | `o0_mapping.py` | **PASS** |
| 6 | O0-L1-T | O0-T-01-a-1 … O0-T-04-a-1 (6) | `o0_types.py` | **PASS** |
| 7 | **O0** | 위 61 gate 합본 | — | **PASS** `--rollup O0` |

---

## Phase 2 — O1 Probes (O0 전 L4 PASS 후)

| # | rollup | gate 수 |
|---|--------|---------|
| 8 | O1-P | 15 | `o1_opju_path.py` | **PASS** |
| 9 | O1-W | 7 | `o1_opju_writable.py` | **PASS** |
| 10 | O1-I | 5 | `o1_origin_install.py` | **PASS** |
| 11 | **O1** | 27 + O0 선행 | — | **PASS** `--rollup O1` |

---

## Phase 3 — O2 Gate (O1 PASS 후)

| # | rollup | L4 | module | 상태 |
|---|--------|-----|--------|------|
| 12 | O2-E | O2-E-01-a-1 … O2-E-04-a-1 (6) | `o2_env.py` | **PASS** |
| 13 | O2-L | O2-L-01-a-1 … O2-L-05-a-1 (9) | `o2_pipeline_lock.py`, `o2_origin_lock.py` | **PASS** |
| 14 | O2-G | O2-G-01-a-1 … O2-G-06-a-1 (6) | `o2_gate_chain.py` | **PASS** |
| 15 | **O2** | 21 + O0+O1 선행 | — | **PASS** `--rollup O2` |

---

## Phase 4 — O3 Session (O2 PASS 후)

| # | rollup | L4 | module | 상태 |
|---|--------|-----|--------|------|
| 16 | O3-S | O3-S-01-a-1 … O3-S-06-a-1 (8) | `o3_import.py`, `o3_session.py` | **PASS** |
| 17 | O3-P | O3-P-01-a-1 … O3-P-04-a-1 (4) | `o3_plugins.py` | **PASS** |
| 18 | **O3** | 12 + O0..O2 선행 | — | **PASS** `--rollup O3` |

---

## Phase 4b — O4 Project (O3 PASS 후)

| # | rollup | L4 | module | 상태 |
|---|--------|-----|--------|------|
| 19 | O4-V | O4-V-01-a-1 (1) | `o4_project.py` (validate) | **PASS** |
| 20 | O4-O | O4-O-01-a-1 … O4-O-02-a-1 (4) | `o4_project.py` (open) | **PASS** |
| 21 | O4-S | O4-S-01-a-1 … O4-S-02-a-1 (2) | `o4_project.py` (save) | **PASS** |
| 22 | O4-R | O4-R-01-a-1 (1) | roundtrip smoke | **PASS** |
| 23 | **O4** | 8 + O0..O3 선행 | `o4_errors.py` | **PASS** `--rollup O4` |

---

## Phase 5 — O5 Worksheet ★ (O4 PASS 후, **105 core L4**)

> **마스터:** [`design/catalog/O5-REGISTRY.md`](design/catalog/O5-REGISTRY.md) · 카탈로그 `O5-I/T/M.md` · YAML `gates/O5/`

| # | rollup | L4 | module | 상태 |
|---|--------|-----|--------|------|
| 24 | O5-L2-I01 | I-01 a..l (12) | `o5_iterate.iter_pages_w` | LOCKED |
| 25 | O5-L2-I02 | I-02 a..l (12) | `o5_iterate.iter_worksheets` | LOCKED |
| 26 | O5-L1-I | 24 | — | LOCKED |
| 27 | O5-L2-T01..04 | T-01..04 (27) | `o5_text.py` | LOCKED |
| 28 | O5-L1-T | 27 | — | LOCKED |
| 29 | O5-L2-M01 | M-01 a..n (14) | `o5_match.keyword_in_text` | LOCKED |
| 30 | O5-L2-M02 | M-02 a..n (14) | `find_worksheet_for_keyword` | LOCKED |
| 31 | O5-L2-M03 | M-03 a..r (18) | `resolve_worksheets` | LOCKED |
| 32 | O5-L2-M04 | M-04 a..h (8) | `report_missing` | LOCKED |
| 33 | O5-L1-M | 54 | — | LOCKED |
| 34 | **O5** | **105** + O0..O4 | — | **PASS** |
| 35 | O5-DEBUG | 5 | `o5_debug.py` | **PASS** `--o5-debug` |
| 36 | O5-E2E / R | 7 | `o5_meta_gates.py` | **PASS** `--o5-meta` |

**증상:** #92 `O5-M-03-l-1` · DEBUG-02 · E2E-02

**구현 규칙:** registry #1부터 **1 gate** → verify → 승인 → #2 …

---

## Phase 5b–7 — O6 Column → O9 Facade

| Phase | L0 | L4(설계) | 선행 |
|-------|-----|----------|------|
| 5b | O6 column | 12 | O5 |
| 5c | O7 write | 9 | O6 |
| 6 | O8 job | 11 | O5–O7 |
| 7 | O9 facade + E2E + P | 10 | O8 |
| 8 | O9-L live harness | 3 | O9-P | **PASS** `--o9-live` |

---

## Phase 8 — 파이프라인 (O9 PASS + 승인)

`촉매 반응 계산.py` 1곳 → `update_from_dataframe` · `DATA_PC_SKIP_ORIGIN=0`

---

## 현재 작업 포인터

```
DONE: O0..O9 (287) + O5-DEBUG (5) + O9-L (3) + Phase 8 pipeline — verify --o9-live PASS
NEXT: live opju 1회 — DATA_PC_SKIP_ORIGIN=0 · DATA_PC_LIVE_OPJU=<G:\…Ni5.opju>
```

```bash
# 설계 참조
design/catalog/O5-I.md
design/catalog/FX-O5-opju-mock.yaml
# 구현 시작 시
python -m data_pc_origin.verify --gate O5-I-01-a-1
python -m data_pc_origin.verify --rollup O5-L1-I
```
