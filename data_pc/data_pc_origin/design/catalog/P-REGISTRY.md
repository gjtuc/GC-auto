# P-REGISTRY — 메일·엑셀 ↔ Origin 연결 (55 L4)

> 형제 순서 = `gates/registry.py` `P_IMPLEMENTATION_ORDER` = verify 체인.

## L2 → L4 맵

### P0 Pure (10) — **PASS**

| # | gate_id | L2 | assert |
|---|---------|-----|--------|
| 1 | P0-T-01-a-1 | T | `WorkflowMode` 3값 |
| … | … | | |
| 10 | P0-R-04-a-1 | R | `skip_stage4` on options |

### P1 Payload (8) — **PASS**

| # | gate_id | assert |
|---|---------|--------|
| 11 | P1-P-01-a-1 | `Stage2Metadata` |
| 12 | P1-P-02-a-1 | `validate_sample_name` |
| 13 | P1-P-03-a-1 | `validate_identity_key` |
| 14 | P1-P-04-a-1 | full df 8/8 mapping |
| 15 | P1-P-05-a-1 | DRE partial 6 cols |
| 16 | P1-P-06-a-1 | skipped 2 cols |
| 17 | P1-P-07-a-1 | `assemble_stage2_metadata` |
| 18 | P1-P-08-a-1 | `build_payload_from_stage2` |

### P2 Paths (6) — **PASS**

| # | gate_id | assert |
|---|---------|--------|
| 19 | P2-V-01-a-1 | `normalize_opju_path` G: |
| 20 | P2-V-02-a-1 | `is_g_drive_path` |
| 21 | P2-P-01-a-1 | suffix `.opju` |
| 22 | P2-S-01-a-1 | save in place |
| 23 | P2-S-02-a-1 | `_Updated.opju` |
| 24 | P2-R-01-a-1 | `build_stage4_paths` |

### P3 Skip (4) — **PASS**

| # | gate_id | assert |
|---|---------|--------|
| 25 | P3-S-01-a-1 | env skip |
| 26 | P3-S-02-a-1 | explicit override |
| 27 | P3-S-03-a-1 | `should_execute_stage4` |
| 28 | P3-S-04-a-1 | skip UX message |

### P4 Origin stage (6) — **PASS**

| # | gate_id | assert |
|---|---------|--------|
| 29 | P4-O-01-a-1 | mock 8 sheets |
| 30 | P4-O-02-a-1 | bridge kwargs |
| 31 | P4-M-01-a-1 | runner injection |
| 32 | P4-M-02-a-1 | skip no call |
| 33 | P4-R-01-a-1 | skipped result |
| 34 | P4-R-02-a-1 | ok=False |

### P5 Workflow (9) — **PASS**

| # | gate_id | assert |
|---|---------|--------|
| 35 | P5-W-01-a-1 | OPJU (2,4) |
| 36 | P5-W-02-a-1 | CALC (2,) |
| 37 | P5-W-03-a-1 | FULL (2,3,4) |
| 38 | P5-W-04-a-1 | OPJU mock run |
| 39 | P5-W-05-a-1 | skip stage4 |
| 40 | P5-P-01-a-1 | payload save mode |
| 41 | P5-R-01-a-1 | CALC ok |
| 42 | P5-R-02-a-1 | stage2 fail |
| 43 | P5-R-03-a-1 | stage4 fail |

### P6 Catalyst adapter (8) — **PASS**

| # | gate_id | assert |
|---|---------|--------|
| 44–51 | P6-* | importlib mock |

### P7 Mail E2E (4) — **PASS**

| # | gate_id | assert |
|---|---------|--------|
| 52 | P7-M-01-a-1 | xlsx parse |
| 53 | P7-M-02-a-1 | mail workflow |
| 54 | P7-R-01-a-1 | CALC ok |
| 55 | P7-R-02-a-1 | pdf reject |

## Rollup

| rollup_id | gates |
|-----------|-------|
| P0-T | #1–6 |
| P0-R | #7–10 |
| P0 | #1–10 |
| P1 | #11–18 |
| … | |
| **P** | #1–55 |
