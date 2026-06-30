# GC1 Runtime 설계 — PART 3: L6 parse·clean·mail·pdf-wait

> 상위: [GC1_RUNTIME_DESIGN.md](GC1_RUNTIME_DESIGN.md)

---

## §PAR.00 wait_for_pdf_file_ready (poll 1회 = 6 leaf)

| sub-id | leaf |
|--------|------|
| PAR.00.1 | PURE deadline=now+max_wait |
| PAR.00.2 | FS.isfile path |
| PAR.00.3 | WAIT poll_sec 0.5 |
| PAR.00.4 | FS.read header 5 bytes |
| PAR.00.5 | CMP == b"%PDF-" |
| PAR.00.6 | PROC fitz.open page_count>0 |
| PAR.00.7 | FS.getsize |
| PAR.00.8 | CMP size==last_size |
| PAR.00.9 | PURE stable_start timer |
| PAR.00.10 | CMP stable>=2s → retry fitz |
| PAR.00.11 | CMP age>only_if_recent → early readable ok |

---

## §PAR.01–06 collect

| id | leaves |
|----|--------|
| PAR.01 | invoke PAR.00 |
| PAR.02 | PROC fitz.open |
| PAR.03.i | per page i: load_page, get_text (2 leaf × page_count) |
| PAR.04.i | parse_pdf_page(text) per page |
| PAR.05 | _merge_peak_continuation_pages loop pairs |
| PAR.06 | _collect_gc1_cycles_from_pages |

---

## §PAR.07 incomplete last cycle

| sub | leaf |
|-----|------|
| PAR.07.1 | PURE last_b_idx = _find_last_channel_b_page |
| PAR.07.2 | PROC measure_channel_b_scan_end_minutes |
| PAR.07.3 | PURE min = GC1_LAST_CYCLE_MIN_SCAN_MIN |
| PAR.07.4 | CMP scan_min < min |
| PAR.07.5 | PURE drop_count=1 (A/B/C 3 pages) |
| PAR.07.6 | LOG drop message |

---

## §PAR.08 trim — **주입 i마다** (i = 0 .. N-1)

> N = max(len(fid_cycles), len(tcd_cycles)). **6 leaf × N**.

| sub (per i) | leaf |
|-------------|------|
| PAR.08.i.01 | PURE fid,tcd = _cycle_at(i) |
| PAR.08.i.02 | PURE h2 = h2_area(tcd) |
| PAR.08.i.03 | CMP is_reduction_h2_area(h2, thresholds) |
| PAR.08.i.04 | PURE co = get_compound_area(tcd,"CO") |
| PAR.08.i.05 | CMP co >= reaction_co_min |
| PAR.08.i.06 | PURE class = classify(i): noise\|reduction\|transition\|reaction\|post |

### §PAR.08 aggregate (고정 leaf)

| id | leaf |
|----|------|
| PAR.08.A.01 | PROC find_reduction_streak → first, last |
| PAR.08.A.02 | PURE transition_idx = last+1 |
| PAR.08.A.03 | PURE first_reaction_idx scan |
| PAR.08.A.04 | loop i: CMP class==noise → mark drop |
| PAR.08.A.05 | loop i in [first..last]: mark drop reduction |
| PAR.08.A.06 | CMP transition_idx valid → mark drop 1 |
| PAR.08.A.07 | **R-04** CMP first_reaction_idx → **KEEP** (never drop) |
| PAR.08.A.08 | loop i>last_reduction: keep reaction+post |
| PAR.08.A.09 | PURE build trimmed fid_cycles[], tcd_cycles[] |
| PAR.08.A.10 | LOG counts |

### §PAR.08 thresholds load (env leaf)

| id | leaf |
|----|------|
| PAR.08.T.01 | PURE read GC1_REDUCTION_H2_AREA default 20000 |
| PAR.08.T.02 | PURE read GC1_REDUCTION_H2_TOL default 0.35 |
| PAR.08.T.03 | PURE reduction_h2_low = area×(1-tol) |
| PAR.08.T.04 | PURE reduction_h2_high = area×(1+tol) |
| PAR.08.T.05 | PURE read GC1_REACTION_CO_MIN |

---

## §PAR.09–10 excel

| id | leaf |
|----|------|
| PAR.09.1 | PURE peaks_to_gc1_excel_rows fid cycle 0.. |
| PAR.09.2 | PROC write sheet FID |
| PAR.10.1 | PURE tcd rows |
| PAR.10.2 | PROC write sheet TCD |
| PAR.10.3 | FS.isfile xlsx |
| PAR.10.4 | CMP size>0 |

---

## §CL cleanup (per pdf file j)

| sub (per j) | leaf |
|-------------|------|
| CL.j.01 | FS.path pdf_j |
| CL.j.02 | PROC _try_parse_gc1_pdf_quiet |
| CL.j.03 | CMP obsolete stem |
| CL.j.04 | CMP truncated vs canonical |
| CL.j.05.1 | PURE fingerprint injections count |
| CL.j.05.2 | PURE experiment_group_key |
| CL.j.05.3 | CMP same experiment |
| CL.j.05.4 | CMP keep higher injection count |
| CL.j.05.5 | **fix:** verbatim stem never obsolete if parse ok |
| CL.j.06 | FS.unlink pdf if marked |
| CL.j.07 | FS.unlink related xlsx |

---

## §ML mail (gc_mailer)

| id | leaf |
|----|------|
| ML.01 | CMP force OR gc1 → skip cooldown |
| ML.02 | PROC load_dotenv script_dir+output |
| ML.03 | PURE sender, password, recipient |
| ML.04 | CMP credentials non-empty else **E_SMTP_CFG** |
| ML.05 | PROC wait_for_smtp_internet poll DNS |
| ML.06 | PROC smtplib.SMTP_SSL connect |
| ML.07 | PROC login |
| ML.08 | PURE build MIMEMultipart |
| ML.09 | PURE attach xlsx MIMEBase |
| ML.10 | PROC sendmail |
| ML.11 | PROC noop verify |
| ML.12 | CMP noop ok else retry |
| ML.13 | LOG sent |
| ML.14 | STW gc_send_state mail slot |

**ML retry loop** (attempt 1..SMTP_SEND_RETRIES):

| sub | leaf |
|-----|------|
| ML.R.1 | CMP attempt <= max |
| ML.R.2 | WAIT SMTP_SEND_RETRY_DELAY |
| ML.R.3 | retry ML.06–ML.11 |

---

## §PART3 leaf count

| block | leaves |
|-------|--------|
| PAR.00 | 11 |
| PAR.01-06 | 10 + 2×pages |
| PAR.07 | 6 |
| PAR.08 per-i | 6×N |
| PAR.08 aggregate | 14 |
| PAR.08 thresholds | 5 |
| PAR.09-10 | 7 |
| CL per file | 7×files |
| ML | 14 + 3×retries |
| **typical N=50** | **~350+ L6 leaves** |
