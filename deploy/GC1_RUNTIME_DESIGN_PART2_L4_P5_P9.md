# GC1 Runtime 설계 — PART 2b: L4 P5~P9 + job JSON (T14)

> 상위: [GC1_RUNTIME_DESIGN.md](GC1_RUNTIME_DESIGN.md)
> P0~P4 registry: [PART2_L4_P0_P4](GC1_RUNTIME_DESIGN_PART2_L4_P0_P4.md)
> L6 leaf: [PART3_L6](GC1_RUNTIME_DESIGN_PART3_L6.md)

---

## §L4-P5~P9 atom registry (36 atoms)

| atom_id | channel | pre_probe[] | post_probe[] | on_fail | timeout_ms |
|---------|---------|-------------|--------------|---------|------------|
| Ω.A.L4.P5.01 | H | Ω.A.L4.P4.08 ok | Ω.A.L0.TAB.03 | {code:null,max_attempt:1} | 10000 |
| Ω.A.L4.P5.02 | H | Ω.A.L0.TAB.03 | CMP sample_list | {code:null,max_attempt:1} | 10000 |
| Ω.A.L4.P5.03 | H | Ω.A.L4.P5.02 ok | CMP focus | {code:E_P2_FOCUS,max_attempt:3,retry_delay_ms:500} | 15000 |
| Ω.A.L4.P5.04 | H | Ω.A.L4.P5.03 ok | CMP keys | {code:E_P2_SELECT,max_attempt:2,retry_delay_ms:300} | 5000 |
| Ω.A.L4.P5.05 | W | Ω.A.L4.P5.04 ok | CMP elapsed | {code:null,max_attempt:1} | 1000 |
| Ω.A.L4.P6.01 | H | Ω.A.L4.P5.05 ok | Ω.A.L0.TAB.03 | {code:null,max_attempt:1} | 10000 |
| Ω.A.L4.P6.02 | H | Ω.A.L0.TAB.03 | CMP sample_list | {code:null,max_attempt:1} | 10000 |
| Ω.A.L4.P6.03 | H | Ω.A.L4.P6.02 ok | CMP rclick | {code:null,max_attempt:1} | 10000 |
| Ω.A.L4.P6.04 | H | Ω.A.L4.P6.03 ok | CMP menu | {code:E_P3_MENU,max_attempt:3,retry_delay_ms:120} | 20000 |
| Ω.A.L4.P6.05 | W | Ω.A.L4.P6.04 ok | CMP elapsed | {code:null,max_attempt:1} | 2000 |
| Ω.A.L4.P6.06 | E | Ω.A.L4.P6.05 ok | TASK cleared | {code:E_VERIFY_PEAK,max_attempt:1} | 30000 |
| Ω.A.L4.P7.01 | H | Ω.A.L4.P6.06 ok | Ω.A.L4.P2.05 ok | {code:null,max_attempt:1} | 30000 |
| Ω.A.L4.P7.02 | H | Ω.A.L4.P7.01 ok | CMP menu selected | {code:E_P7_MENU,max_attempt:2,retry_delay_ms:500} | 20000 |
| Ω.A.L4.P7.03 | W | Ω.A.L4.P7.02 ok | CMP elapsed>=3000 | {code:null,max_attempt:1} | 4000 |
| Ω.A.L4.P7.04 | PROC|W | Ω.A.L4.P7.03 ok | CMP progress done | {code:null,max_attempt:1} | 120000 |
| Ω.A.L4.P7.05 | E | Ω.A.L4.P7.04 ok | TASK pass | {code:E_VERIFY_PEAK,max_attempt:1} | 30000 |
| Ω.A.L4.P8.01 | H | Ω.A.L4.P7.05 ok | Ω.A.L4.P2.05 ok | {code:null,max_attempt:1} | 30000 |
| Ω.A.L4.P8.02 | H | Ω.A.L4.P8.01 ok | CMP fg hwnd | {code:null,max_attempt:1} | 5000 |
| Ω.A.L4.P8.03 | H | Ω.A.L4.P8.02 ok | CMP keys | {code:null,max_attempt:1} | 5000 |
| Ω.A.L4.P8.04 | W | Ω.A.L4.P8.03 ok | CMP elapsed | {code:null,max_attempt:1} | 2000 |
| Ω.A.L4.P8.05 | H | Ω.A.L4.P8.04 ok | CMP dlg handled | {code:E_P8_PRINT,max_attempt:2,retry_delay_ms:500} | 30000 |
| Ω.A.L4.P8.06 | W | Ω.A.L4.P8.05 ok | CMP save dlg or timeout | {code:null,max_attempt:1} | 60000 |
| Ω.A.L4.P9.01 | FS | Ω.A.L4.P8.06 ok | FS.isdir parent | {code:null,max_attempt:1} | 5000 |
| Ω.A.L4.P9.02 | PROC | Ω.A.L4.P9.01 ok | CMP dlg non-null | {code:E_P9_DLG,max_attempt:3,retry_delay_ms:2000} | 120000 |
| Ω.A.L4.P9.03 | H | Ω.A.L4.P9.02 ok | CMP fg dlg | {code:null,max_attempt:1} | 5000 |
| Ω.A.L4.P9.04 | PURE | data_name STW | CMP stem | {code:null,max_attempt:1} | 1000 |
| Ω.A.L4.P9.05 | H | Ω.A.L4.P9.03 ok | CMP edit found | {code:null,max_attempt:1} | 15000 |
| Ω.A.L4.P9.06 | H | Ω.A.L4.P9.05 ok | CMP text set | {code:null,max_attempt:1} | 10000 |
| Ω.A.L4.P9.07 | W | Ω.A.L4.P9.06 ok | CMP elapsed | {code:null,max_attempt:1} | 1000 |
| Ω.A.L4.P9.08 | H | Ω.A.L4.P9.07 ok | CMP click | {code:E_P9_SAVE_BTN,max_attempt:2,retry_delay_ms:300} | 15000 |
| Ω.A.L4.P9.09 | H | Ω.A.L4.P9.08 ok | CMP overwrite ok | {code:null,max_attempt:1} | 15000 |
| Ω.A.L4.P9.10 | H|W | Ω.A.L4.P9.09 ok | CMP hancom idle | {code:null,max_attempt:1} | 180000 |
| Ω.A.L4.P9.11 | FS|W | Ω.A.L4.P9.10 ok | Ω.A.L0.PDF.01..05 | {code:E_P9_READY,max_attempt:1} | 120000 |
| Ω.A.L4.P9.12 | FS | Ω.A.L4.P9.11 fail soft | CMP recent pdf | {code:null,max_attempt:1} | 10000 |
| Ω.A.L4.P9.13 | FS | pdf path known | CL.08 kept_path | {code:E_CLEAN_WRONG,max_attempt:1} | 30000 |
| Ω.A.L4.P9.14 | STW | Ω.A.L4.P9.11 or P9.12 ok | CMP record_export | {code:null,max_attempt:1} | 5000 |

