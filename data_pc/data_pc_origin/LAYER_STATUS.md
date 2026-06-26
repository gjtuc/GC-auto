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

규칙: **L4 나노 PASS → L3 → L2 → L1 → L0** · 형제는 선행 형제 PASS 후 · **사용자 승인** 후 다음 구현.
