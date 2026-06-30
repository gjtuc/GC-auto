# GC1 Runtime 설계 — PART 2: L4 원자 (7필드 전개)

> 상위: [GC1_RUNTIME_DESIGN.md](GC1_RUNTIME_DESIGN.md)  
> **leaf 종료:** §0-3. 각 **atom** = 독립 7필드. action[] 안 leaf는 순서 고정.

---

## §L4-P0 JOB_PRELUDE

### Ω.A.L4.P0.01 — hancom 잔류 창 정리

| 필드 | 값 |
|------|-----|
| id | Ω.A.L4.P0.01 |
| channel | H |
| pre_probe | [Ω.A.L0.WIN.04] |
| action | [loop: Ω.A.L4.P0.01a … 01f] |
| post_probe | [CMP len(hancom_handles)==0] |
| on_fail | {code:null, max_attempt:1} — 실패해도 P0.02 진행 |
| timeout_ms | 30000 |

| sub-id | leaf |
|--------|------|
| P0.01a | W32 `_find_all_hancom_pdf_windows()` |
| P0.01b | CMP len(windows)==0 → exit loop |
| P0.01c | loop win: Ω.A.L4.P9.H.03 CMP complete |
| P0.01d | loop win: Ω.A.L4.P9.H.05 CMP close_enabled |
| P0.01e | H `_close_hancom_window` (닫기 only) |
| P0.01f | WAIT 300ms |
| P0.01g | STW hancom_windows_seen += closed |

### Ω.A.L4.P0.02 — Autochro 창 연결·배치

| sub-id | leaf |
|--------|------|
| P0.02a | Ω.A.L0.WIN.01 find handles |
| P0.02b | Ω.A.L0.WIN.02 CMP count>=1 else **E_WIN_NONE** |
| P0.02c | Ω.A.L0.WIN.03 connect each |
| P0.02d | Ω.A.L0.WIN.04a-d score |
| P0.02e | Ω.A.L0.WIN.05 argmax |
| P0.02f | W32 restore |
| P0.02g | W32 set_focus |
| P0.02h | CMP AUTOCHRO_AUTO_POSITION |
| P0.02i | W32 rectangle → rect |
| P0.02j | PURE width=max(rect.w,1200) |
| P0.02k | PURE height=max(rect.h,800) |
| P0.02l | PURE x=ENV AUTOCHRO_WINDOW_X |
| P0.02m | PURE y=ENV AUTOCHRO_WINDOW_Y |
| P0.02n | W32 move_window(x,y,w,h) |
| P0.02o | LOG position |
| P0.02p | WAIT 600ms |
| P0.02q | W32 set_focus |

### Ω.A.L4.P0.03 — data_name

| sub-id | leaf |
|--------|------|
| P0.03a | Ω.A.L0.DN.01 select control tab |
| P0.03b | Ω.A.L0.DN.02 WAIT 300 |
| P0.03c | try Ω.A.L0.DN-T.* title path |
| P0.03d | try Ω.A.L0.DN-R.* tree path |
| P0.03e | PURE fallback AUTOCHRO_DATA_NAME |
| P0.03f | Ω.A.L0.DN.99 else **E_DATA_NAME** |
| P0.03g | STW data_name |

### Ω.A.L4.P0.04 — pdf_path_planned

| sub-id | leaf |
|--------|------|
| P0.04a | Ω.A.L1.01 sanitize stem |
| P0.04b | Ω.A.L1.02 join output_dir |
| P0.04c | STW pdf_path_planned |

### Ω.A.L4.P0.05 — fresh skip

| sub-id | leaf |
|--------|------|
| P0.05a | Ω.A.L1.05 pdf_fresh |
| P0.05b | CMP NOT force AND fresh → **EARLY_OK** |

### Ω.A.L4.P0.06 — job init

| sub-id | leaf |
|--------|------|
| P0.06a | STW job_id uuid |
| P0.06b | STW started_at |
| P0.06c | STW phase_current=P0 |
| P0.06d | STW all P1..P9 atoms status=pending |

---

## §L4-P1 sync (atoms P1.01–P1.11)

각 atom 7필드 — action leaf만 열거.

**P1.01** pre: [Ω.A.L0.TAB.01] post: [Ω.A.L0.TAB.04]  
→ P1.01a Ω.A.L0.TAB.04? skip : P1.01b tabs.select(1) P1.01c WAIT 800

**P1.02** pre: [Ω.A.L0.TAB.04] post: [L0-LVP ctrl non-null]  
→ P1.02a L0-LV prefer=lower P1.02b L0-LVP pick

**P1.03** W32 set_focus(sample_list)

**P1.04** W32 click_input() neutral