---

### Ω.A.L4.P5.01 — 분석목록 탭 (2차)

| 필드 | 값 |
|------|-----|
| id | Ω.A.L4.P5.01 |
| channel | H |
| pre_probe | [Ω.A.L4.P4.08 ok] |
| action | [maps Ω.A.L4.P2.01] |
| post_probe | [Ω.A.L0.TAB.03] |
| on_fail | {code:null,max_attempt:1} |
| timeout_ms | 10000 |

### Ω.A.L4.P5.02 — 시료표 LV (2차)

| 필드 | 값 |
|------|-----|
| id | Ω.A.L4.P5.02 |
| channel | H |
| pre_probe | [Ω.A.L0.TAB.03] |
| action | [maps Ω.A.L4.P2.02] |
| post_probe | [CMP sample_list] |
| on_fail | {code:null,max_attempt:1} |
| timeout_ms | 10000 |

### Ω.A.L4.P5.03 — focus click (2차)

| 필드 | 값 |
|------|-----|
| id | Ω.A.L4.P5.03 |
| channel | H |
| pre_probe | [Ω.A.L4.P5.02 ok] |
| action | [maps Ω.A.L4.P2.03] |
| post_probe | [CMP focus] |
| on_fail | {code:E_P2_FOCUS,max_attempt:3,retry_delay_ms:500} |
| timeout_ms | 15000 |

