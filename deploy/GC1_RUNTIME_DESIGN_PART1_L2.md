# GC1 Runtime 설계 — PART 1b: Ω-L2 게이트 + Ω-ERR (T12)

> 상위: [GC1_RUNTIME_DESIGN.md](GC1_RUNTIME_DESIGN.md)

---

## §L2-G-EX — export 잡 게이트 (leaf 순서 고정)

| step | gate ID | leaf / expr | fail code |
|------|---------|-------------|-----------|
| 1 | Ω.A.L2.GEX.01 | CMP CFG.enabled OR force | — (skip export) |
| 2 | Ω.A.L2.GEX.02 | CMP NOT Ω.A.B.IDENT.07 fail | E_IDENT_CROSS_PC |
| 3 | Ω.A.L2.GEX.03 | Ω.A.L0.WIN.02 handles>=1 | E_WIN_NONE |
| 4 | Ω.A.L2.GEX.04 | IF prep: Ω.A.L0.MTD.03 | E_MTD_MISSING |
| 5 | Ω.A.L2.GEX.05 | Ω.A.L1.04 crm_need OR force | — (skip) |
| 6 | Ω.A.L2.GEX.06 | CMP NOT pipeline_locked | E_PIPELINE_BUSY |
| 7 | Ω.A.L2.GEX.07 | PURE RUN = G1∧G2∧G3∧G4∧G5∧G6 | — |

### G-EX bypass (force / L7)

| ID | leaf |
|----|------|
| Ω.A.L2.GEX.F.01 | CMP force=True |
| Ω.A.L2.GEX.F.02 | skip G4 (MTD) if not prep |
| Ω.A.L2.GEX.F.03 | skip G5 (crm fresh) |

---

## §L2-G-ATOM — 원자 직전·직후

| step | gate ID | leaf |
|------|---------|------|
| PRE | Ω.A.L2.GAT.PRE.01 | ∧ atom.pre_probe[] all true |
| PRE | Ω.A.L2.GAT.PRE.02 | STW atom status=running |
| POST | Ω.A.L2.GAT.POST.01 | ∧ atom.post_probe[] all true |
| POST | Ω.A.L2.GAT.POST.02 | STW atom status=ok |
| FAIL | Ω.A.L2.GAT.FAIL.01 | STW atom status=fail |
| FAIL | Ω.A.L2.GAT.FAIL.02 | STW fail_code |
| RETRY | Ω.A.L2.GAT.RTY.01 | CMP attempt < max_attempt |
| RETRY | Ω.A.L2.GAT.RTY.02 | WAIT retry_delay_ms |
| FB | Ω.A.L2.GAT.FB.01 | CMP fallback_channel E |
| FB | Ω.A.L2.GAT.FB.02 | rerun action via E channel |

---

## §L2-B-GATE — 타워 B (data_pc) 요약

| step | ID | leaf |
|------|-----|------|
| 0 | Ω.B.L2.0 | skip_wifi |
| 1 | Ω.B.L2.1 | L0-WIFI.09 |
| 2 | Ω.B.L2.2 | L0-IMAP.02 optional |
| 3 | Ω.B.L2.3 | PipelineLock.try_acquire |
| 4 | Ω.B.L2.4 | cooldown L1 state |
| 5 | Ω.B.L2.5 | gdrive_retry timer |
| 6 | Ω.B.L2.6 | RUN |

---

## §ERR — 실패 코드 → 은규 한 줄 (전량)