**P1.05** PURE rel_x=max(20, width//4)

**P1.06** PURE rel_y=max(12, height-24)

**P1.07** W32 double_click_input(coords)

**P1.08** WAIT 1500

**P1.09** pre [P1.08 ok] → P1.09a L0-TAB.03? : select(0) WAIT 800

**P1.10** post L0-TAB.03 fail **E_P1_TAB**

**P1.11** [if GC1_RUNTIME_VERIFY_EYE] TASK verify_active_tab_analysis fail **E_VERIFY_TAB**

---

## §L4-P2 select_all (P2.01–P2.05)

동일 패턴. **P2.03** = focus atom 4 leaf (a–d).  
on_fail P2.04: {max_attempt:3, retry_delay_ms:500, fallback: re-P2.03}

---

## §L4-P3 context_initialize

**P3.04 popup** — deadline loop body (매 iteration):

| sub | leaf |
|-----|------|
| P3.04.1 | PURE deadline = now+5000 |
| P3.04.2 | CMP now<deadline |
| P3.04.3 | W32 Desktop #32768 enumerate |
| P3.04.4 | CMP menu_win exists |
| P3.04.5 | W32 wrapper_object |
| P3.04.6 | W32 menu().items() |
| P3.04.7 | loop item: PURE text str |
| P3.04.8 | CMP matcher(text) |
| P3.04.9 | W32 menu_item.click |
| P3.04.10 | WAIT 120 |
| P3.04.11 | fail **E_P3_MENU** |

**P3.06** post TASK verify_peak_table_cleared — numeric zero ratio > 0.85

---

## §L4-P4 load MTD

**P4.03 tree select** — line loop:

| sub | leaf |
|-----|------|
| P4.03.1 | L0-TR tree |
| P4.03.2 | W32 texts() → lines[] |
| P4.03.3 | loop line: L1.03 tree_match |
| P4.03.4 | PURE chosen=split(".")[0] |
| P4.03.5 | try tree.select(chosen) |
| P4.03.6 | WAIT 250 |
| P4.03.7 | try tree.select([chosen]) |
| P4.03.8 | try tree.select(full line) |
| P4.03.9 | fail **E_P4_TREE** |

**P4.06 dialog** — 7 sub (06a–06g) 각각 독립 atom 가능 (설계 leaf 7).

---

## §L4-P5 / P6 (attempt=2)

| atom | maps to | STW |
|------|---------|-----|
| P5.01 | P2.01 | attempt=2 |
| P5.02 | P2.02 | |
| … | … | |
| P5.05 | P2.05 | |
| P6.01 | P3.01 | attempt=2 |
| … | P3.06 | |

총 **11 atom** (P5×5 + P6×6) — 재사용이지만 **상태 기록은 독립 atom ID**.

---

## §L4-P7 quantify

**P7.02 menu** — loop menu_items:

| sub | leaf |
|-----|------|
| P7.02.1 | W32 menu_items top[] |
| P7.02.2 | CMP "시료목록" in top_text |
| P7.02.3 | loop sub items |
| P7.02.4 | CMP sub== or startswith "초기화+정량" |
| P7.02.5 | W32 menu_select |
| P7.02.6 | fallback menu_select(T) path |
| P7.02.7 | fail **E_P7_MENU** |

**P7.04 progress poll** — loop body:

| sub | leaf |
|-----|------|
| P7.04.1 | PURE deadline=now+QUANTIFY_WAIT |
| P7.04.2 | PROC findwindow 적분\|정량\|Progress |
| P7.04.3 | CMP found → WAIT 1000 continue |
| P7.04.4 | CMP elapsed>5s from start → break |
| P7.04.5 | WAIT 1000 |

---

## §L4-P8 print

**P8.05 print dialog** — btn loop:

| sub | leaf |
|-----|------|
| P8.05.1 | PROC find 인쇄\|Print timeout=DIALOG |
| P8.05.2 | CMP dlg null → send_keys ENTER return |
| P8.05.3 | W32 dlg.set_focus |
| P8.05.4 | loop btn in (확인,OK,&OK): child_window Button click |
| P8.05.5 | W32 type_keys ENTER |

**P8.06 save dialog wait** — poll 500ms until print_wait_sec

---

## §L4-P9 save (full)

**P9.05 edit find** — loop Edit descendants:

| sub | leaf |
|-----|------|
| P9.05.1 | W32 descendants Edit[] |
| P9.05.2 | CMP ".pdf" in window_text |
| P9.05.3 | CMP non-empty text |
| P9.05.4 | PURE pick first else edits[0] |

**P9.08 save btn** — loop (저장&S, 저장, Save) + %s

**P9.09 overwrite** — find dlg → loop Yes buttons → %y

**P9.11 wait_for_pdf_ready** — poll loop (see PART3 PAR.00)

**P9.12 fallback** — glob *.pdf sort mtime → recent<120s → alt path

---

## §L4-P9-HANCOM (per iteration)

8 leaf × max(hancom_wait/0.5) iterations — **상태기록은 iteration마다 STW last_hancom_progress**.

---

## §L4 atom count (PART2)

| Phase | atoms | action leaves |
|-------|-------|---------------|
| P0 | 6 | 38 |
| P1 | 11 | 18 |
| P2 | 5 | 9 |
| P3 | 6 | 22 |
| P4 | 8 | 28 |
| P5 | 5 | 9 (ref) |
| P6 | 6 | 22 (ref) |
| P7 | 5 | 18 |
| P8 | 6 | 16 |
| P9 | 14 | 45 + hancom loop |
| **합** | **72 atoms** | **~225 action leaves** |
