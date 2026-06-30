# GC1 Runtime — 최하층(지하)부터 재귀 분해 설계서

> **목적:** 규칙(R)은 **동결**. 체질(C)만 **0·지하층부터** leaf까지 **재귀 분해 끝** (코드·Hook 큐 **없음**).  
> **상태:** 2026-06-29 — **절대 최대 분해** (PART 1~6). MOD 슬롯 §MOD.  
> **leaf ID:** `Ω.<타워>.<층>.<블록>.<순번>.<기호>`

### 문서 분할 (전체 설계)

| 파일 | 내용 |
|------|------|
| **본 문서** | §0 헌법, §B, §L0~L3, 요약 |
| [PART1_L0](GC1_RUNTIME_DESIGN_PART1_L0.md) | **Ω-L0 전 leaf** (T11: 502+) |
| [PART1_L2](GC1_RUNTIME_DESIGN_PART1_L2.md) | **Ω-L2 게이트 + Ω-ERR** (T12) |
| [PART2_L4](GC1_RUNTIME_DESIGN_PART2_L4.md) | P0~P9 **72 atom**, ~225 action leaf, 7필드 |
| [PART3_L6](GC1_RUNTIME_DESIGN_PART3_L6.md) | parse·trim(**6×N**), clean, mail, pdf-wait |
| [PART4_L7_L8](GC1_RUNTIME_DESIGN_PART4_L7_L8.md) | watch·force·표면·error_handler |
| [PART5_TOWER_B](GC1_RUNTIME_DESIGN_PART5_TOWER_B.md) | 은규 PC IMAP→계산→G:→Origin |
| [PART6_RETRY](GC1_RUNTIME_DESIGN_PART6_RETRY.md) | 전 atom on_fail·resume·blocked |

---

## §0. 불변식 (헌법)

> **T10 범위:** §Ω-1 ~ §Ω-4 + §B (IDENT · HOST · CFG · STATE · CLK)

### §Ω-1. 규칙(R) — 변경 금지 (§0-1)

### §0-1. 규칙(R) — 변경 금지 (참조만)

| R-ID | 내용 |
|------|------|
| R-01 | Autochro UI 8단계 순서 (동기화→초기화→MTD→초기화→초기화+정량→인쇄→PDF) |
| R-02 | MTD: `{YYYYMMDD} 분석방법.MTD` (데이터명 날짜 접두) |
| R-03 | PDF stem = 제어목록 UI 데이터명 **그대로** (Windows 금지문자만 제거) |
| R-04 | GC1 trim: 환원·전환 제외, **첫 반응 포함** |
| R-05 | GC1 장비 PC = `gc_automation.py` / 은규 PC = `촉매 반응 계산.py` **교차 실행 금지** |
| R-06 | 은규 개시: `진행`/`시작` 등 → data_pc 파이프라인 (본 설계의 타워 B) |
| R-07 | Git: pull 후 작업, env·profile Git 제외 |

### §Ω-2. 체질(C) — 본 설계 전부 (§0-2)

### §0-2. 체질(C) — 본 설계 전부

레이어·프로브·게이트·원자·상태·retry·채널(H/E/F/W) — **전부 교체 가능**.

### §Ω-3. leaf 종료 조건 (§0-3)

### §0-3. leaf 종료 조건 (더 쪼갤 수 없을 때만 leaf)

| 기호 | 의미 | leaf 예 |
|------|------|---------|
| `W32` | Win32/pywinauto **의미 1회** | `set_focus`, `click_input(coords=(x,y))` |
| `WAIT` | 대기 **1회** | `sleep(0.35)` |
| `PROC` | 외부 프로세스 **1회** | `subprocess.run(netsh…)` |
| `FS` | 파일 syscall **1회** | `os.path.isfile`, `open(rb).read(4096)` |
| `RX` | 정규식 **1회** | `re.search(pat, s)` |
| `CMP` | 비교 **1회** | `conf >= 25`, `frac < 0.30` |
| `PURE` | 부작용 0 계산 **1회** | `normpath`, `strip`, `max(w,h)` |
| `STW` | 상태 JSON **필드 1개** 쓰기 | `atoms[id].status = "ok"` |
| `LOG` | 로그 **1줄** | `_log("…")` |

**금지:** leaf 하나에 W32 두 번, 또는 `click+sleep+verify` 묶음.

### §Ω-4. 원자(atom) 7필드 + R/C 경계 (§0-4)

**R/C 경계:** R-ID 표(§Ω-1)는 **참조만**. leaf·게이트·retry·채널(§Ω-2~§L4)은 **C — 전부 교체 가능**.

### §0-4. 원자(atom) 7필드 (구현 시 필수, 설계 시 전 leaf가 이 틀에 매핑)

```
id, channel(H|E|F|W|ST|LOG), pre_probe[], action[], post_probe[],
on_fail{code, max_attempt, retry_delay_ms, fallback_channel},
timeout_ms
```

### §0-5. ID 체계

```
Ω.A.B.IDENT.01.FS.isdir          — 타워 A(GC1 장비), 지하, 블록, 순번, leaf
Ω.B.L0.IMAP.04.CMP.reachable     — 타워 B(은규 PC)
Ω.A.L4.P3.MENU.04a3.CMP.matcher  — 페이즈 내부 서브-leaf (재귀 허용)
```

### §0-6. 의존 방향 (위는 아래만 import)

```
L8 표면 → L7 세션 → L6 잡 → L5 페이즈 → L4 원자 → L3 액추에이터
  → L2 게이트 → L1 팩트 → L0 프로브 → B 지하
```

