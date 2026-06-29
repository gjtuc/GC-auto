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
DONE: O0..O9-EXT + P0..P27-EXT (198) — verify --p27 PASS
IMAP: python -m data_pc_origin.live_imap --probe
      DATA_PC_SKIP_ORIGIN=0 python -m data_pc_origin.live_imap
RUNTIME: python -m data_pc_origin.live_runtime --dry
         python -m data_pc_origin.live_runtime --dry-job
SUPERVISOR: python -m data_pc_origin.live_supervisor
            python -m data_pc_runtime.verify --dry-supervisor
WATCH: python -m data_pc_origin.live_watch
       DATA_PC_LEGACY_WATCH=1  # 구 DataPcWatchRunner
ENV: python -m data_pc_origin.live_env
E2E: python -m data_pc_origin.live_production_e2e
     DATA_PC_E2E_LIVE=1 python -m data_pc_origin.live_production_e2e --live
RUN: python -m data_pc_origin.live_production_run --validate-fixture
     DATA_PC_E2E_LIVE=1 python -m data_pc_origin.live_production_run
READY: python -m data_pc_origin.live_readiness
       python -m data_pc_origin.live_readiness --tick
CUTOVER: python -m data_pc_origin.live_cutover
         DATA_PC_CUTOVER_APPLY=1 python -m data_pc_origin.live_cutover --apply
AUTOSTART: python -m data_pc_origin.live_autostart
GITHUB: python -m data_pc_origin.live_github_snapshot
        python -m data_pc_origin.live_github_snapshot --sync
        DATA_PC_GITHUB_PUSH=1 python -m data_pc_origin.live_github_snapshot --push
OPS: python -m data_pc_origin.live_ops_rollup
     python -m data_pc_origin.live_ops_rollup --tick
NATIVE: python -m data_pc_origin.live_native_production
        DATA_PC_NATIVE_LIVE=1 python -m data_pc_origin.live_native_production --live
WATCH: python -m data_pc_origin.live_watch_resident
       python -m data_pc_origin.live_watch_resident --delegate
GITHUB: python -m data_pc_origin.live_github_refresh
        python -m data_pc_origin.live_github_refresh --sync
        DATA_PC_GITHUB_PUSH=1 python -m data_pc_origin.live_github_refresh --push
