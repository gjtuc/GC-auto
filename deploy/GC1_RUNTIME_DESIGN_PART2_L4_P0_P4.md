# GC1 Runtime 설계 — PART 2a: L4 P0~P4 (7필드 전량, T13)

> 상위: [GC1_RUNTIME_DESIGN.md](GC1_RUNTIME_DESIGN.md)
> action sub-leaf: [PART2_L4](GC1_RUNTIME_DESIGN_PART2_L4.md)

---

## §L4-P0~P4 atom registry (36 atoms)

| atom_id | channel | pre_probe[] | post_probe[] | on_fail | timeout_ms |
|---------|---------|-------------|--------------|---------|------------|
| Ω.A.L4.P0.01 | H | Ω.A.L0.WIN.04 | CMP len(hancom_handles)==0 | {code:null,max_attempt:1} | 30000 |
| Ω.A.L4.P0.02 | H | Ω.A.L2.GEX.03, Ω.A.B.IDENT.07 | Ω.A.L0.WIN.06, Ω.A.L0.WIN.07 | {code:E_WIN_NONE,max_attempt:2,retry_delay_ms:1000} | 60000 |
| Ω.A.L4.P0.03 | H|E | Ω.A.L4.P0.02 ok | CMP data_name non-empty | {code:E_DATA_NAME,max_attempt:1} | 20000 |
| Ω.A.L4.P0.04 | PURE|STW | Ω.A.L4.P0.03 ok, data_name STW | CMP pdf_path_planned set | {code:null,max_attempt:1} | 5000 |
| Ω.A.L4.P0.05 | PURE|CMP | Ω.A.L4.P0.04 ok | CMP skip_decision recorded | {code:EARLY_OK,max_attempt:1} | 5000 |
| Ω.A.L4.P0.06 | STW | Ω.A.L4.P0.05 not EARLY_OK | CMP job_id, phase_current=P0 | {code:null,max_attempt:1} | 5000 |
| Ω.A.L4.P1.01 | H | Ω.A.L4.P0.06 ok, Ω.A.L0.TAB.01 | Ω.A.L0.TAB.04 | {code:E_P1_TAB,max_attempt:2,retry_delay_ms:800} | 15000 |
| Ω.A.L4.P1.02 | H | Ω.A.L0.TAB.04 | CMP control_sync_list non-null | {code:null,max_attempt:1} | 10000 |
| Ω.A.L4.P1.03 | H | Ω.A.L4.P1.02 ok | CMP focused hwnd | {code:null,max_attempt:1} | 5000 |
| Ω.A.L4.P1.04 | H | Ω.A.L4.P1.03 ok | CMP click sent | {code:null,max_attempt:1} | 5000 |
| Ω.A.L4.P1.05 | PURE | Ω.A.L4.P1.04 ok | CMP rel_x>0 | {code:null,max_attempt:1} | 1000 |
| Ω.A.L4.P1.06 | PURE | Ω.A.L4.P1.05 ok | CMP rel_y>0 | {code:null,max_attempt:1} | 1000 |
| Ω.A.L4.P1.07 | H | Ω.A.L4.P1.05, Ω.A.L4.P1.06 | CMP dblclick sent | {code:null,max_attempt:1} | 5000 |
| Ω.A.L4.P1.08 | W | Ω.A.L4.P1.07 ok | CMP elapsed>=1500 | {code:null,max_attempt:1} | 2000 |
| Ω.A.L4.P1.09 | H | Ω.A.L4.P1.08 ok | Ω.A.L0.TAB.03 | {code:E_P1_TAB,max_attempt:2,retry_delay_ms:800} | 15000 |
| Ω.A.L4.P1.10 | CMP | Ω.A.L4.P1.09 done | Ω.A.L0.TAB.03 | {code:E_P1_TAB,max_attempt:1} | 3000 |
| Ω.A.L4.P1.11 | E | GC1_RUNTIME_VERIFY_EYE=1, Ω.A.L4.P1.10 ok | TASK verify_active_tab_analysis pass | {code:E_VERIFY_TAB,max_attempt:1} | 30000 |
| Ω.A.L4.P2.01 | H | Ω.A.L4.P1.10 ok | Ω.A.L0.TAB.03 | {code:null,max_attempt:1} | 10000 |
| Ω.A.L4.P2.02 | H | Ω.A.L0.TAB.03 | CMP sample_list non-null | {code:null,max_attempt:1} | 10000 |
| Ω.A.L4.P2.03 | H | Ω.A.L4.P2.02 ok | CMP focus on sample_list | {code:E_P2_FOCUS,max_attempt:3,retry_delay_ms:500,fallback:re-P2.03} | 15000 |
| Ω.A.L4.P2.04 | H | Ω.A.L4.P2.03 ok | CMP keys sent | {code:E_P2_SELECT,max_attempt:2,retry_delay_ms:300} | 5000 |
| Ω.A.L4.P2.05 | W | Ω.A.L4.P2.04 ok | CMP elapsed>=500 | {code:null,max_attempt:1} | 1000 |
| Ω.A.L4.P3.01 | H | Ω.A.L4.P2.05 ok | Ω.A.L0.TAB.03 | {code:null,max_attempt:1} | 10000 |
| Ω.A.L4.P3.02 | H | Ω.A.L0.TAB.03 | CMP sample_list non-null | {code:null,max_attempt:1} | 10000 |
| Ω.A.L4.P3.03 | H | Ω.A.L4.P3.02 ok | CMP rclick sent | {code:null,max_attempt:1} | 10000 |
| Ω.A.L4.P3.04 | H | Ω.A.L4.P3.03 ok | CMP menu clicked | {code:E_P3_MENU,max_attempt:3,retry_delay_ms:120,fallback:E} | 20000 |
| Ω.A.L4.P3.05 | W | Ω.A.L4.P3.04 ok | CMP elapsed>=800 | {code:null,max_attempt:1} | 2000 |
| Ω.A.L4.P3.06 | E | Ω.A.L4.P3.05 ok | TASK zero_ratio>=0.85 | {code:E_VERIFY_PEAK,max_attempt:1} | 30000 |
| Ω.A.L4.P4.01 | F|L0 | Ω.A.L4.P3.06 ok | Ω.A.L0.MTD.03 FS.isfile | {code:E_MTD_MISSING,max_attempt:1} | 10000 |
| Ω.A.L4.P4.02 | H | Ω.A.L4.P4.01 ok | Ω.A.L0.TAB.03 | {code:null,max_attempt:1} | 10000 |
| Ω.A.L4.P4.03 | H | Ω.A.L0.TAB.03, Ω.A.L0.L1.03 | CMP tree selection ok | {code:E_P4_TREE,max_attempt:3,retry_delay_ms:250} | 30000 |
| Ω.A.L4.P4.04 | H | Ω.A.L4.P4.03 ok | CMP rclick sent | {code:null,max_attempt:1} | 10000 |
| Ω.A.L4.P4.05 | H | Ω.A.L4.P4.04 ok | CMP menu item clicked | {code:null,max_attempt:1} | 15000 |
| Ω.A.L4.P4.06 | H|F | Ω.A.L4.P4.05 ok | CMP dialog closed ok | {code:E_P4_MTD_DLG,max_attempt:2,retry_delay_ms:400,fallback:F} | 30000 |
| Ω.A.L4.P4.07 | W | Ω.A.L4.P4.06 ok | CMP elapsed>=2000 | {code:null,max_attempt:1} | 3000 |
| Ω.A.L4.P4.08 | E | Ω.A.L4.P4.07 ok | TASK numeric>=1 | {code:E_VERIFY_PEAK,max_attempt:1} | 30000 |