### Ω.A.L4.P5.04 — Ctrl+A (2차)

| 필드 | 값 |
|------|-----|
| id | Ω.A.L4.P5.04 |
| channel | H |
| pre_probe | [Ω.A.L4.P5.03 ok] |
| action | [maps Ω.A.L4.P2.04] |
| post_probe | [CMP keys] |
| on_fail | {code:E_P2_SELECT,max_attempt:2,retry_delay_ms:300} |
| timeout_ms | 5000 |

### Ω.A.L4.P5.05 — WAIT (2차)

| 필드 | 값 |
|------|-----|
| id | Ω.A.L4.P5.05 |
| channel | W |
| pre_probe | [Ω.A.L4.P5.04 ok] |
| action | [maps Ω.A.L4.P2.05] |
| post_probe | [CMP elapsed] |
| on_fail | {code:null,max_attempt:1} |
| timeout_ms | 1000 |

### Ω.A.L4.P6.01 — 분석목록 (2차)

| 필드 | 값 |
|------|-----|
| id | Ω.A.L4.P6.01 |
| channel | H |
| pre_probe | [Ω.A.L4.P5.05 ok] |
| action | [maps Ω.A.L4.P3.01] |
| post_probe | [Ω.A.L0.TAB.03] |
| on_fail | {code:null,max_attempt:1} |
| timeout_ms | 10000 |

### Ω.A.L4.P6.02 — 시료표 (2차)

| 필드 | 값 |
|------|-----|
| id | Ω.A.L4.P6.02 |
| channel | H |
| pre_probe | [Ω.A.L0.TAB.03] |
| action | [maps Ω.A.L4.P3.02] |
| post_probe | [CMP sample_list] |
| on_fail | {code:null,max_attempt:1} |
| timeout_ms | 10000 |

### Ω.A.L4.P6.03 — 우클릭 (2차)

| 필드 | 값 |
|------|-----|
| id | Ω.A.L4.P6.03 |
| channel | H |
| pre_probe | [Ω.A.L4.P6.02 ok] |
| action | [maps Ω.A.L4.P3.03] |
| post_probe | [CMP rclick] |
| on_fail | {code:null,max_attempt:1} |
| timeout_ms | 10000 |

### Ω.A.L4.P6.04 — 초기화 메뉴 (2차)

| 필드 | 값 |
|------|-----|
| id | Ω.A.L4.P6.04 |
| channel | H |
| pre_probe | [Ω.A.L4.P6.03 ok] |
| action | [maps Ω.A.L4.P3.04] |
| post_probe | [CMP menu] |
| on_fail | {code:E_P3_MENU,max_attempt:3,retry_delay_ms:120} |
| timeout_ms | 20000 |

### Ω.A.L4.P6.05 — WAIT (2차)

| 필드 | 값 |
|------|-----|
| id | Ω.A.L4.P6.05 |
| channel | W |
| pre_probe | [Ω.A.L4.P6.04 ok] |
| action | [maps Ω.A.L4.P3.05] |
| post_probe | [CMP elapsed] |
| on_fail | {code:null,max_attempt:1} |
| timeout_ms | 2000 |

### Ω.A.L4.P6.06 — cleared verify (2차)

| 필드 | 값 |
|------|-----|
| id | Ω.A.L4.P6.06 |
| channel | E |
| pre_probe | [Ω.A.L4.P6.05 ok] |
| action | [maps Ω.A.L4.P3.06] |
| post_probe | [TASK cleared] |
| on_fail | {code:E_VERIFY_PEAK,max_attempt:1} |
| timeout_ms | 30000 |

### Ω.A.L4.P7.01 — P2 subtree

| 필드 | 값 |
|------|-----|
| id | Ω.A.L4.P7.01 |
| channel | H |
| pre_probe | [Ω.A.L4.P6.06 ok] |
| action | [P7.01 P2.01..P2.05] |
| post_probe | [Ω.A.L4.P2.05 ok] |
| on_fail | {code:null,max_attempt:1} |
| timeout_ms | 30000 |

### Ω.A.L4.P7.02 — 초기화+정량 메뉴

