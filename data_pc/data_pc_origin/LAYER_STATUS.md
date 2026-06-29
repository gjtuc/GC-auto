# data_pc_origin — 층별 검증 상태

| 문서 | 내용 |
|------|------|
| `DESIGN.md` | L0~L9 모듈·함수 수준 |
| `DESIGN_ATOMIC.md` | **L4 나노 ~250+ 게이트** (4단계 분해) |
| `DESIGN_NANO.md` | **L5 쿼크 ~900 · L6 포톤 ~450** (6단계·RG/ER/SM/FX) |
| `DESIGN_LEPTON.md` | **L7 레pton ~2400 · L8 bit ~1200** (8단계) |
| `design/catalog/` | **O0 61** · O1-P · **O5 117 L4** ([`O5-REGISTRY.md`](design/catalog/O5-REGISTRY.md)) |

상세 ID: **L4** `DESIGN_ATOMIC` → **L5/L6** `DESIGN_NANO` → **L7/L8** `DESIGN_LEPTON` / `design/catalog/`.

| 층 | 상태 | 검증 명령 | 비고 |
|----|------|-----------|------|
| O0 pure | **PASS** (합본) | `python -m data_pc_origin.verify --o0` | unit=PASS |
| O0 L4 리프 | **PASS** (61 L4) | `verify --rollup O0` | 61 gates |
| O1 probes | **PASS** (27 L4) | `verify --rollup O1` | 27 gates |
| O2 gates | **PASS** (21 L4) | `verify --rollup O2` | 21 gates |
| O3 session | **PASS** (12 L4) | `verify --rollup O3` | 12 gates |
| O4 project | **PASS** (8 L4) | `verify --rollup O4` | 8 gates |
| O5-I iterate | **PASS** (24 L4) | `verify --rollup O5-L1-I` | 24 gates |
| O5-T text | **PASS** (27 L4) | `verify --rollup O5-L1-T` | 27 gates |
| O5-M match | **PASS** (54 L4) | `verify --rollup O5-L1-M` | 54 gates |
| O5 worksheet | **PASS** (core 105/105) | `verify --rollup O5-M` | I+T+M |
| O5-DEBUG | **PASS** (5/5) | `verify --o5-debug` | #106–110 |
| O5 meta E2E+R | **PASS** (7/7) | `verify --rollup O5-META` | #111–117 |
| O6-S scan | **PASS** (4/12) | `verify --rollup O6-S` | iter_col · dated |
| O6-F find | **PASS** (4/12) | `verify --rollup O6-F` | exact · identity |
| O6-P plan | **PASS** (4/12) | `verify --rollup O6-P` | insert · occupied |
| O6-I insert | **PASS** (4/16) | `verify --rollup O6-I` | LT_execute mock |
| O6-R resolve | **PASS** (2/16) | `verify --rollup O6-R` | exact>identity>insert |
| O6 column | **PASS** (16/16) | `verify --rollup O6` | full layer |
| O7-P policy | **PASS** (3/9) | `verify --rollup O7-P` | gap · prepare |
| O7-W write | **PASS** (4/9) | `verify --rollup O7-W` | from_list mock |
| O7-G gap | **PASS** (2/9) | `verify --rollup O7-G` | idx 99·100 |
| O7 write | **PASS** (9/9) | `verify --rollup O7` | full layer |
| O8-C context | **PASS** (2/11) | `verify --rollup O8-C` | SampleContext |
| O8-J job | **PASS** (9/11) | `verify --rollup O8-J` | O5→O6→O7 |
| O8 job | **PASS** (11/11) | `verify --rollup O8` | full layer |
| O9-F facade | **PASS** (5/7) | `verify --rollup O9-F` | update_from_dataframe |
| O9-E2E mock | **PASS** (2/7) | `verify --rollup O9-E2E` | Ni5 · gap |
| O9 facade | **PASS** (7/7) | `verify --rollup O9` | full layer |
| O9-P pipeline | **PASS** (3/3) | `verify --rollup O9-P` | bridge hook |
| O9-L live | **PASS** (3/3) | `verify --o9-live` | `live_run.py` dry skip |
| Pipeline | **WIRED** | `촉매 반응 계산.py` → `run_origin_update` | SKIP unchanged |
| P0 workflow | **PASS** (10/10) | `verify --p0` | types·routing |
| P1 payload | **PASS** (8/8) | `verify --p1` | metadata·mapping |
| P2 paths | **PASS** (6/6) | `verify --p2` | opju·save |
| P3 skip | **PASS** (4/4) | `verify --p3` | SKIP_ORIGIN |
| P4 origin | **PASS** (6/6) | `verify --p4` | mock bridge |
| P5 workflow | **PASS** (9/9) | `verify --p5` | route×skip |
| P6 adapter | **PASS** (8/8) | `verify --p6` | importlib mock |
| P7 mail | **PASS** (4/4) | `verify --p7` | mail→P5 |
| **P** | **PASS** (59/59) | `verify --p` | P0..P8 |
| P8 bridge | **PASS** (4/4) | `verify --p8` | 촉매 위임 |
| P9-L live | **PASS** (4/4) | `verify --p9-live` | `live_workflow.py` |
| P10-F live | **PASS** (3/3) | `verify --p10` | FULL_ARCHIVE in-place |
| P10-M live | **PASS** (4/4) | `verify --p10` | mail sim → `_Updated.opju` |
| **P10-EXT** | **PASS** (70/70) | `verify --p10` | P9-EXT + P10 |
| P11-K live | **PASS** (4/4) | `verify --p11` | KCH native process_excel |
| **P11-EXT** | **PASS** (74/74) | `verify --p11` | P10-EXT + P11-K |
| P12-F live | **PASS** (4/4) | `verify --p12` | FULL native s2+s3 |
| **P12-EXT** | **PASS** (78/78) | `verify --p12` | P11-EXT + P12-F |
| P13-I probe | **PASS** (4/4) | `verify --p13` | IMAP prep · masked |
| P13-M mail | **PASS** (4/4) | `verify --p13` | fetch → P7 → P8 |
| **P13-EXT** | **PASS** (86/86) | `verify --p13` | P12-EXT + P13 |
| P14-R bridge | **PASS** (4/4) | `verify --p14` | RuntimePipelineResult |
| P14-J job | **PASS** (4/4) | `verify --p14` | JobRunner dry-job |
| **P14-EXT** | **PASS** (94/94) | `verify --p14` | P13-EXT + P14 |
| P15-S supervisor | **PASS** (4/4) | `verify --p15` | resolve in L4 |
| P15-H harness | **PASS** (4/4) | `verify --p15` | dry tick |
| **P15-EXT** | **PASS** (102/102) | `verify --p15` | P14-EXT + P15 |
| P16-W watch | **PASS** (4/4) | `verify --p16` | runtime delegate |
| P16-H harness | **PASS** (4/4) | `verify --p16` | dry tick |
| **P16-EXT** | **PASS** (110/110) | `verify --p16` | P15-EXT + P16 |
| P17-E env | **PASS** (4/4) | `verify --p17` | defaults · mask |
| P17-H report | **PASS** (4/4) | `verify --p17` | live_env |
| **P17-EXT** | **PASS** (118/118) | `verify --p17` | P16-EXT + P17 |
| P18-P prep | **PASS** (4/4) | `verify --p18` | production stack |
| P18-L harness | **PASS** (4/4) | `verify --p18` | dry/live gate |
| **P18-EXT** | **PASS** (126/126) | `verify --p18` | P17-EXT + P18 |
| P19-V assert | **PASS** (4/4) | `verify --p19` | row/sheet rules |
| P19-R run | **PASS** (4/4) | `verify --p19` | live_production_run |
| **P19-EXT** | **PASS** (134/134) | `verify --p19` | P18-EXT + P19 |
| P20-M manifest | **PASS** (4/4) | `verify --p20` | stack rollup |
| P20-H harness | **PASS** (4/4) | `verify --p20` | live_readiness |
| **P20-EXT** | **PASS** (142/142) | `verify --p20` | P19-EXT + P20 |
| P21-C cutover | **PASS** (4/4) | `verify --p21` | plan · apply · gate |
| P21-H harness | **PASS** (4/4) | `verify --p21` | live_cutover |
| **P21-EXT** | **PASS** (150/150) | `verify --p21` | P20-EXT + P21 |
| P22-A scan | **PASS** (4/4) | `verify --p22` | bat/VBS/watchdog |
| P22-H harness | **PASS** (4/4) | `verify --p22` | live_autostart |
| **P22-EXT** | **PASS** (158/158) | `verify --p22` | P21-EXT + P22 |
| P23-G snapshot | **PASS** (4/4) | `verify --p23` | sync plan |
| P23-H harness | **PASS** (4/4) | `verify --p23` | live_github_snapshot |
| **P23-EXT** | **PASS** (166/166) | `verify --p23` | P22-EXT + P23 |
| P24-O rollup | **PASS** (4/4) | `verify --p24` | P20–P23 manifest |
| P24-H harness | **PASS** (4/4) | `verify --p24` | live_ops_rollup |
| **P24-EXT** | **PASS** (174/174) | `verify --p24` | P23-EXT + P24 |
| P25-N native | **PASS** (4/4) | `verify --p25` | env file only |
| P25-H harness | **PASS** (4/4) | `verify --p25` | live_native_production |
| **P25-EXT** | **PASS** (182/182) | `verify --p25` | P24-EXT + P25 |
| P26-W resident | **PASS** (4/4) | `verify --p26` | native --watch |
| P26-H harness | **PASS** (4/4) | `verify --p26` | live_watch_resident |
| **P26-EXT** | **PASS** (190/190) | `verify --p26` | P25-EXT + P26 |
| P27-G refresh | **PASS** (4/4) | `verify --p27` | P24–P26 markers |
| P27-H harness | **PASS** (4/4) | `verify --p27` | live_github_refresh |
| **P27-EXT** | **PASS** (198/198) | `verify --p27` | P26-EXT + P27 |
| P28-M merge | **PASS** (4/4) | `verify --p28` | ops · sync · diff |
| P28-H harness | **PASS** (4/4) | `verify --p28` | live_merge_readiness |
| **P28-EXT** | **PASS** (206/206) | `verify --p28` | P27-EXT + P28 |
| P29-G refresh | **PASS** (4/4) | `verify --p29` | P27–P28 markers |
| P29-H harness | **PASS** (4/4) | `verify --p29` | live_p29_github_refresh |
| **P29-EXT** | **PASS** (214/214) | `verify --p29` | P28-EXT + P29 |
| P30-G push | **PASS** (4/4) | `verify --p30` | dest markers · branch |
| P30-H harness | **PASS** (4/4) | `verify --p30` | live_p30_github_push |
| **P30-EXT** | **PASS** (222/222) | `verify --p30` | P29-EXT + P30 |
| P31-M merge PR | **PASS** (4/4) | `verify --p31` | structural · remote |
| P31-H harness | **PASS** (4/4) | `verify --p31` | live_p31_merge_pr |
| **P31-EXT** | **PASS** (230/230) | `verify --p31` | P30-EXT + P31 |
| P32-G refresh | **PASS** (4/4) | `verify --p32` | P30–P31 markers |
| P32-H harness | **PASS** (4/4) | `verify --p32` | live_p32_github_refresh |
| **P32-EXT** | **PASS** (238/238) | `verify --p32` | P31-EXT + P32 |