타워 A(L6 export)와 타워 B(L6 data_pc)는 **SMTP xlsx**에서만 접점.

---

# 타워 A — GC1 장비 PC

---

## §B — 지하층 (Ω.A.B.*)

### §B-IDENT

| ID | leaf | 입출력 |
|----|------|--------|
| Ω.A.B.IDENT.01.FS.isdir | `FS.isdir(repo_root)` | bool |
| Ω.A.B.IDENT.02.FS.isfile | `FS.isfile(Desktop\박은규\gc_automation.env)` | bool |
| Ω.A.B.IDENT.03.PURE.resolve_profile | `gc_profiles.resolve_profile()` | `{instance, mode, output_dir, script_dir}` |
| Ω.A.B.IDENT.04.CMP.instance | `instance == "gc1"` | bool |
| Ω.A.B.IDENT.05.FS.isfile | `machine_profile.json` optional | bool |
| Ω.A.B.IDENT.06.PURE.read_json | profile.role | string |
| Ω.A.B.IDENT.07.CMP.role | `role != "data_pc"` | bool → else **E_IDENT_CROSS_PC** |
| Ω.A.B.IDENT.08.CMP.chemstation_mode | `mode == "gc1"` | bool |

### §B-HOST

| ID | leaf |
|----|------|
| Ω.A.B.HOST.01.PURE.platform | `sys.platform` |
| Ω.A.B.HOST.02.PURE.arch | `platform.architecture()[0]` → 32bit/64bit |
| Ω.A.B.HOST.03.PROC.tasklist | filter `Autochro` → pid\|null |
| Ω.A.B.HOST.04.W32.enum | `findwindows(title_re=한컴\|Hancom)` → handles[] |
| Ω.A.B.HOST.05.W32.foreground | `GetForegroundWindow()` → hwnd |
| Ω.A.B.HOST.06.PURE.metrics | `SM_CXSCREEN`, `SM_CYSCREEN` |
| Ω.A.B.HOST.07.PURE.dpi | `GetDpiForWindow` or 96 default |
| Ω.A.B.HOST.08.PURE.profile_key | `f"{w}x{h}@{dpi}"` → screen_regions display_profile |

### §B-CFG (env 키 **키마다** read→trim→default→validate 4 leaf)

| env 키 | read ID | default | validate |
|--------|---------|---------|----------|
| AUTOCHRO_ENABLED | `.01` | 0 | bool |
| AUTOCHRO_WINDOW_TITLE_PATTERN | `.02` | Autochro | non-empty str |
| AUTOCHRO_AUTO_POSITION | `.03` | 1 | bool |
| AUTOCHRO_WINDOW_X | `.04` | 40 | int |
| AUTOCHRO_WINDOW_Y | `.05` | 40 | int |
| AUTOCHRO_LIST_NEUTRAL_X_FRAC | `.06` | 0.78 | 0.0<f<1.0 |
| AUTOCHRO_ANALYSIS_METHOD_DIR | `.07` | Desktop | isdir |
| GC1_AUTOCHRO_PREP_STEPS | `.08` | 1 | bool |
| AUTOCHRO_HANCOM_WAIT_SEC | `.09` | 120 | int≥0 |
| AUTOCHRO_QUANTIFY_WAIT_SEC | `.10` | 60 | int≥0 |
| AUTOCHRO_DIALOG_WAIT_SEC | `.11` | 30 | int≥0 |
| GC1_PDF_READY_WAIT_SEC | `.12` | 90 | int≥0 |
| AUTOCHRO_CRM_PATH | `.13` | — | file optional |
| AUTOCHRO_DATA_NAME | `.14` | — | str fallback |
| GC1_USE_RUNTIME | `.15` | 0 | bool |
| GC1_RUNTIME_VERIFY_EYE | `.16` | 0 | bool |
| GC1_SKIP_AUTOCHRO_EXPORT | `.17` | 0 | bool |
| REQUIRED_HOTSPOT | `.18` | iPhone | csv ssid |
| GC1_HOTSPOT_RECONNECT_MIN_SEC | `.19` | 90 | int |

각 키 leaf 4개 × 19키 = **76 leaf** (Ω.A.B.CFG.*)

#### §B-CFG-LEAF — 76 leaf 전개