```

## Phase 9 — P층 (메일·엑셀 ↔ Origin)

> 마스터: [`DESIGN_P.md`](DESIGN_P.md) · [`design/catalog/P-REGISTRY.md`](design/catalog/P-REGISTRY.md)

| # | rollup | L4 | module | 상태 |
|---|--------|-----|--------|------|
| 37 | P0-T | 6 | `p0_types.py` | **PASS** |
| 38 | P0-R | 4 | `p0_routing.py` | **PASS** |
| 39 | **P0** | 10 | — | **PASS** `--p0` |
| 40 | P1-P | 8 | `p1_payload.py` | **PASS** |
| 41 | **P1** | 8 | — | **PASS** `--p1` |
| 42 | P2 | 6 | `p2_paths.py` | **PASS** |
| 43 | **P2** | 6 | — | **PASS** `--p2` |
| 44 | P3-S | 4 | `p3_skip.py` | **PASS** |
| 45 | **P3** | 4 | — | **PASS** `--p3` |
| 46 | P4-O/M/R | 6 | `p4_origin_stage.py` | **PASS** |
| 47 | **P4** | 6 | — | **PASS** `--p4` |
| 48 | P5-W/P/R | 9 | `p5_workflow.py` | **PASS** |
| 49 | **P5** | 9 | — | **PASS** `--p5` |
| 50 | P6 | 8 | `p6_catalyst_adapter.py` | **PASS** |
| 51 | **P6** | 8 | — | **PASS** `--p6` |
| 52 | P7 | 4 | `p7_mail_hook.py` | **PASS** |
| 53 | **P7** | 4 | — | **PASS** `--p7` |
| 54 | **P** | 55 | 합본 | **PASS** `--p` |
| 55 | P8-B | 4 | `workflow_bridge.py` | **PASS** |
| 56 | **P8** | 4 | — | **PASS** `--p8` |
| 57 | P9-L | 4 | `live_workflow.py` | **PASS** |
| 58 | **P9-EXT** | 63 | P + P9-L | **PASS** `--p9-live` |
| 59 | P10-F | 3 | `live_full_archive.py` | **PASS** |
| 60 | P10-M | 4 | `live_mail.py` | **PASS** |
| 61 | **P10-EXT** | 70 | P9-EXT + P10 | **PASS** `--p10` |
| 62 | P11-K | 4 | `live_kch.py` | **PASS** |
| 63 | **P11-EXT** | 74 | P10-EXT + P11-K | **PASS** `--p11` |
| 64 | P12-F | 4 | `live_full_native.py` | **PASS** |
| 65 | **P12-EXT** | 78 | P11-EXT + P12-F | **PASS** `--p12` |
| 66 | P13-I | 4 | `p13_imap_adapter.py` | **PASS** |
| 67 | P13-M | 4 | `live_imap.py` | **PASS** |
| 68 | **P13-EXT** | 86 | P12-EXT + P13 | **PASS** `--p13` |
| 69 | P14-R | 4 | `p14_runtime_bridge.py` | **PASS** |
| 70 | P14-J | 4 | `live_runtime.py` | **PASS** |
| 71 | **P14-EXT** | 94 | P13-EXT + P14 | **PASS** `--p14` |
| 72 | P15-S | 4 | `layer4_supervisor.py` | **PASS** |
| 73 | P15-H | 4 | `live_supervisor.py` | **PASS** |
| 74 | **P15-EXT** | 102 | P14-EXT + P15 | **PASS** `--p15` |
| 75 | P16-W | 4 | `p16_watch_bridge.py` | **PASS** |
| 76 | P16-H | 4 | `live_watch.py` | **PASS** |
| 77 | **P16-EXT** | 110 | P15-EXT + P16 | **PASS** `--p16` |
| 78 | P17-E | 4 | `p17_env_config.py` | **PASS** |
| 79 | P17-H | 4 | `live_env.py` | **PASS** |
| 80 | **P17-EXT** | 118 | P16-EXT + P17 | **PASS** `--p17` |
| 81 | P18-P | 4 | `p18_production_e2e.py` | **PASS** |
| 82 | P18-L | 4 | `live_production_e2e.py` | **PASS** |
| 83 | **P18-EXT** | 126 | P17-EXT + P18 | **PASS** `--p18` |
| 84 | P19-V | 4 | `p19_live_assert.py` | **PASS** |
| 85 | P19-R | 4 | `live_production_run.py` | **PASS** |
| 86 | **P19-EXT** | 134 | P18-EXT + P19 | **PASS** `--p19` |
| 87 | P20-M | 4 | `p20_readiness.py` | **PASS** |
| 88 | P20-H | 4 | `live_readiness.py` | **PASS** |
| 89 | **P20-EXT** | 142 | P19-EXT + P20 | **PASS** `--p20` |
| 90 | P21-C | 4 | `p21_cutover.py` | **PASS** |
| 91 | P21-H | 4 | `live_cutover.py` | **PASS** |
| 92 | **P21-EXT** | 150 | P20-EXT + P21 | **PASS** `--p21` |
| 93 | P22-A | 4 | `p22_autostart.py` | **PASS** |
| 94 | P22-H | 4 | `live_autostart.py` | **PASS** |
| 95 | **P22-EXT** | 158 | P21-EXT + P22 | **PASS** `--p22` |
| 96 | P23-G | 4 | `p23_github_snapshot.py` | **PASS** |
| 97 | P23-H | 4 | `live_github_snapshot.py` | **PASS** |
| 98 | **P23-EXT** | 166 | P22-EXT + P23 | **PASS** `--p23` |
| 99 | P24-O | 4 | `p24_ops_rollup.py` | **PASS** |
| 100 | P24-H | 4 | `live_ops_rollup.py` | **PASS** |
| 101 | **P24-EXT** | 174 | P23-EXT + P24 | **PASS** `--p24` |
| 102 | P25-N | 4 | `p25_native_live.py` | **PASS** |
| 103 | P25-H | 4 | `live_native_production.py` | **PASS** |
| 104 | **P25-EXT** | 182 | P24-EXT + P25 | **PASS** `--p25` |
| 105 | P26-W | 4 | `p26_watch_resident.py` | **PASS** |
| 106 | P26-H | 4 | `live_watch_resident.py` | **PASS** |
| 107 | **P26-EXT** | 190 | P25-EXT + P26 | **PASS** `--p26` |
| 108 | P27-G | 4 | `p27_github_refresh.py` | **PASS** |
| 109 | P27-H | 4 | `live_github_refresh.py` | **PASS** |
| 110 | **P27-EXT** | 198 | P26-EXT + P27 | **PASS** `--p27` |

```bash
# P27 — GitHub refresh (P24–P26)
python -m data_pc_origin.live_github_refresh
python -m data_pc_origin.live_github_refresh --sync
DATA_PC_GITHUB_PUSH=1 python -m data_pc_origin.live_github_refresh --push
python -m data_pc_origin.verify --p27

