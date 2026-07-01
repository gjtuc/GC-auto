# GC1 Runtime 설계 — PART 4: L7 세션 · L8 표면 · error

> 상위: [GC1_RUNTIME_DESIGN.md](GC1_RUNTIME_DESIGN.md)

---

## §L7-WATCH (gc_watch GC1 분기) — tick 1회

| id | leaf |
|----|------|
| Ω.A.L7.W.T.01 | PURE tick_start monotonic |
| Ω.A.L7.W.T.02 | FS read .gc_watch_status.json |
| Ω.A.L7.W.T.03 | PROC gc_status.write_heartbeat MMDDHHmm.txt |
| Ω.A.L7.W.01 | Ω.A.L0.WIFI full chain |
| Ω.A.L7.W.02 | STW last_ssid |
| Ω.A.L7.W.03 | CMP connected = WIFI.09 |
| Ω.A.L7.W.04 | STW prev_connected from state |
| Ω.A.L7.W.05 | CMP edge = connected AND NOT prev |
| Ω.A.L7.W.06 | CMP NOT edge → exit tick |
| Ω.A.L7.W.07 | Ω.A.B.CLK.03 delta since last_edge |
| Ω.A.L7.W.08 | Ω.A.B.CLK.04 debounce fail → exit |
| Ω.A.L7.W.09 | STW last_edge_at |
| Ω.A.L7.W.10 | STW session_id uuid |
| Ω.A.L7.W.11 | STW session_export_done=false |
| Ω.A.L7.W.12 | PROC run_processing force=True |
| Ω.A.L7.W.13 | CMP export ok |
| Ω.A.L7.W.14 | STW session_export_done=true |
| Ω.A.L7.W.15 | STW prev_connected=connected |
| Ω.A.L7.W.16 | LOG tick summary |

### §L7-WATCH pipeline 내부 (1 edge = L6 chain)

| id | leaf |
|----|------|
| Ω.A.L7.P.01 | G-EX RUN |
| Ω.A.L7.P.02 | L4 P0-P9 full |
| Ω.A.L7.P.03 | PAR.* full |
| Ω.A.L7.P.04 | ML.* full |
| Ω.A.L7.P.05 | STW .gc_send_state processed |

---

## §L7-FORCE (gc_automation --force / Cursor 개시)

| id | leaf |
|----|------|
| Ω.A.L7.F.01 | PROC gc_request.message_is_initiation OR argv force |
| Ω.A.L7.F.02 | CMP NOT initiation → exit 2 |
| Ω.A.L7.F.03 | PROC gc_force_auth if configured |
| Ω.A.L7.F.04 | G-EX with G4/G5 bypass |
| Ω.A.L7.F.05 | L4 P0-P9 (prep per env) |
| Ω.A.L7.F.06 | L6 PAR+ML |
| Ω.A.L7.F.07 | exit 0 ok / exit 1 fail |

---

## §L8 — 사용자 표면 (은규·장비)

### Ω.A.L8.GC1 bat

| id | leaf |
|----|------|
| Ω.A.L8.01 | PROC spawn python gc_automation.py --force |
| Ω.A.L8.02 | CMP exit 0 → show 완료 |
| Ω.A.L8.03 | CMP exit 1 → GC_오류_최근.txt |

### Ω.B.L8 data_pc (R-06)

| id | leaf |
|----|------|
| Ω.B.L8.01 | PROC data_pc_request.message_is_initiation |
| Ω.B.L8.02 | PROC 촉매 반응 계산.py OR data_pc_runtime |
| Ω.B.L8.03 | LOG 4단계 요약 |

---

## §ERROR_HANDLER (gc_error_handler)

| id | leaf |
|----|------|
| Ω.A.ERR.01 | CMP GC_ERROR_HANDLER_ENABLED |
| Ω.A.ERR.02 | PROC read heartbeat stale |
| Ω.A.ERR.03 | CMP age > STALE_SEC |
| Ω.A.ERR.04 | FS append .gc_error_log.jsonl |
| Ω.A.ERR.05 | FS write GC_오류_최근.txt 한 줄 |
| Ω.A.ERR.06 | PROC gc_stop_watch.bat |
| Ω.A.ERR.07 | WAIT cooldown |
| Ω.A.ERR.08 | PROC gc_start_watch.bat |
| Ω.A.ERR.09 | [opt] CURSOR_API_KEY Agent.prompt |

---

## §PART4 leaf count: ~45
