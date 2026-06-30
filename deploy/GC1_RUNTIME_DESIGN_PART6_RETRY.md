# GC1 Runtime 설계 — PART 6: on_fail · retry · fallback (전 atom)

> 상위: [GC1_RUNTIME_DESIGN.md](GC1_RUNTIME_DESIGN.md)  
> **모든 L4 atom**은 실패 시 아래 표 중 하나. 미표시 = max_attempt=1, no fallback.

---

## §RETRY-Policy 표

| atom_id | max_attempt | retry_delay_ms | fallback_channel | fail_code |
|---------|-------------|----------------|------------------|-----------|
| Ω.A.L4.P0.02 | 2 | 1000 | — | E_WIN_NONE |
| Ω.A.L4.P1.01 | 2 | 800 | — | E_P1_TAB |
| Ω.A.L4.P2.03 | 3 | 500 | H re-click neutral | E_P2_FOCUS |
| Ω.A.L4.P2.04 | 2 | 300 | H resend ^a | E_P2_SELECT |
| Ω.A.L4.P3.04 | 3 | 120 | E eye click 초기화 | E_P3_MENU |
| Ω.A.L4.P4.03 | 3 | 250 | — | E_P4_TREE |
| Ω.A.L4.P4.06 | 2 | 400 | F send_keys path | E_P4_MTD_DLG |
| Ω.A.L4.P7.02 | 2 | 500 | — | E_P7_MENU |
| Ω.A.L4.P7.04 | 1 | — | — | (timeout ok) |
| Ω.A.L4.P8.05 | 2 | 500 | send_keys ENTER | E_P8_PRINT |
| Ω.A.L4.P9.02 | 3 | 2000 | — | E_P9_DLG |
| Ω.A.L4.P9.08 | 2 | 300 | %s | E_P9_SAVE_BTN |
| Ω.A.L4.P9.11 | 1 | poll 500 | — | E_P9_READY |
| Ω.A.L0.WIFI.01 | 3 | 1500 | cache ssid | E_WIFI |
| ML.06-11 | SMTP_SEND_RETRIES | SMTP_SEND_RETRY_DELAY | — | E_SMTP |
| PAR.00 | ceil(max_wait/0.5) | 500 | — | E_PDF_READY |
| B-P1.02 | 2 | 2000 | — | E_B_IMAP_AUTH |
| B-P3.01 | gdrive_retry | 900000 | — | E_B_GDRIVE |
| B-P4.01 | 1 | 900000 wait | skip P4 | E_B_ORIGIN_LOCK |

---

## §G-POST retry (eye verify)

| TASK | fail action |
|------|-------------|
| verify_peak_table_cleared | retry P3.04 once, then E_VERIFY_PEAK |
| verify_peak_table_has_data | retry P4.07 wait +2s, then E_VERIFY_PEAK |
| verify_active_tab_analysis | retry P1.09 once |

---

## §BLOCKED → agent_queue_state (Hook)

| 조건 | status |
|------|--------|
| Autochro 실장비 UI 필요 | blocked |
| Origin GUI | blocked |
| G: SecuYou 수동 unlock | blocked |
| 사용자 비밀번호 | blocked |

---

## §Resume (`.gc_autochro_job.json`)

| resume_from | skip atoms |
|-------------|------------|
| Ω.A.L4.P4.03 | P0-P3 ok, run P4..P9 |
| Ω.A.L4.P9.02 | P0-P8 ok, run P9 |

각 skipped atom: STW status=skip.

---

## §PART6: policy leaves = 25 + 3 TASK + 4 resume rules