# P26 — watch resident smoke
python -m data_pc_origin.live_watch_resident
python -m data_pc_origin.live_watch_resident --delegate
python -m data_pc_origin.verify --p26

# P25 — native env production live (no override)
python -m data_pc_origin.live_native_production
DATA_PC_NATIVE_LIVE=1 python -m data_pc_origin.live_native_production --live
python -m data_pc_origin.verify --p25

# P24 — operational closure rollup
python -m data_pc_origin.live_ops_rollup
python -m data_pc_origin.live_ops_rollup --tick
python -m data_pc_origin.verify --p24

# P23 — GitHub feat/data-pc-origin snapshot
python -m data_pc_origin.live_github_snapshot
python -m data_pc_origin.live_github_snapshot --sync
DATA_PC_GITHUB_PUSH=1 python -m data_pc_origin.live_github_snapshot --push
python -m data_pc_origin.verify --p23

# P22 — autostart / watch integration smoke
python -m data_pc_origin.live_autostart
python -m data_pc_origin.verify --p22

# P21 — operational cutover
python -m data_pc_origin.live_cutover
DATA_PC_CUTOVER_APPLY=1 python -m data_pc_origin.live_cutover --apply
python -m data_pc_origin.verify --p21
python -m data_pc_origin.live_readiness --tick
python -m data_pc_origin.verify --p20

# P19 — live run + artifact validation
python -m data_pc_origin.live_production_run --validate-fixture
DATA_PC_E2E_LIVE=1 python -m data_pc_origin.live_production_run
python -m data_pc_origin.verify --p19

# P18 — production full E2E
python -m data_pc_origin.live_production_e2e
python -m data_pc_origin.live_production_e2e --prep-live
DATA_PC_E2E_LIVE=1 python -m data_pc_origin.live_production_e2e --live
python -m data_pc_origin.verify --p18

# P17 — origin env effective config
python -m data_pc_origin.live_env
python -m data_pc_origin.verify --p17

# P16 — --watch → runtime supervisor
python -m data_pc_origin.live_watch
python -m data_pc_origin.verify --p16

# P15 — Supervisor ↔ resolve_job_pipeline
python -m data_pc_origin.live_supervisor
python -m data_pc_runtime.verify --dry-supervisor
python -m data_pc_origin.verify --p15

# P14 — JobRunner ↔ live_imap
python -m data_pc_origin.live_runtime --dry
python -m data_pc_origin.live_runtime --dry-job
DATA_PC_ORIGIN_PIPELINE=1 python -m data_pc_origin.verify --p14

# P13 live — IMAP → inbox → FULL_ARCHIVE
python -m data_pc_origin.live_imap --probe
python -m data_pc_origin.live_imap --fetch-only
DATA_PC_SKIP_ORIGIN=0 python -m data_pc_origin.live_imap
DATA_PC_IMAP_LIVE=1 python -m data_pc_origin.verify --p13  # live IMAP unittest
```