---

### Ω.A.L4.P0.01 — hancom 잔류 창 정리

| 필드 | 값 |
|------|-----|
| id | Ω.A.L4.P0.01 |
| channel | H |
| pre_probe | [Ω.A.L0.WIN.04] |
| action | [P0.01a..P0.01g (hancom loop)] |
| post_probe | [CMP len(hancom_handles)==0] |
| on_fail | {code:null,max_attempt:1} |
| timeout_ms | 30000 |

### Ω.A.L4.P0.02 — Autochro 창 연결·배치

| 필드 | 값 |
|------|-----|
| id | Ω.A.L4.P0.02 |
| channel | H |
| pre_probe | [Ω.A.L2.GEX.03, Ω.A.B.IDENT.07] |
| action | [P0.02a..P0.02q (WIN chain + move)] |
| post_probe | [Ω.A.L0.WIN.06, Ω.A.L0.WIN.07] |
| on_fail | {code:E_WIN_NONE,max_attempt:2,retry_delay_ms:1000} |
| timeout_ms | 60000 |

### Ω.A.L4.P0.03 — data_name 읽기

| 필드 | 값 |
|------|-----|
| id | Ω.A.L4.P0.03 |
| channel | H|E |
| pre_probe | [Ω.A.L4.P0.02 ok] |
| action | [P0.03a..P0.03g (DN-T/DN-R)] |
| post_probe | [CMP data_name non-empty] |
| on_fail | {code:E_DATA_NAME,max_attempt:1} |
| timeout_ms | 20000 |