| leaf ID | op | env 키 | 동작 |
|---------|-----|--------|------|
| Ω.A.B.CFG.01a | READ | AUTOCHRO_ENABLED | os.getenv |
| Ω.A.B.CFG.01b | TRIM | AUTOCHRO_ENABLED | strip |
| Ω.A.B.CFG.01c | DEFAULT | AUTOCHRO_ENABLED | 0 |
| Ω.A.B.CFG.01d | VALID | AUTOCHRO_ENABLED | bool |
| Ω.A.B.CFG.02a | READ | AUTOCHRO_WINDOW_TITLE_PATTERN | os.getenv |
| Ω.A.B.CFG.02b | TRIM | AUTOCHRO_WINDOW_TITLE_PATTERN | strip |
| Ω.A.B.CFG.02c | DEFAULT | AUTOCHRO_WINDOW_TITLE_PATTERN | Autochro |
| Ω.A.B.CFG.02d | VALID | AUTOCHRO_WINDOW_TITLE_PATTERN | non-empty str |
| Ω.A.B.CFG.03a | READ | AUTOCHRO_AUTO_POSITION | os.getenv |
| Ω.A.B.CFG.03b | TRIM | AUTOCHRO_AUTO_POSITION | strip |
| Ω.A.B.CFG.03c | DEFAULT | AUTOCHRO_AUTO_POSITION | 1 |
| Ω.A.B.CFG.03d | VALID | AUTOCHRO_AUTO_POSITION | bool |
| Ω.A.B.CFG.04a | READ | AUTOCHRO_WINDOW_X | os.getenv |
| Ω.A.B.CFG.04b | TRIM | AUTOCHRO_WINDOW_X | strip |
| Ω.A.B.CFG.04c | DEFAULT | AUTOCHRO_WINDOW_X | 40 |
| Ω.A.B.CFG.04d | VALID | AUTOCHRO_WINDOW_X | int |
| Ω.A.B.CFG.05a | READ | AUTOCHRO_WINDOW_Y | os.getenv |
| Ω.A.B.CFG.05b | TRIM | AUTOCHRO_WINDOW_Y | strip |
| Ω.A.B.CFG.05c | DEFAULT | AUTOCHRO_WINDOW_Y | 40 |
| Ω.A.B.CFG.05d | VALID | AUTOCHRO_WINDOW_Y | int |
| Ω.A.B.CFG.06a | READ | AUTOCHRO_LIST_NEUTRAL_X_FRAC | os.getenv |
| Ω.A.B.CFG.06b | TRIM | AUTOCHRO_LIST_NEUTRAL_X_FRAC | strip |
| Ω.A.B.CFG.06c | DEFAULT | AUTOCHRO_LIST_NEUTRAL_X_FRAC | 0.78 |
| Ω.A.B.CFG.06d | VALID | AUTOCHRO_LIST_NEUTRAL_X_FRAC | 0<f<1 |
| Ω.A.B.CFG.07a | READ | AUTOCHRO_ANALYSIS_METHOD_DIR | os.getenv |
| Ω.A.B.CFG.07b | TRIM | AUTOCHRO_ANALYSIS_METHOD_DIR | strip |
| Ω.A.B.CFG.07c | DEFAULT | AUTOCHRO_ANALYSIS_METHOD_DIR | Desktop |
| Ω.A.B.CFG.07d | VALID | AUTOCHRO_ANALYSIS_METHOD_DIR | isdir |
| Ω.A.B.CFG.08a | READ | GC1_AUTOCHRO_PREP_STEPS | os.getenv |
| Ω.A.B.CFG.08b | TRIM | GC1_AUTOCHRO_PREP_STEPS | strip |
| Ω.A.B.CFG.08c | DEFAULT | GC1_AUTOCHRO_PREP_STEPS | 1 |
| Ω.A.B.CFG.08d | VALID | GC1_AUTOCHRO_PREP_STEPS | bool |
| Ω.A.B.CFG.09a | READ | AUTOCHRO_HANCOM_WAIT_SEC | os.getenv |
| Ω.A.B.CFG.09b | TRIM | AUTOCHRO_HANCOM_WAIT_SEC | strip |
| Ω.A.B.CFG.09c | DEFAULT | AUTOCHRO_HANCOM_WAIT_SEC | 120 |
| Ω.A.B.CFG.09d | VALID | AUTOCHRO_HANCOM_WAIT_SEC | int≥0 |
| Ω.A.B.CFG.10a | READ | AUTOCHRO_QUANTIFY_WAIT_SEC | os.getenv |
| Ω.A.B.CFG.10b | TRIM | AUTOCHRO_QUANTIFY_WAIT_SEC | strip |
| Ω.A.B.CFG.10c | DEFAULT | AUTOCHRO_QUANTIFY_WAIT_SEC | 60 |
| Ω.A.B.CFG.10d | VALID | AUTOCHRO_QUANTIFY_WAIT_SEC | int≥0 |
| Ω.A.B.CFG.11a | READ | AUTOCHRO_DIALOG_WAIT_SEC | os.getenv |
| Ω.A.B.CFG.11b | TRIM | AUTOCHRO_DIALOG_WAIT_SEC | strip |
| Ω.A.B.CFG.11c | DEFAULT | AUTOCHRO_DIALOG_WAIT_SEC | 30 |
| Ω.A.B.CFG.11d | VALID | AUTOCHRO_DIALOG_WAIT_SEC | int≥0 |
| Ω.A.B.CFG.12a | READ | GC1_PDF_READY_WAIT_SEC | os.getenv |
| Ω.A.B.CFG.12b | TRIM | GC1_PDF_READY_WAIT_SEC | strip |
| Ω.A.B.CFG.12c | DEFAULT | GC1_PDF_READY_WAIT_SEC | 90 |
| Ω.A.B.CFG.12d | VALID | GC1_PDF_READY_WAIT_SEC | int≥0 |
| Ω.A.B.CFG.13a | READ | AUTOCHRO_CRM_PATH | os.getenv |
| Ω.A.B.CFG.13b | TRIM | AUTOCHRO_CRM_PATH | strip |
| Ω.A.B.CFG.13c | DEFAULT | AUTOCHRO_CRM_PATH | — |
| Ω.A.B.CFG.13d | VALID | AUTOCHRO_CRM_PATH | file optional |
| Ω.A.B.CFG.14a | READ | AUTOCHRO_DATA_NAME | os.getenv |
| Ω.A.B.CFG.14b | TRIM | AUTOCHRO_DATA_NAME | strip |
| Ω.A.B.CFG.14c | DEFAULT | AUTOCHRO_DATA_NAME | — |
| Ω.A.B.CFG.14d | VALID | AUTOCHRO_DATA_NAME | str fallback |
| Ω.A.B.CFG.15a | READ | GC1_USE_RUNTIME | os.getenv |
| Ω.A.B.CFG.15b | TRIM | GC1_USE_RUNTIME | strip |
| Ω.A.B.CFG.15c | DEFAULT | GC1_USE_RUNTIME | 0 |
| Ω.A.B.CFG.15d | VALID | GC1_USE_RUNTIME | bool |
| Ω.A.B.CFG.16a | READ | GC1_RUNTIME_VERIFY_EYE | os.getenv |
| Ω.A.B.CFG.16b | TRIM | GC1_RUNTIME_VERIFY_EYE | strip |
| Ω.A.B.CFG.16c | DEFAULT | GC1_RUNTIME_VERIFY_EYE | 0 |
| Ω.A.B.CFG.16d | VALID | GC1_RUNTIME_VERIFY_EYE | bool |
| Ω.A.B.CFG.17a | READ | GC1_SKIP_AUTOCHRO_EXPORT | os.getenv |
| Ω.A.B.CFG.17b | TRIM | GC1_SKIP_AUTOCHRO_EXPORT | strip |
| Ω.A.B.CFG.17c | DEFAULT | GC1_SKIP_AUTOCHRO_EXPORT | 0 |
| Ω.A.B.CFG.17d | VALID | GC1_SKIP_AUTOCHRO_EXPORT | bool |
| Ω.A.B.CFG.18a | READ | REQUIRED_HOTSPOT | os.getenv |
| Ω.A.B.CFG.18b | TRIM | REQUIRED_HOTSPOT | strip |
| Ω.A.B.CFG.18c | DEFAULT | REQUIRED_HOTSPOT | iPhone |
| Ω.A.B.CFG.18d | VALID | REQUIRED_HOTSPOT | csv ssid |
| Ω.A.B.CFG.19a | READ | GC1_HOTSPOT_RECONNECT_MIN_SEC | os.getenv |
| Ω.A.B.CFG.19b | TRIM | GC1_HOTSPOT_RECONNECT_MIN_SEC | strip |
| Ω.A.B.CFG.19c | DEFAULT | GC1_HOTSPOT_RECONNECT_MIN_SEC | 90 |
| Ω.A.B.CFG.19d | VALID | GC1_HOTSPOT_RECONNECT_MIN_SEC | int≥0 |