규칙: **L4 나노 PASS → L3 → L2 → L1 → L0** · 형제는 선행 형제 PASS 후 · **사용자 승인** 후 다음 구현.

### P10 live 실행 검증 (2026-06-25)

| harness | artifact | live 결과 |
|---------|----------|-----------|
| `live_full_archive.py` | `live_full_archive_result.json` | ok · 6 sheets · save_in_place |
| `live_mail.py` | `live_mail_result.json` | ok · 6 sheets · `_Updated.opju` |

### P11-K live 실행 검증 (2026-06-28)

| harness | artifact | live 결과 |
|---------|----------|-----------|
| `live_kch.py --stage2-only` | `live_kch_result.json` | ok · **135행** · KCH inbox 원본 |
| `live_kch.py` (OPJU) | `live_kch_result.json` | ok · 6 sheets · 135행 · `_Updated.opju` |

Companion shortcut(108행)과 달리 **process_excel 직접** 경로 확인.

### P12-F live 실행 검증 (2026-06-28)

| harness | artifact | live 결과 |
|---------|----------|-----------|
| `live_full_native.py --dry` | `live_full_native_result.json` | ok · experiment_basename · DRE |
| `live_full_native.py` live | `live_full_native_result.json` | ok · **135행** · G: 폴더 갱신 · save_in_place |