### Ω.A.L4.P0.04 — pdf_path_planned

| 필드 | 값 |
|------|-----|
| id | Ω.A.L4.P0.04 |
| channel | PURE|STW |
| pre_probe | [Ω.A.L4.P0.03 ok, data_name STW] |
| action | [P0.04a L1.01, P0.04b L1.02, P0.04c STW] |
| post_probe | [CMP pdf_path_planned set] |
| on_fail | {code:null,max_attempt:1} |
| timeout_ms | 5000 |

### Ω.A.L4.P0.05 — fresh skip

| 필드 | 값 |
|------|-----|
| id | Ω.A.L4.P0.05 |
| channel | PURE|CMP |
| pre_probe | [Ω.A.L4.P0.04 ok] |
| action | [P0.05a L1.05, P0.05b CMP force|fresh] |
| post_probe | [CMP skip_decision recorded] |
| on_fail | {code:EARLY_OK,max_attempt:1} |
| timeout_ms | 5000 |

### Ω.A.L4.P0.06 — job init

| 필드 | 값 |
|------|-----|
| id | Ω.A.L4.P0.06 |
| channel | STW |
| pre_probe | [Ω.A.L4.P0.05 not EARLY_OK] |
| action | [P0.06a..P0.06d (job_id, atoms pending)] |
| post_probe | [CMP job_id, phase_current=P0] |
| on_fail | {code:null,max_attempt:1} |
| timeout_ms | 5000 |

### Ω.A.L4.P1.01 — 제어 탭 선택

| 필드 | 값 |
|------|-----|
| id | Ω.A.L4.P1.01 |
| channel | H |
| pre_probe | [Ω.A.L4.P0.06 ok, Ω.A.L0.TAB.01] |
| action | [P1.01a TAB.04?, P1.01b select(1), P1.01c WAIT 800] |
| post_probe | [Ω.A.L0.TAB.04] |
| on_fail | {code:E_P1_TAB,max_attempt:2,retry_delay_ms:800} |
| timeout_ms | 15000 |

### Ω.A.L4.P1.02 — 제어 목록 ListView

| 필드 | 값 |
|------|-----|
| id | Ω.A.L4.P1.02 |
| channel | H |
| pre_probe | [Ω.A.L0.TAB.04] |
| action | [P1.02a L0-LV lower, P1.02b L0-LVP pick] |
| post_probe | [CMP control_sync_list non-null] |
| on_fail | {code:null,max_attempt:1} |
| timeout_ms | 10000 |

### Ω.A.L4.P1.03 — 시료표 focus

| 필드 | 값 |
|------|-----|
| id | Ω.A.L4.P1.03 |
| channel | H |
| pre_probe | [Ω.A.L4.P1.02 ok] |
| action | [P1.03 W32 set_focus] |
| post_probe | [CMP focused hwnd] |
| on_fail | {code:null,max_attempt:1} |
| timeout_ms | 5000 |

### Ω.A.L4.P1.04 — 중립 클릭

| 필드 | 값 |
|------|-----|
| id | Ω.A.L4.P1.04 |
| channel | H |
| pre_probe | [Ω.A.L4.P1.03 ok] |
| action | [P1.04 W32 click_input neutral] |
| post_probe | [CMP click sent] |
| on_fail | {code:null,max_attempt:1} |
| timeout_ms | 5000 |