### §B-STATE `.gc_autochro_job.json`

| 필드 | leaf 쓰기 |
|------|-----------|
| job_id | STW uuid4 |
| started_at | STW iso8601 |
| data_name | STW string |
| pdf_path_planned | STW string |
| prep_enabled | STW bool |
| phase_current | STW enum P0..P9 |
| atom_current | STW string |
| resume_from | STW atom_id\|null |
| atoms.{id}.status | STW pending\|running\|ok\|fail\|skip |
| atoms.{id}.attempt | STW int |
| atoms.{id}.channel_used | STW H\|E\|F\|W |
| atoms.{id}.fail_code | STW string\|null |
| atoms.{id}.probe_snapshot | STW object |
| atoms.{id}.started_at | STW iso |
| atoms.{id}.ended_at | STW iso |
| hancom_windows_seen | STW int |

### §B-CLK

| ID | leaf |
|----|------|
| Ω.A.B.CLK.01.PURE.monotonic | `time.monotonic()` |
| Ω.A.B.CLK.02.PURE.wall | `datetime.now()` |
| Ω.A.B.CLK.03.PURE.delta | `monotonic - last_edge` |
| Ω.A.B.CLK.04.CMP.debounce | `delta >= GC1_HOTSPOT_RECONNECT_MIN_SEC` |

---

## §L0 — 프로브 (부작용 0)

> **T11 전량:** [GC1_RUNTIME_DESIGN_PART1_L0.md](GC1_RUNTIME_DESIGN_PART1_L0.md) — WIFI/WIN/LV/TR/TAB/DN/MTD/PDF/SCR(420)/TASK/FOCUS  
> 아래는 요약 인덱스.

### §L0-WIFI

| ID | leaf |
|----|------|
| Ω.A.L0.WIFI.01.PROC.spawn | `netsh wlan show interfaces` |
| Ω.A.L0.WIFI.02.WAIT.proc | timeout 30s |
| Ω.A.L0.WIFI.03.CMP.rc | returncode==0 |
| Ω.A.L0.WIFI.04.RX.ssid | line `SSID` not `BSSID` → ssid |
| Ω.A.L0.WIFI.05.WAIT.retry | sleep 1.5 |
| Ω.A.L0.WIFI.06.CMP.attempt | attempt < max_attempts |
| Ω.A.L0.WIFI.07.PURE.cache_at | monotonic cache |
| Ω.A.L0.WIFI.08.CMP.cache_ttl | age <= 180s → use cached ssid |
| Ω.A.L0.WIFI.09.CMP.allowed | ssid in REQUIRED_HOTSPOT list |

### §L0-WIN (Autochro 창)

| ID | leaf |
|----|------|
| Ω.A.L0.WIN.01.PROC.find | `findwindows(title_re=.*pattern.*)` |
| Ω.A.L0.WIN.02.CMP.count | len(handles)>=1 |
| Ω.A.L0.WIN.03.W32.connect | `Application.connect(handle)` per handle |
| Ω.A.L0.WIN.04.CMP.visible | `win.is_visible()` → score+=100 |
| Ω.A.L0.WIN.04b.PURE.area | w×h//1000 cap 500 → score |
| Ω.A.L0.WIN.04c.CMP.tree | descendants SysTreeView32 → score+=200 |
| Ω.A.L0.WIN.04d.CMP.list | descendants SysListView32 → score+=100 |
| Ω.A.L0.WIN.05.PURE.argmax | best handle |
| Ω.A.L0.WIN.06.W32.rect | `win.rectangle()` → Rect |
| Ω.A.L0.WIN.07.CMP.fg | foreground hwnd == win hwnd |