P10-F(stage3 주입)과 달리 **setup_experiment_folder** 실제 호출 → `20260620 DRE(1.5) 600C Ni5_Ce5_Al2O3` 폴더 갱신.

### P13 live 실행 검증 (2026-06-28)

| harness | artifact | live 결과 |
|---------|----------|-----------|
| `live_imap --probe` | `live_imap_result.json` | ok · pending 3건 |
| `live_imap --fetch-only` | same | ok · inbox xlsx 저장 |
| `live_imap` (full) | same | ok · **161행** · 6 sheets · G: in-place |

실제 IMAP 수신 → `process_excel` → `setup_experiment_folder` → Origin (production path).

### P14 runtime bridge 실행 검증 (2026-06-28)

| harness | artifact | 결과 |
|---------|----------|------|
| `live_runtime --dry` | `live_runtime_result.json` | dry_run · pipeline 0건 |
| `live_runtime --dry-job` | same | JobRunner pipeline_done |
| `DATA_PC_ORIGIN_PIPELINE=1` + L3 | `layer3_job.run_job_once` | P14 → live_imap |

### P15 supervisor 실행 검증 (2026-06-28)

| harness | artifact | 결과 |
|---------|----------|------|
| `live_supervisor` (default) | `live_supervisor_result.json` | dry_tick · pipeline_done |
| `data_pc_runtime.verify --dry-supervisor` | — | L4 mock tick regression |