| 필드 | 값 |
|------|-----|
| id | Ω.A.L4.P7.02 |
| channel | H |
| pre_probe | [Ω.A.L4.P7.01 ok] |
| action | [P7.02.1..P7.02.7] |
| post_probe | [CMP menu selected] |
| on_fail | {code:E_P7_MENU,max_attempt:2,retry_delay_ms:500} |
| timeout_ms | 20000 |

### Ω.A.L4.P7.03 — 정량 시작 대기

| 필드 | 값 |
|------|-----|
| id | Ω.A.L4.P7.03 |
| channel | W |
| pre_probe | [Ω.A.L4.P7.02 ok] |
| action | [P7.03 WAIT 3000] |
| post_probe | [CMP elapsed>=3000] |
| on_fail | {code:null,max_attempt:1} |
| timeout_ms | 4000 |

### Ω.A.L4.P7.04 — progress poll

| 필드 | 값 |
|------|-----|
| id | Ω.A.L4.P7.04 |
| channel | PROC|W |
| pre_probe | [Ω.A.L4.P7.03 ok] |
| action | [P7.04.1..P7.04.5 loop] |
| post_probe | [CMP progress done] |
| on_fail | {code:null,max_attempt:1} |
| timeout_ms | 120000 |

### Ω.A.L4.P7.05 — 피크 데이터 검증

| 필드 | 값 |
|------|-----|
| id | Ω.A.L4.P7.05 |
| channel | E |
| pre_probe | [Ω.A.L4.P7.04 ok] |
| action | [TASK verify_peak_table_has_data] |
| post_probe | [TASK pass] |
| on_fail | {code:E_VERIFY_PEAK,max_attempt:1} |
| timeout_ms | 30000 |

### Ω.A.L4.P8.01 — P2 subtree

| 필드 | 값 |
|------|-----|
| id | Ω.A.L4.P8.01 |
| channel | H |
| pre_probe | [Ω.A.L4.P7.05 ok] |
| action | [P8.01 P2.01..P2.05] |
| post_probe | [Ω.A.L4.P2.05 ok] |
| on_fail | {code:null,max_attempt:1} |
| timeout_ms | 30000 |

### Ω.A.L4.P8.02 — 창 focus

| 필드 | 값 |
|------|-----|
| id | Ω.A.L4.P8.02 |
| channel | H |
| pre_probe | [Ω.A.L4.P8.01 ok] |
| action | [P8.02 set_focus] |
| post_probe | [CMP fg hwnd] |
| on_fail | {code:null,max_attempt:1} |
| timeout_ms | 5000 |

### Ω.A.L4.P8.03 — Ctrl+P

| 필드 | 값 |
|------|-----|
| id | Ω.A.L4.P8.03 |
| channel | H |
| pre_probe | [Ω.A.L4.P8.02 ok] |
| action | [P8.03 ^p] |
| post_probe | [CMP keys] |
| on_fail | {code:null,max_attempt:1} |
| timeout_ms | 5000 |

### Ω.A.L4.P8.04 — 인쇄 대화 대기

| 필드 | 값 |
|------|-----|
| id | Ω.A.L4.P8.04 |
| channel | W |
| pre_probe | [Ω.A.L4.P8.03 ok] |
| action | [P8.04 WAIT 1000] |
| post_probe | [CMP elapsed] |
| on_fail | {code:null,max_attempt:1} |
| timeout_ms | 2000 |

### Ω.A.L4.P8.05 — 인쇄 확인

| 필드 | 값 |
|------|-----|
| id | Ω.A.L4.P8.05 |
| channel | H |
| pre_probe | [Ω.A.L4.P8.04 ok] |
| action | [P8.05.1..P8.05.5] |
| post_probe | [CMP dlg handled] |
| on_fail | {code:E_P8_PRINT,max_attempt:2,retry_delay_ms:500} |
| timeout_ms | 30000 |

### Ω.A.L4.P8.06 — 저장 대화 poll

| 필드 | 값 |
|------|-----|
| id | Ω.A.L4.P8.06 |
| channel | W |
| pre_probe | [Ω.A.L4.P8.05 ok] |
| action | [P8.06 poll 500ms] |
| post_probe | [CMP save dlg or timeout] |
| on_fail | {code:null,max_attempt:1} |
| timeout_ms | 60000 |

### Ω.A.L4.P9.01 — output dir