### §L0-LV (ListView 후보 — **ctrl마다** 02a~02i 반복)

| ID | leaf |
|----|------|
| Ω.A.L0.LV.01.W32.desc | descendants SysListView32 |
| Ω.A.L0.LV.02a.W32.rect | ctrl.rectangle() |
| Ω.A.L0.LV.02b.W32.count | item_count() |
| Ω.A.L0.LV.02c.CMP.n | n>0 |
| Ω.A.L0.LV.02d.CMP.h | height>=60 |
| Ω.A.L0.LV.02e.CMP.w | width>=180 |
| Ω.A.L0.LV.02f.PURE.frac | rel_mid_y/win_h |
| Ω.A.L0.LV.02g.CMP.lower | prefer lower → frac>=0.30 |
| Ω.A.L0.LV.02h.CMP.upper | prefer upper → frac<=0.72 |
| Ω.A.L0.LV.02i.PURE.append | candidates[] |
| Ω.A.L0.LV.03.PURE.fallback | prefer fail → retry any |

### §L0-LV-PICK

| ID | leaf |
|----|------|
| Ω.A.L0.LVP.01.PURE.score | item_count |
| Ω.A.L0.LVP.02.PURE.bias | (1-abs(frac-target))×1000 |
| Ω.A.L0.LVP.03.PURE.sum | score total |
| Ω.A.L0.LVP.04.PURE.argmax | selected ctrl |

target_frac: upper=0.35, lower=0.75, any=0.5

### §L0-TR (TreeView)

| ID | leaf |
|----|------|
| Ω.A.L0.TR.01.W32.desc | SysTreeView32 all |
| Ω.A.L0.TR.02.PURE.rel_left | rect.left - win.left |
| Ω.A.L0.TR.03.CMP.half | rel_left <= win.width×0.5 |
| Ω.A.L0.TR.04.PURE.area | h×w |
| Ω.A.L0.TR.05.PURE.max | largest left tree |

### §L0-TAB

| ID | leaf |
|----|------|
| Ω.A.L0.TAB.01.W32.child | SysTabControl32 Tab1 |
| Ω.A.L0.TAB.02.W32.menu | menu_items() texts[] |
| Ω.A.L0.TAB.03.CMP.analysis | any "분석목록" in t |
| Ω.A.L0.TAB.04.CMP.control | any "제어목록" in t |

### §L0-DN (데이터명)

| ID | leaf |
|----|------|
| Ω.A.L0.DN.01.W32.tab | select control tab |
| Ω.A.L0.DN.02.WAIT | 300ms |
| Ω.A.L0.DN-T.01.W32.title | window_text() |
| Ω.A.L0.DN-T.02.RX | `\s[-–]\s+.*[Aa]utochro` |
| Ω.A.L0.DN-T.03.PURE.slice | before match |
| Ω.A.L0.DN-T.04.PURE.split | split(".")[0] |
| Ω.A.L0.DN-T.05.RX.date | `^\d{6}` or `^\d{8}` |
| Ω.A.L0.DN-R.01.loop | tree lines[] |
| Ω.A.L0.DN-R.02.CMP.marker | YL6500 GC in line |
| Ω.A.L0.DN-R.03.PURE.prev | lines[idx-1] |
| Ω.A.L0.DN-R.04.W32.sel | get_selected()[0] fallback |
| Ω.A.L0.DN.99.CMP.ok | non-empty or **E_DATA_NAME** |

### §L0-MTD

| ID | leaf |
|----|------|
| Ω.A.L0.MTD.01.RX.date6 | `^(\d{6})` from data_name |
| Ω.A.L0.MTD.01b.RX.date8 | `^(\d{8})` |
| Ω.A.L0.MTD.02.PURE.path | dir + f"{date} 분석방법.MTD" |
| Ω.A.L0.MTD.03.FS.isfile | exists → else **E_MTD_MISSING** |

### §L0-PDF

| ID | leaf |
|----|------|
| Ω.A.L0.PDF.01.FS.isfile | path |
| Ω.A.L0.PDF.02.FS.mtime | mtime |
| Ω.A.L0.PDF.03.FS.read4k | open rb read 4096 |
| Ω.A.L0.PDF.04.CMP.lock | PermissionError → locked |
| Ω.A.L0.PDF.05.FITZ.pages | page_count (post-save) |

### §L0-SCR (눈 — **단계마다** GEO→CAP→ZOOM→PRE→OCR)

**GEO (region 1회)**

| ID | leaf |
|----|------|
| Ω.A.L0.SCR.G.01.FS.load | screen_regions.gc1.json |
| Ω.A.L0.SCR.G.02.PURE.parent | resolve parent chain |
| Ω.A.L0.SCR.G.03.PURE.abs | win_rect × box_frac |
| Ω.A.L0.SCR.G.04.CMP.min | w>=1,h>=1 |

**CAP**

| ID | leaf |
|----|------|
| Ω.A.L0.SCR.C.01.PROC.mss | mss.grab |
| Ω.A.L0.SCR.C.02.PURE.fallback | ImageGrab |
| Ω.A.L0.SCR.C.03.PURE.rgb | frombytes |

**ZOOM**

| ID | leaf |
|----|------|
| Ω.A.L0.SCR.Z.01.CMP.scale1 | scale<=1 skip |
| Ω.A.L0.SCR.Z.02.PURE.dim | nw,nh round |
| Ω.A.L0.SCR.Z.03.PURE.resize | LANCZOS |

**PRE**