### P16 watch 실행 검증 (2026-06-28)

| harness | artifact | 결과 |
|---------|----------|------|
| `live_watch` (default) | `live_watch_result.json` | dry_tick · runtime_origin |
| `촉매 반응 계산.py --watch` | — | `run_watch_via_runtime` 위임 |

### P17 env 실행 검증 (2026-06-28)

| harness | artifact | 결과 |
|---------|----------|------|
| `live_env` | `live_env_result.json` | origin_pipeline · masked keys |
| `gc_automation.env` | — | `DATA_PC_ORIGIN_PIPELINE=1` 추가 |

### P18 production E2E 실행 검증 (2026-06-28)

| harness | artifact | 결과 |
|---------|----------|------|
| `live_production_e2e` (default) | `live_production_e2e_result.json` | dry_prep · stack |
| `--prep-live` | same | IMAP probe (optional) |
| `--live` + `DATA_PC_E2E_LIVE=1` | same | full imap workflow |

### P19 live run 실행 검증 (2026-06-28)

| harness | artifact | live 결과 |
|---------|----------|-----------|
| `live_production_run --validate-fixture` | `live_production_run_result.json` | validation ok · 161행 fixture |
| `DATA_PC_E2E_LIVE=1 live_production_run` | same | **161행 · 6 sheets · G: in-place · validation ok** |

### P20 readiness 실행 검증 (2026-06-28)

| harness | artifact | 결과 |
|---------|----------|------|
| `live_readiness` | `live_readiness_result.json` | ready · 6 checks · stack wired |
| `live_readiness --tick` | same | + supervisor_dry_tick pipeline_done |