| 필드 | 값 |
|------|-----|
| id | Ω.A.L4.P9.01 |
| channel | FS |
| pre_probe | [Ω.A.L4.P8.06 ok] |
| action | [P9.01 makedirs] |
| post_probe | [FS.isdir parent] |
| on_fail | {code:null,max_attempt:1} |
| timeout_ms | 5000 |

### Ω.A.L4.P9.02 — 저장 대화 찾기

| 필드 | 값 |
|------|-----|
| id | Ω.A.L4.P9.02 |
| channel | PROC |
| pre_probe | [Ω.A.L4.P9.01 ok] |
| action | [P9.02 find dlg] |
| post_probe | [CMP dlg non-null] |
| on_fail | {code:E_P9_DLG,max_attempt:3,retry_delay_ms:2000} |
| timeout_ms | 120000 |

### Ω.A.L4.P9.03 — 대화 focus

| 필드 | 값 |
|------|-----|
| id | Ω.A.L4.P9.03 |
| channel | H |
| pre_probe | [Ω.A.L4.P9.02 ok] |
| action | [P9.03 set_focus] |
| post_probe | [CMP fg dlg] |
| on_fail | {code:null,max_attempt:1} |
| timeout_ms | 5000 |

### Ω.A.L4.P9.04 — stem pure

| 필드 | 값 |
|------|-----|
| id | Ω.A.L4.P9.04 |
| channel | PURE |
| pre_probe | [data_name STW] |
| action | [P9.04 PURE stem] |
| post_probe | [CMP stem] |
| on_fail | {code:null,max_attempt:1} |
| timeout_ms | 1000 |

### Ω.A.L4.P9.05 — Edit 찾기

| 필드 | 값 |
|------|-----|
| id | Ω.A.L4.P9.05 |
| channel | H |
| pre_probe | [Ω.A.L4.P9.03 ok] |
| action | [P9.05.1..P9.05.4] |
| post_probe | [CMP edit found] |
| on_fail | {code:null,max_attempt:1} |
| timeout_ms | 15000 |

### Ω.A.L4.P9.06 — 경로 입력

| 필드 | 값 |
|------|-----|
| id | Ω.A.L4.P9.06 |
| channel | H |
| pre_probe | [Ω.A.L4.P9.05 ok] |
| action | [P9.06 set_edit_text] |
| post_probe | [CMP text set] |
| on_fail | {code:null,max_attempt:1} |
| timeout_ms | 10000 |

### Ω.A.L4.P9.07 — 입력 대기

| 필드 | 값 |
|------|-----|
| id | Ω.A.L4.P9.07 |
| channel | W |
| pre_probe | [Ω.A.L4.P9.06 ok] |
| action | [P9.07 WAIT 500] |
| post_probe | [CMP elapsed] |
| on_fail | {code:null,max_attempt:1} |
| timeout_ms | 1000 |

### Ω.A.L4.P9.08 — 저장 버튼

| 필드 | 값 |
|------|-----|
| id | Ω.A.L4.P9.08 |
| channel | H |
| pre_probe | [Ω.A.L4.P9.07 ok] |
| action | [P9.08 btn loop+%s] |
| post_probe | [CMP click] |
| on_fail | {code:E_P9_SAVE_BTN,max_attempt:2,retry_delay_ms:300} |
| timeout_ms | 15000 |

### Ω.A.L4.P9.09 — 덮어쓰기

| 필드 | 값 |
|------|-----|
| id | Ω.A.L4.P9.09 |
| channel | H |
| pre_probe | [Ω.A.L4.P9.08 ok] |
| action | [P9.09 Yes loop] |
| post_probe | [CMP overwrite ok] |
| on_fail | {code:null,max_attempt:1} |
| timeout_ms | 15000 |

### Ω.A.L4.P9.10 — hancom loop

| 필드 | 값 |
|------|-----|
| id | Ω.A.L4.P9.10 |
| channel | H|W |
| pre_probe | [Ω.A.L4.P9.09 ok] |
| action | [P9.H.01..08 × iter] |
| post_probe | [CMP hancom idle] |
| on_fail | {code:null,max_attempt:1} |
| timeout_ms | 180000 |

### Ω.A.L4.P9.11 — PDF ready