| ID | leaf |
|----|------|
| Ω.A.L0.SCR.P.01.PURE.gray | grayscale |
| Ω.A.L0.SCR.P.02.PURE.contrast | ×1.35 |

**OCR (token i마다 04a~04e)**

| ID | leaf |
|----|------|
| Ω.A.L0.SCR.O.01.FS.tess | tesseract.exe |
| Ω.A.L0.SCR.O.02.PROC.str | image_to_string |
| Ω.A.L0.SCR.O.03.PROC.data | image_to_data |
| Ω.A.L0.SCR.O.04a.PURE.strip | text |
| Ω.A.L0.SCR.O.04b.CMP.empty | skip |
| Ω.A.L0.SCR.O.04c.CMP.conf0 | conf<0 skip |
| Ω.A.L0.SCR.O.04d.CMP.conf25 | conf<25 skip |
| Ω.A.L0.SCR.O.04e.PURE.token | append OcrToken |

**HIERARCHICAL READ (region × stage — 각 조합 독립 leaf 체인)**

regions: `bottom_tabs`, `left_analysis_tree`, `top_sample_table`, `bottom_peak_table`, `bottom_peak_table_fine`, `chromatogram_center`, `autochro_window`  
stages: `full`(1.0×) → `panel`(2.5×) → `fine`(3.5×)

per (region, stage): GEO.01→04, CAP.01→03, Z.01→03, P.01→02, O.01→04e  
= **7 regions × 3 stages × 14 leaf = 294 leaf** (Ω.A.L0.SCR.H.*)

**TASK (read_tasks)** — each TASK = full hierarchical read + verify

| task | verify leaf |
|------|-------------|
| verify_active_tab_analysis | CMP "분석목록" in plain_text |
| verify_peak_table_has_data | RX numeric≥1, reject mostly_zero |
| verify_peak_table_cleared | CMP zero ratio ≥ 0.85 |

**FOCUS overlay**

| ID | leaf |
|----|------|
| Ω.A.L0.FOC.01.W32.create | hollow rect |
| Ω.A.L0.FOC.02.WAIT.min | GC_SCREEN_FOCUS_MS clamp 150-400 |
| Ω.A.L0.FOC.03.W32.destroy | prev box |

---

## §L1 — 팩트 (L0 조합, IO 없음)

| ID | 입력 | 출력 |
|----|------|------|
| Ω.A.L1.01.PURE.pdf_stem | data_name | sanitize_sample_name |
| Ω.A.L1.02.PURE.pdf_path | output_dir+stem+.pdf | path |
| Ω.A.L1.03.PURE.tree_match | line,data_name | bool (norm, startswith base+" ", base+"-") |
| Ω.A.L1.04.PURE.crm_need | crm mtime vs state | bool |
| Ω.A.L1.05.PURE.pdf_fresh | pdf mtime age < skip_sec | bool |

---

## §L2 — 게이트

> **T12 전량:** [GC1_RUNTIME_DESIGN_PART1_L2.md](GC1_RUNTIME_DESIGN_PART1_L2.md)

### G-EX (export 잡)

```
G1 = CFG.enabled OR force
G2 = NOT E_IDENT_CROSS_PC
G3 = L0-WIN.02
G4 = IF prep: L0-MTD.03
G5 = L1.04 OR force
G6 = NOT pipeline_locked
RUN = G1∧G2∧G3∧G4∧G5∧G6
```

### G-ATOM (모든 L4 원자)

```
G-PRE  = ∧ pre_probe
G-POST = ∧ post_probe
G-RETRY = attempt < max_attempt → same atom after retry_delay_ms
G-FB   = channel H fail → retry E same matcher (if configured)
```

---

## §L3 — 액추에이터 채널 (각 호출 = 1 leaf)

### H (Hand) — 16 leaf types

| H-ID | W32 op |
|------|--------|
| H.01 | restore |
| H.02 | set_focus(win) |
| H.03 | move_window |
| H.04 | tabs.select(i) |
| H.05 | click_input left coords |
| H.06 | click_input right coords |
| H.07 | double_click_input |
| H.08 | send_keys |
| H.09 | menu_select path |
| H.10 | menu_item.click |
| H.11 | set_edit_text |
| H.12 | type_keys |
| H.13 | child_window(Button).click |
| H.14 | dlg.set_focus |
| H.15 | tree.select |
| H.16 | wrapper_object |

### E (Eye) — 5 leaf types

| E-ID | op |
|----|-----|
| E.01 | hierarchical_read(region) |
| E.02 | find_token(text) |
| E.03 | PURE token center xy |
| E.04 | H.05 click at token |
| E.05 | focus_overlay show/destroy |

### F (File) — 8 leaf types

| F-ID | op |
|----|-----|
| F.01 | FS.makedirs |
| F.02 | FS.unlink |
| F.03 | FS.glob |
| F.04 | find dialog by title_re |
| F.05 | pick filename Edit |
| F.06 | click Open/Save |
| F.07 | confirm overwrite Yes |
| F.08 | record_export state |

### W (Wait) — 3 leaf types

| W-ID | op |
|----|-----|
| W.01 | sleep(fixed_ms) |
| W.02 | poll_until(probe, interval, deadline) |
| W.03 | retry_delay from on_fail |

---

## §L4 — 페이즈·원자 (요약 — **전량은 PART2**)

> 72 atom × 7필드. action leaf ~225. P5/P6는 P2/P3 재사용이나 **atom ID·STW 독립**.

### P0 JOB_PRELUDE