### Ω.A.L4.P1.05 — rel_x

| 필드 | 값 |
|------|-----|
| id | Ω.A.L4.P1.05 |
| channel | PURE |
| pre_probe | [Ω.A.L4.P1.04 ok] |
| action | [P1.05 PURE rel_x=max(20,w//4)] |
| post_probe | [CMP rel_x>0] |
| on_fail | {code:null,max_attempt:1} |
| timeout_ms | 1000 |

### Ω.A.L4.P1.06 — rel_y

| 필드 | 값 |
|------|-----|
| id | Ω.A.L4.P1.06 |
| channel | PURE |
| pre_probe | [Ω.A.L4.P1.05 ok] |
| action | [P1.06 PURE rel_y=max(12,h-24)] |
| post_probe | [CMP rel_y>0] |
| on_fail | {code:null,max_attempt:1} |
| timeout_ms | 1000 |

### Ω.A.L4.P1.07 — double_click 동기화

| 필드 | 값 |
|------|-----|
| id | Ω.A.L4.P1.07 |
| channel | H |
| pre_probe | [Ω.A.L4.P1.05, Ω.A.L4.P1.06] |
| action | [P1.07 W32 double_click_input] |
| post_probe | [CMP dblclick sent] |
| on_fail | {code:null,max_attempt:1} |
| timeout_ms | 5000 |

### Ω.A.L4.P1.08 — 동기화 대기

| 필드 | 값 |
|------|-----|
| id | Ω.A.L4.P1.08 |
| channel | W |
| pre_probe | [Ω.A.L4.P1.07 ok] |
| action | [P1.08 WAIT 1500] |
| post_probe | [CMP elapsed>=1500] |
| on_fail | {code:null,max_attempt:1} |
| timeout_ms | 2000 |

### Ω.A.L4.P1.09 — 분석목록 탭

| 필드 | 값 |
|------|-----|
| id | Ω.A.L4.P1.09 |
| channel | H |
| pre_probe | [Ω.A.L4.P1.08 ok] |
| action | [P1.09a TAB.03?, P1.09b select(0) WAIT 800] |
| post_probe | [Ω.A.L0.TAB.03] |
| on_fail | {code:E_P1_TAB,max_attempt:2,retry_delay_ms:800} |
| timeout_ms | 15000 |

### Ω.A.L4.P1.10 — 분석목록 탭 검증

| 필드 | 값 |
|------|-----|
| id | Ω.A.L4.P1.10 |
| channel | CMP |
| pre_probe | [Ω.A.L4.P1.09 done] |
| action | [P1.10 CMP TAB.03] |
| post_probe | [Ω.A.L0.TAB.03] |
| on_fail | {code:E_P1_TAB,max_attempt:1} |
| timeout_ms | 3000 |

### Ω.A.L4.P1.11 — eye 탭 검증 (opt)

| 필드 | 값 |
|------|-----|
| id | Ω.A.L4.P1.11 |
| channel | E |
| pre_probe | [GC1_RUNTIME_VERIFY_EYE=1, Ω.A.L4.P1.10 ok] |
| action | [P1.11 TASK verify_active_tab_analysis] |
| post_probe | [TASK verify_active_tab_analysis pass] |
| on_fail | {code:E_VERIFY_TAB,max_attempt:1} |
| timeout_ms | 30000 |

### Ω.A.L4.P2.01 — 분석목록 탭

| 필드 | 값 |
|------|-----|
| id | Ω.A.L4.P2.01 |
| channel | H |
| pre_probe | [Ω.A.L4.P1.10 ok] |
| action | [P2.01 H.select_analysis_tab] |
| post_probe | [Ω.A.L0.TAB.03] |
| on_fail | {code:null,max_attempt:1} |
| timeout_ms | 10000 |

### Ω.A.L4.P2.02 — 시료표 ListView

| 필드 | 값 |
|------|-----|
| id | Ω.A.L4.P2.02 |
| channel | H |
| pre_probe | [Ω.A.L0.TAB.03] |
| action | [P2.02 L0-LVP upper] |
| post_probe | [CMP sample_list non-null] |
| on_fail | {code:null,max_attempt:1} |
| timeout_ms | 10000 |

### Ω.A.L4.P2.03 — focus+click neutral

| 필드 | 값 |
|------|-----|
| id | Ω.A.L4.P2.03 |
| channel | H |
| pre_probe | [Ω.A.L4.P2.02 ok] |
| action | [P2.03a set_focus, P2.03b rel_x, P2.03c rel_y, P2.03d click] |
| post_probe | [CMP focus on sample_list] |
| on_fail | {code:E_P2_FOCUS,max_attempt:3,retry_delay_ms:500,fallback:re-P2.03} |
| timeout_ms | 15000 |

### Ω.A.L4.P2.04 — Ctrl+A

| 필드 | 값 |
|------|-----|
| id | Ω.A.L4.P2.04 |
| channel | H |
| pre_probe | [Ω.A.L4.P2.03 ok] |
| action | [P2.04 send_keys ^a] |
| post_probe | [CMP keys sent] |
| on_fail | {code:E_P2_SELECT,max_attempt:2,retry_delay_ms:300} |
| timeout_ms | 5000 |

### Ω.A.L4.P2.05 — 선택 대기

| 필드 | 값 |
|------|-----|
| id | Ω.A.L4.P2.05 |
| channel | W |
| pre_probe | [Ω.A.L4.P2.04 ok] |
| action | [P2.05 WAIT 500] |
| post_probe | [CMP elapsed>=500] |
| on_fail | {code:null,max_attempt:1} |
| timeout_ms | 1000 |

### Ω.A.L4.P3.01 — 분석목록 탭

| 필드 | 값 |
|------|-----|
| id | Ω.A.L4.P3.01 |
| channel | H |
| pre_probe | [Ω.A.L4.P2.05 ok] |
| action | [P3.01 H.select_analysis] |
| post_probe | [Ω.A.L0.TAB.03] |
| on_fail | {code:null,max_attempt:1} |
| timeout_ms | 10000 |

### Ω.A.L4.P3.02 — 시료표 ListView

| 필드 | 값 |
|------|-----|
| id | Ω.A.L4.P3.02 |
| channel | H |
| pre_probe | [Ω.A.L0.TAB.03] |
| action | [P3.02 L0-LVP upper] |
| post_probe | [CMP sample_list non-null] |
| on_fail | {code:null,max_attempt:1} |
| timeout_ms | 10000 |

### Ω.A.L4.P3.03 — 우클릭 준비

| 필드 | 값 |
|------|-----|
| id | Ω.A.L4.P3.03 |
| channel | H |
| pre_probe | [Ω.A.L4.P3.02 ok] |
| action | [P3.03a focus, P3.03b coords, P3.03c rclick, P3.03d WAIT 350] |
| post_probe | [CMP rclick sent] |
| on_fail | {code:null,max_attempt:1} |
| timeout_ms | 10000 |

### Ω.A.L4.P3.04 — 초기화 메뉴

| 필드 | 값 |
|------|-----|
| id | Ω.A.L4.P3.04 |
| channel | H |
| pre_probe | [Ω.A.L4.P3.03 ok] |
| action | [P3.04.1..P3.04.11 (#32768 loop)] |
| post_probe | [CMP menu clicked] |
| on_fail | {code:E_P3_MENU,max_attempt:3,retry_delay_ms:120,fallback:E} |
| timeout_ms | 20000 |

### Ω.A.L4.P3.05 — 초기화 대기

| 필드 | 값 |
|------|-----|
| id | Ω.A.L4.P3.05 |
| channel | W |
| pre_probe | [Ω.A.L4.P3.04 ok] |
| action | [P3.05 WAIT 800] |
| post_probe | [CMP elapsed>=800] |
| on_fail | {code:null,max_attempt:1} |
| timeout_ms | 2000 |

### Ω.A.L4.P3.06 — 피크표 cleared 검증

| 필드 | 값 |
|------|-----|
| id | Ω.A.L4.P3.06 |
| channel | E |
| pre_probe | [Ω.A.L4.P3.05 ok] |
| action | [P3.06 TASK verify_peak_table_cleared] |
| post_probe | [TASK zero_ratio>=0.85] |
| on_fail | {code:E_VERIFY_PEAK,max_attempt:1} |
| timeout_ms | 30000 |

### Ω.A.L4.P4.01 — MTD 경로

| 필드 | 값 |
|------|-----|
| id | Ω.A.L4.P4.01 |
| channel | F|L0 |
| pre_probe | [Ω.A.L4.P3.06 ok] |
| action | [P4.01 Ω.A.L0.MTD.01..03] |
| post_probe | [Ω.A.L0.MTD.03 FS.isfile] |
| on_fail | {code:E_MTD_MISSING,max_attempt:1} |
| timeout_ms | 10000 |

### Ω.A.L4.P4.02 — 분석목록 탭

| 필드 | 값 |
|------|-----|
| id | Ω.A.L4.P4.02 |
| channel | H |
| pre_probe | [Ω.A.L4.P4.01 ok] |
| action | [P4.02 H.select_analysis] |
| post_probe | [Ω.A.L0.TAB.03] |
| on_fail | {code:null,max_attempt:1} |
| timeout_ms | 10000 |

### Ω.A.L4.P4.03 — 트리 시료 선택

| 필드 | 값 |
|------|-----|
| id | Ω.A.L4.P4.03 |
| channel | H |
| pre_probe | [Ω.A.L0.TAB.03, Ω.A.L0.L1.03] |
| action | [P4.03.1..P4.03.9 tree loop] |
| post_probe | [CMP tree selection ok] |
| on_fail | {code:E_P4_TREE,max_attempt:3,retry_delay_ms:250} |
| timeout_ms | 30000 |

### Ω.A.L4.P4.04 — 트리 우클릭

| 필드 | 값 |
|------|-----|
| id | Ω.A.L4.P4.04 |
| channel | H |
| pre_probe | [Ω.A.L4.P4.03 ok] |
| action | [P4.04 rclick tree center] |
| post_probe | [CMP rclick sent] |
| on_fail | {code:null,max_attempt:1} |
| timeout_ms | 10000 |

### Ω.A.L4.P4.05 — 분석방법 불러오기 메뉴

| 필드 | 값 |
|------|-----|
| id | Ω.A.L4.P4.05 |
| channel | H |
| pre_probe | [Ω.A.L4.P4.04 ok] |
| action | [P4.05 popup 분석방법+불러] |
| post_probe | [CMP menu item clicked] |
| on_fail | {code:null,max_attempt:1} |
| timeout_ms | 15000 |

### Ω.A.L4.P4.06 — MTD 파일 대화상자

| 필드 | 값 |
|------|-----|
| id | Ω.A.L4.P4.06 |
| channel | H|F |
| pre_probe | [Ω.A.L4.P4.05 ok] |
| action | [P4.06a..P4.06g dialog path] |
| post_probe | [CMP dialog closed ok] |
| on_fail | {code:E_P4_MTD_DLG,max_attempt:2,retry_delay_ms:400,fallback:F} |
| timeout_ms | 30000 |

### Ω.A.L4.P4.07 — MTD 로드 대기

| 필드 | 값 |
|------|-----|
| id | Ω.A.L4.P4.07 |
| channel | W |
| pre_probe | [Ω.A.L4.P4.06 ok] |
| action | [P4.07 WAIT 2000] |
| post_probe | [CMP elapsed>=2000] |
| on_fail | {code:null,max_attempt:1} |
| timeout_ms | 3000 |

### Ω.A.L4.P4.08 — 피크 데이터 검증

| 필드 | 값 |
|------|-----|
| id | Ω.A.L4.P4.08 |
| channel | E |
| pre_probe | [Ω.A.L4.P4.07 ok] |
| action | [P4.08 TASK verify_peak_table_has_data] |
| post_probe | [TASK numeric>=1] |
| on_fail | {code:E_VERIFY_PEAK,max_attempt:1} |
| timeout_ms | 30000 |

## §T13 leaf count

| block | atoms | action leaves (PART2) |
|-------|-------|----------------------|
| P0 | 6 | 38 |
| P1 | 11 | 18 |
| P2 | 5 | 9 |
| P3 | 6 | 22 |
| P4 | 8 | 28 |
| **7필드 registry** | **36** | **115** |

*T13 complete — pre/post probe ID per atom*