| 필드 | 값 |
|------|-----|
| id | Ω.A.L4.P9.11 |
| channel | FS|W |
| pre_probe | [Ω.A.L4.P9.10 ok] |
| action | [PAR.00 poll] |
| post_probe | [Ω.A.L0.PDF.01..05] |
| on_fail | {code:E_P9_READY,max_attempt:1} |
| timeout_ms | 120000 |

### Ω.A.L4.P9.12 — PDF fallback glob

| 필드 | 값 |
|------|-----|
| id | Ω.A.L4.P9.12 |
| channel | FS |
| pre_probe | [Ω.A.L4.P9.11 fail soft] |
| action | [P9.12 glob mtime] |
| post_probe | [CMP recent pdf] |
| on_fail | {code:null,max_attempt:1} |
| timeout_ms | 10000 |

### Ω.A.L4.P9.13 — cleanup CL

| 필드 | 값 |
|------|-----|
| id | Ω.A.L4.P9.13 |
| channel | FS |
| pre_probe | [pdf path known] |
| action | [CL.01..CL.08] |
| post_probe | [CL.08 kept_path] |
| on_fail | {code:E_CLEAN_WRONG,max_attempt:1} |
| timeout_ms | 30000 |

### Ω.A.L4.P9.14 — export record

| 필드 | 값 |
|------|-----|
| id | Ω.A.L4.P9.14 |
| channel | STW |
| pre_probe | [Ω.A.L4.P9.11 or P9.12 ok] |
| action | [P9.14 STW atoms+paths] |
| post_probe | [CMP record_export] |
| on_fail | {code:null,max_attempt:1} |
| timeout_ms | 5000 |

## §L6 cross-ref (T14 — export 이후)

| chain | PART3 section | leaf |
|-------|---------------|------|
| PDF wait | §PAR.00 | 11 |
| parse+trim | §PAR.01–08 | 10+6×N+14+5 |
| excel | §PAR.09–10 | 7 |
| cleanup | §CL | 7×files |
| mail | §ML | 14+3×retries |

## §JOB-JSON — `.gc_autochro_job.json` 예시

파일: [gc_autochro_job.example.json](gc_autochro_job.example.json)

```json
{
  "job_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "started_at": "2026-06-30T10:00:00+09:00",
  "data_name": "20260630_DRE-01",
  "pdf_path_planned": "C:\\Users\\User\\Desktop\\박은규\\20260630_DRE-01.pdf",
  "prep_enabled": true,
  "phase_current": "P4",
  "atom_current": "Ω.A.L4.P4.03",
  "resume_from": null,
  "force": false,
  "hancom_windows_seen": 1,
  "atoms": {
    "Ω.A.L4.P0.01": {
      "status": "ok",
      "attempt": 1,
      "channel_used": "H",
      "fail_code": null,
      "probe_snapshot": {
        "hancom_closed": 1
      },
      "started_at": "2026-06-30T10:00:01+09:00",
      "ended_at": "2026-06-30T10:00:05+09:00"
    },
    "Ω.A.L4.P4.03": {
      "status": "running",
      "attempt": 2,
      "channel_used": "H",
      "fail_code": null,
      "probe_snapshot": {
        "tree_line": "20260630_DRE-01.1"
      },
      "started_at": "2026-06-30T10:02:10+09:00",
      "ended_at": null
    },
    "Ω.A.L4.P9.14": {
      "status": "pending",
      "attempt": 0,
      "channel_used": null,
      "fail_code": null,
      "probe_snapshot": {},
      "started_at": null,
      "ended_at": null
    }
  }
}
```

### §JOB-JSON 필드 leaf (§B-STATE)

| JSON path | STW leaf |
|-----------|----------|
| job_id | Ω.A.B.STATE.job_id |
| atoms.{id}.status | Ω.A.B.STATE.atoms.status |
| atoms.{id}.attempt | Ω.A.B.STATE.atoms.attempt |
| resume_from | Ω.A.B.STATE.resume_from |

## §T14 leaf count

| block | atoms |
|-------|-------|
| P5 | 5 |
| P6 | 6 |
| P7 | 5 |
| P8 | 6 |
| P9 | 14 |
| **합** | **36** |

*T14 complete*