| atom | action leaves |
|------|----------------|
| P0.01 | loop hancom: L0-WIN.04 → is_complete\|close_enabled → H.close(닫기 only) → WAIT 0.3 |
| P0.02 | L0-WIN connect chain → H.prepare_window: restore→focus→move→WAIT 0.6→focus |
| P0.03 | L0-DN chain → STW data_name |
| P0.04 | L1.01→L1.02 → STW pdf_path_planned |
| P0.05 | L1.05 fresh skip → early return ok |
| P0.06 | STW job init all atoms pending |

### P1 sync_control_to_analysis

| atom | leaves |
|------|--------|
| P1.01 | H.select_control_tab: L0-TAB.04? else tabs.select(1) WAIT 800 |
| P1.02 | L0-LVP lower → control_sync_list |
| P1.03 | H.set_focus list |
| P1.04 | H.click neutral |
| P1.05 | PURE rel_x=max(20,w//4) |
| P1.06 | PURE rel_y=max(12,h-24) |
| P1.07 | H.double_click coords |
| P1.08 | WAIT 1500 |
| P1.09 | H.select_analysis: L0-TAB.03? else select(0) WAIT 800 |
| P1.10 | POST L0-TAB.03 else E_P1_TAB |
| P1.11 | [opt] TASK verify_active_tab_analysis |

### P2 select_all_samples

| atom | leaves |
|------|--------|
| P2.01 | H.select_analysis_tab |
| P2.02 | L0-LVP upper → sample table |
| P2.03a | H.set_focus |
| P2.03b | PURE x=w×NEUTRAL_X_FRAC |
| P2.03c | PURE y=h×0.45 |
| P2.03d | H.click coords |
| P2.04 | H.send_keys ^a |
| P2.05 | WAIT 500 |

### P3 context_initialize (1차)

| atom | leaves |
|------|--------|
| P3.01 | H.select_analysis |
| P3.02 | L0-LVP upper |
| P3.03a-d | H.rclick: focus, coords, WAIT 350 |
| P3.04 | H.popup_menu (loop #32768): scan items → CMP matcher → click → **E_P3_MENU** |
| P3.04a | Desktop.windows class #32768 |
| P3.04b | wrapper.menu().items() |
| P3.04c | CMP "초기화"∧¬"정량"∧¬"검량" |
| P3.04d | menu_item.click |
| P3.04e | WAIT 120 loop |
| P3.05 | WAIT 800 |
| P3.06 | POST TASK verify_peak_table_cleared |

### P4 load_analysis_method

| atom | leaves |
|------|--------|
| P4.01 | L0-MTD full |
| P4.02 | H.select_analysis |
| P4.03 | tree select loop: L0-TR, lines, L1.03 match, try select×3, **E_P4_TREE** |
| P4.04 | H.rclick tree item center |
| P4.05 | H.popup "분석방법"+"불러" |
| P4.06a | find dialog title |
| P4.06b | H.focus dlg |
| P4.06c | PURE normpath abs mtd |
| P4.06d | H.set_edit_text path |
| P4.06e | WAIT 400 |
| P4.06f | H.click 열기 or %o |
| P4.06g | WAIT 300 |
| P4.07 | WAIT 2000 |
| P4.08 | POST TASK verify_peak_table_has_data |

### P5 P6

P2+P3 재실행, `attempt=2` STW only.

### P7 initialize_quantify

| atom | leaves |
|------|--------|
| P7.01 | P2 subtree |
| P7.02 | H.menu 시료목록→초기화+정량 (+fallback) |
| P7.03 | WAIT 3000 |
| P7.04 loop | find progress window / break after 5s idle / WAIT 1000 |
| P7.05 | POST verify_peak_has_data |

### P8 print_pdf

| atom | leaves |
|------|--------|
| P8.01 | P2 |
| P8.02 | H.win.set_focus |
| P8.03 | H.send_keys ^p |
| P8.04 | WAIT 1000 |
| P8.05 | print dialog: find / ENTER / btn 확인 / ENTER |
| P8.06 | poll save dialog until print_wait_sec |

### P9 save_pdf

| atom | leaves |
|------|--------|
| P9.01 | FS.makedirs |
| P9.02 | find save dlg max(dialog,120) **E_P9_DLG** |
| P9.03 | H.focus |
| P9.04 | PURE stem |
| P9.05 | find Edit descendant |
| P9.06 | H.set_edit_text stem |
| P9.07 | WAIT 500 |
| P9.08 | H.save btn or %s |
| P9.09 | overwrite dlg → 예 |
| P9.10 | hancom loop (see §P9-HANCOM) |
| P9.11 | wait_for_pdf_file_ready poll **E_P9_READY** |
| P9.12 | fallback newest pdf glob |
| P9.13 | CLEAN CL.* |
| P9.14 | STW record_export |

### §P9-HANCOM (loop body **매 0.5s** leaf)

| ID | leaf |
|----|------|
| Ω.A.L4.P9.H.01.W32.find | all hancom windows |
| Ω.A.L4.P9.H.02.CMP.empty | seen? return |
| Ω.A.L4.P9.H.03.CMP.complete | static text complete |
| Ω.A.L4.P9.H.04.H.close | 닫기 only |
| Ω.A.L4.P9.H.05.CMP.close_en | close btn enabled |
| Ω.A.L4.P9.H.06.RX.progress | N/M 페이지 |
| Ω.A.L4.P9.H.07.LOG.progress | if changed |
| Ω.A.L4.P9.H.08.WAIT | 300-500ms |

---

## §L6 — export 이후 (기존 gc_gc1 · gc_pipeline)

### §L6-CLEAN (CL.*)

| ID | leaf |
|----|------|
| CL.01.FS.glob | *.pdf |
| CL.02.PROC.parse | quiet Gc1PdfReport each |
| CL.03.CMP.obsolete | _is_obsolete_gc1_stem |
| CL.04.CMP.truncated | _is_truncated_gc1_stem |
| CL.05.CMP.same_exp | fingerprint injections — **버그 수정 지점** |
| CL.06.PURE.group | _experiment_group_key |
| CL.07.FS.unlink | pdf+xlsx |
| CL.08.PURE.return | removed, kept_path |

### §L6-PARSE (PAR.*) — trim **주입마다**

| ID | leaf |
|----|------|
| PAR.01 | wait pdf ready |
| PAR.02 | fitz open |
| PAR.03 | per page extract text |
| PAR.04 | parse_pdf_page |
| PAR.05 | merge overflow |
| PAR.06 | collect cycles |
| PAR.07a | measure B scan end min |
| PAR.07b | CMP < LAST_CYCLE_MIN → drop |
| PAR.08a | drop pre-noise H2 |
| PAR.08b | drop reduction cycles |
| PAR.08c | drop transition 1 |
| PAR.08d | **KEEP** first reaction (R-04) |
| PAR.09 | write FID sheet |
| PAR.10 | write TCD sheet |

### §L6-MAIL

| ID | leaf |
|----|------|
| ML.01 | gate force/skip cooldown |
| ML.02 | attach xlsx path |
| ML.03 | SMTP connect |
| ML.04 | send |
| ML.05 | verify/log |

---

## §L7 — 세션 (watch / force)

### §L7-WATCH tick (1 edge = leaf chain)

| ID | leaf |
|----|------|
| Ω.A.L7.W.01 | L0-WIFI.09 |
| Ω.A.L7.W.02 | CMP edge connected (was disconnected) |
| Ω.A.L7.W.03 | B-CLK debounce |
| Ω.A.L7.W.04 | STW session_id |
| Ω.A.L7.W.05 | invoke L6 export force=True once |
| Ω.A.L7.W.06 | STW session_complete |

### §L7-FORCE

| ID | leaf |
|----|------|
| Ω.A.L7.F.01 | bypass G4 G5 partial |
| Ω.A.L7.F.02 | full P0-P9 |

---

# 타워 B — 은규 PC

**전량:** [PART5_TOWER_B](GC1_RUNTIME_DESIGN_PART5_TOWER_B.md) — B-P1 IMAP ~55 leaf, B-P2~P4, JobRunner, Supervisor.

---

## §ERR — 실패 코드 → 은규 한 줄

> **T12 전량:** [GC1_RUNTIME_DESIGN_PART1_L2.md](GC1_RUNTIME_DESIGN_PART1_L2.md) §ERR

| code | 메시지 |
|------|--------|
| E_IDENT_CROSS_PC | 이 PC에서는 Autochro를 실행하지 않습니다 |
| E_WIN_NONE | Autochro 창을 찾지 못했습니다 |
| E_DATA_NAME | 제어목록 이름을 읽지 못했습니다 |
| E_MTD_MISSING | 바탕화면에 {date} 분석방법.MTD 가 없습니다 |
| E_P1_TAB | 분석목록 탭으로 바꾸지 못했습니다 |
| E_P3_MENU | 초기화 메뉴를 찾지 못했습니다 |
| E_P4_TREE | 트리에서 시료명을 찾지 못했습니다 |
| E_P9_DLG | PDF 저장 창이 뜨지 않았습니다 |
| E_P9_READY | PDF가 저장되지 않았습니다 |
| E_VERIFY_PEAK | 피크 표 숫자가 맞지 않습니다 |
| E_CLEAN_WRONG | PDF 정리 중 잘못된 파일이 선택되었습니다 |

---

## §MOD — 사용자 수정사항 슬롯 (다음 입력)

| MOD-ID | 영향 leaf | R 변경 |
|--------|-----------|--------|
| MOD-1 | (대기) | 없음 |
| MOD-2 | (대기) | 없음 |
| MOD-3 | (대기) | 없음 |

---

## §STATS — leaf 카운트 (**절대 최대**, PART 1~6 합)

| 블록 | 고정 leaf | 가변 leaf |
|------|-----------|-----------|
| Ω.A.B | 110 | — |
| Ω.A.L0 (기본) | 95 | — |
| Ω.A.L0.SCR hierarchical | 294 | — |
| Ω.A.L1–L3 | 47 | — |
| Ω.A.L4 (PART2) | 225 | hancom loop × iterations |
| Ω.A.L6 (PART3) | 53 | **6×N** trim + **7×files** clean + **2×pages** parse |
| Ω.A.L7–L8 (PART4) | 45 | — |
| Ω.A.RETRY (PART6) | 32 | — |
| Ω.B (PART5) | 160 | **×mail items × attachments** |
| **합계 (典型)** | **~1060** | N=50 주입 → **+300** → **~1360** |

**가변 공식:**  
`TOTAL = 1060 + 6×N + 2×P + 7×F + 8×M×A + hancom_iters×8`  
(N=주입 수, P=PDF 페이지, F=clean 후보 파일, M=메일, A=첨부)

**leaf 종료:** §0-3 기준 더 쪼개면 W32 단일 API 호출 이하만 남음 → **설계 종료**.

---

## §DONE

- 타워 A Autochro + parse + mail + watch: **leaf 전개 완료**  
- 타워 B IMAP→Origin: **leaf 전개 완료** (PART5)  
- retry/resume/blocked: **완료** (PART6)  
- **MOD-* 입력 시:** §MOD subtree만 추가 leaf (R 불변)

**구현·Hook 큐·코드:** MOD 반영 후.