| code | probe / atom | 은규에게 보이는 한 줄 | GC_오류_최recent.txt |
|------|--------------|----------------------|----------------------|
| E_IDENT_CROSS_PC | Ω.A.B.IDENT.07 | 이 PC에서는 Autochro를 실행하지 않습니다 | 동일 |
| E_WIN_NONE | Ω.A.L2.GEX.03 | Autochro 창을 찾지 못했습니다. Autochro를 켜 주세요 | 동일 |
| E_DATA_NAME | Ω.A.L0.DN.99 | 제어목록 이름을 읽지 못했습니다 | 동일 |
| E_MTD_MISSING | Ω.A.L0.MTD.03 | 바탕화면에 ○○○○○○○○ 분석방법.MTD 가 없습니다 | 파일명 포함 |
| E_P1_TAB | Ω.A.L4.P1.10 | 분석목록 탭으로 바꾸지 못했습니다 | 동일 |
| E_P2_FOCUS | Ω.A.L4.P2.03 | 시료 표 선택에 실패했습니다 | 동일 |
| E_P2_SELECT | Ω.A.L4.P2.04 | Ctrl+A 전체 선택에 실패했습니다 | 동일 |
| E_P3_MENU | Ω.A.L4.P3.04 | 초기화 메뉴를 찾지 못했습니다 | 동일 |
| E_P4_TREE | Ω.A.L4.P4.03 | 트리에서 시료명을 찾지 못했습니다 | data_name 포함 |
| E_P4_MTD_DLG | Ω.A.L4.P4.06 | 분석방법 파일 열기에 실패했습니다 | 동일 |
| E_P7_MENU | Ω.A.L4.P7.02 | 초기화+정량 메뉴를 찾지 못했습니다 | 동일 |
| E_P8_PRINT | Ω.A.L4.P8.05 | 인쇄 대화상자 확인에 실패했습니다 | 동일 |
| E_P9_DLG | Ω.A.L4.P9.02 | PDF 저장 창이 뜨지 않았습니다 | 동일 |
| E_P9_SAVE_BTN | Ω.A.L4.P9.08 | PDF 저장 버튼을 누르지 못했습니다 | 동일 |
| E_P9_READY | Ω.A.L4.P9.11 | PDF가 저장되지 않았습니다 | path basename |
| E_VERIFY_PEAK | Ω.A.L0.TASK.* | 피크 표 숫자가 맞지 않습니다 | 동일 |
| E_VERIFY_TAB | Ω.A.L0.TASK.VTA | 분석목록 탭 확인 실패 | 동일 |
| E_CLEAN_WRONG | CL.05 | PDF 정리 중 잘못된 파일이 선택되었습니다 | 동일 |
| E_WIFI | Ω.A.L0.WIFI.09 | iPhone 핫스팟에 연결되지 않았습니다 | SSID |
| E_SMTP | ML.04 | 메일 설정이 없습니다 | 동일 |
| E_PIPELINE_BUSY | Ω.A.L2.GEX.06 | 다른 작업이 진행 중입니다 | 동일 |
| E_PDF_READY | PAR.00 | PDF 파일을 아직 열 수 없습니다 | 동일 |
| E_B_CROSS_GC1 | Ω.B.B.IDENT.07 | GC1 장비 프로그램은 이 PC에서 실행하지 않습니다 | 동일 |
| E_B_MAIL_CFG | B-P1.01 | 메일 설정이 없습니다 | 동일 |
| E_B_IMAP_AUTH | B-P1.02 | 메일 로그인에 실패했습니다 | 동일 |
| E_B_GDRIVE | B-P3.01 | G: 드라이브를 사용할 수 없습니다 | 동일 |
| E_B_ORIGIN_LOCK | B-P4.01 | Origin이 다른 작업 중입니다 | 동일 |

### §ERR leaf (코드당 3 leaf)

| sub | leaf |
|-----|------|
| ERR.{code}.01 | PURE map code → message_ko |
| ERR.{code}.02 | FS write GC_오류_최근.txt one line |
| ERR.{code}.03 | STW atoms[].fail_code |

---

## §L2-T12 leaf count

| block | leaves |
|-------|--------|
| G-EX | 10 |
| G-ATOM | 10 |
| B-GATE | 7 |
| ERR table + ERR leaf×27 | 81+ |
| **합** | **~108** |
