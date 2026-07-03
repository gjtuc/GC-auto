# GC1 Runtime 설계 — PART 5: 타워 B (은규 PC) 절대 전개

> 상위: [GC1_RUNTIME_DESIGN.md](GC1_RUNTIME_DESIGN.md)  
> **R-05/R-06** 동결. script_dir=`%USERPROFILE%\gc-data-pc\`

---

## §B-B — 지하 (Ω.B.B.*)

### IDENT (8 leaf — A와 동일 구조)

| ID | leaf |
|----|------|
| Ω.B.B.IDENT.01.FS | isdir gc-data-pc |
| Ω.B.B.IDENT.02.FS | isfile gc-data-pc/gc_automation.env |
| Ω.B.B.IDENT.03.FS | isfile PEG/machine_profile.json |
| Ω.B.B.IDENT.04.PURE | read profile role=data_pc |
| Ω.B.B.IDENT.05.CMP | operator == 은규 (optional) |
| Ω.B.B.IDENT.06.FS | NOT isfile chemstation repo gc_automation env as GC1 |
| Ω.B.B.IDENT.07.CMP | NOT run gc_automation.py → **E_B_CROSS_GC1** |
| Ω.B.B.IDENT.08.PURE | resolve script_dir paths |

### CFG (data_pc env — each key 4 leaf)

| key | default |
|-----|---------|
| NAVER_EMAIL | — |
| NAVER_APP_PASSWORD | — |
| DATA_PC_AUTO_MAIL_COOLDOWN_HOURS | 1 |
| DATA_PC_GDRIVE_RETRY_SEC | 900 |
| DATA_PC_SKIP_WIFI_CHECK | 0 |
| EXPERIMENT_DATA_ROOT / REACTION_ROOTS | profile |
| PYTHONPYCACHEPREFIX | .cursor cache |

×4 = **28 leaf**

### STATE (data_pc_runtime JSON)

| field | STW |
|-------|-----|
| status | idle/running_pipeline/pipeline_done/gdrive_retry/error |
| last_pipeline_at | iso |
| workflow_count | int |
| cooldown_remaining | int |
| wifi_ssid | str |
| gdrive_retry_at | iso |

---

## §B-L0 probes

### L0-WIFI — Ω.B.L0.WIFI.01~09 (A와 동일 ID, other SSID list)

### L0-G (G: drive)

| ID | leaf |
|----|------|
| Ω.B.L0.G.01.FS | isdir EXPERIMENT_DATA_ROOT |
| Ω.B.L0.G.02.PROC | os.listdir sample (optional) |
| Ω.B.L0.G.03.CMP | accessible else gdrive_unavailable |

### L0-IMAP TCP

| ID | leaf |
|----|------|
| Ω.B.L0.IMAP.01.PROC | socket.create_connection host:993 timeout |
| Ω.B.L0.IMAP.02.CMP | reachable |
| Ω.B.L0.IMAP.03.LOG | detail on fail |

### L0-PID (supervisor)

| ID | leaf |
|----|------|
| Ω.B.L0.PID.01.PROC | OpenProcess supervisor pid |
| Ω.B.L0.PID.02.CMP | alive |

### L0-LOCK origin

| ID | leaf |
|----|------|
| Ω.B.L0.LOCK.01.FS | isfile .origin_update.lock |
| Ω.B.L0.LOCK.02.PURE | read pid from lock |
| Ω.B.L0.LOCK.03.PROC | pid alive |
| Ω.B.L0.LOCK.04.CMP | stale → clear |

---

## §B-L2 gates (GateEvaluator — 순서 고정)

| gate | leaf |
|------|------|
| Ω.B.L2.0 | skip_wifi → pass |
| Ω.B.L2.1 | L0-WIFI.09 |
| Ω.B.L2.2 | [opt] L0-IMAP.02 |
| Ω.B.L2.3 | PipelineLock.try_acquire |
| Ω.B.L2.4 | cooldown from state |
| Ω.B.L2.5 | gdrive_retry timer |
| Ω.B.L2.6 | RUN |

---

## §B-L6-B-P1 IMAP (process_new_gc_emails)

### B-P1.01 credentials

| sub | leaf |
|-----|------|
| B-P1.01a | PROC load dotenv |
| B-P1.01b | PURE email, password |
| B-P1.01c | CMP non-empty else **E_B_MAIL_CFG** |

### B-P1.02 connect

| sub | leaf |
|-----|------|
| B-P1.02a | PROC IMAP4_SSL host port |
| B-P1.02b | PROC login |
| B-P1.02c | fail **E_B_IMAP_AUTH** |

### B-P1.03 gather INBOX

| sub | leaf |
|-----|------|
| B-P1.03a | PROC select INBOX |
| B-P1.03b | PROC search ALL/UNSEEN |
| B-P1.03c | loop uid: fetch BODY.PEEK |
| B-P1.03d | PURE parse subject date |
| B-P1.03e | CMP attachment xlsx |
| B-P1.03f | CMP NOT in processed_ids |
| B-P1.03g | PURE append pending[] |

### B-P1.04 gather Sent

| sub | leaf |
|-----|------|
| B-P1.04a | PROC _find_sent_mailbox |
| B-P1.04b | PROC search UNSEEN |
| B-P1.04c-f | same as 03c-g |

### B-P1.05 gather Self

| sub | leaf |
|-----|------|
| B-P1.05a | PROC _find_self_mailbox |
| B-P1.05b-f | unseen + YYYYMMDD pattern |

### B-P1.06 merge sort

| sub | leaf |
|-----|------|
| B-P1.06a | PURE merge lists |
| B-P1.06b | PURE sort by date asc |
| B-P1.06c | CMP empty → return 0 workflows |

### B-P1.07 per mail item k

| sub | leaf |
|-----|------|
| B-P1.07k.1 | LOG subject |
| B-P1.07k.2 | loop attachment: save bytes inbox |
| B-P1.07k.3 | PROC _cleanup_inbox_duplicate |
| B-P1.07k.4 | PROC run_workflow_for_file |
| B-P1.07k.5 | CMP ok → mark seen |
| B-P1.07k.6 | STW append processed_id |
| B-P1.07k.7 | CMP gdrive fail → gdrive_retry_needed |

### B-P1.08 teardown

| sub | leaf |
|-----|------|
| B-P1.08a | PROC logout |
| B-P1.08b | PURE return PipelineRunResult |

---

## §B-L6-B-P2 CALC (run_workflow step 2)

| id | leaf |
|----|------|
| B-P2.01 | FS.isfile xlsx |
| B-P2.02 | CMP ext xlsx/xls |
| B-P2.03 | PROC process_excel |
| B-P2.04 | CMP df_final not None |
| B-P2.05 | PROC detect equipment GC1/GC2/GC3 |
| B-P2.06 | PROC generate_sample_name |
| B-P2.07 | PROC validate yield/conversion |
| B-P2.08 | FS write processed xlsx |
| B-P2.09 | LOG warnings |

---

## §B-L6-B-P3 ARCHIVE (step 3)

| id | leaf |
|----|------|
| B-P3.01 | PROC _require_g_drive_access |
| B-P3.02 | fail → GDriveUnavailableError |
| B-P3.03 | PURE reaction_type from filename |
| B-P3.04 | PURE experiment folder path G: |
| B-P3.05 | FS.makedirs |
| B-P3.06 | FS copy xlsx |
| B-P3.07 | PROC _cleanup_duplicate_folders |
| B-P3.08 | PROC _cleanup_canonical_folders |

---

## §B-L6-B-P4 ORIGIN (step 4)

| id | leaf |
|----|------|
| B-P4.01 | PROC _origin_acquire_lock wait 900 |
| B-P4.02 | fail → skip origin |
| B-P4.03 | PROC originpro launch |
| B-P4.04 | PROC _open_opju_for_update |
| B-P4.05 | PROC import data to sheets |
| B-P4.06 | PROC save _Updated.opju |
| B-P4.07 | PROC _origin_dialog_watcher ReadOnly Yes |
| B-P4.08 | PROC _origin_exit_quiet |
| B-P4.09 | PROC _origin_release_lock |

### B-P4.07 watcher loop (per 0.5s)

| sub | leaf |
|-----|------|
| B-P4.07a | W32 EnumWindows |
| B-P4.07b | CMP Read-Only dialog text |
| B-P4.07c | W32 click Yes |
| B-P4.07d | WAIT 500 |

---

## §B-L3 JobRunner (data_pc_runtime layer3)

| id | leaf |
|----|------|
| Ω.B.L3.J.01 | GateEvaluator.evaluate |
| Ω.B.L3.J.02 | CMP RUN else skip |
| Ω.B.L3.J.03 | PipelineLock.try_acquire |
| Ω.B.L3.J.04 | STW running_pipeline |
| Ω.B.L3.J.05 | PROC pipeline_callback |
| Ω.B.L3.J.06 | PURE parse workflow_count |
| Ω.B.L3.J.07 | STW mark_pipeline_finished |
| Ω.B.L3.J.08 | CMP gdrive_retry |
| Ω.B.L3.J.09 | lock.release |

---

## §B-L4 Supervisor tick

| id | leaf |
|----|------|
| Ω.B.L4.S.01 | WAIT poll_interval |
| Ω.B.L4.S.02 | L0-PID supervisor alive |
| Ω.B.L4.S.03 | JobRunner.run_once |
| Ω.B.L4.S.04 | LOG status |
| Ω.B.L4.S.05 | CMP error → backoff |

---

## §B ERR codes

| code | 한 줄 |
|------|------|
| E_B_CROSS_GC1 | GC1 장비 프로그램은 이 PC에서 실행하지 않습니다 |
| E_B_MAIL_CFG | 메일 설정이 없습니다 |
| E_B_IMAP_AUTH | 메일 로그인 실패 |
| E_B_GDRIVE | G: 드라이브를 사용할 수 없습니다 |
| E_B_ORIGIN_LOCK | Origin이 다른 작업 중입니다 |

---

## §PART5 leaf count

| block | leaves |
|-------|--------|
| B-B | ~45 |
| B-L0 | ~25 |
| B-L2 | ~8 |
| B-P1 IMAP | ~55 + k×attachments |
| B-P2 | ~9 |
| B-P3 | ~8 |
| B-P4 | ~15 + watcher loop |
| B-L3/L4 | ~15 |
| **합** | **~160+ base** (+ mail items) |
