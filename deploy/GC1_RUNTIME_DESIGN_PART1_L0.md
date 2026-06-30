# GC1 Runtime 설계 — PART 1: Ω-L0 프로브 (전 leaf)

> 상위: [GC1_RUNTIME_DESIGN.md](GC1_RUNTIME_DESIGN.md)  
> **T11:** WIFI · WIN · LV · TR · TAB · DN · MTD · PDF · SCR · TASK · FOCUS

---

## §L0-WIFI (Ω.A.L0.WIFI.01–09)

| ID | leaf | out |
|----|------|-----|
| Ω.A.L0.WIFI.01.PROC.spawn | subprocess netsh wlan show interfaces | CompletedProcess |
| Ω.A.L0.WIFI.02.WAIT.proc | wait timeout 30s | rc |
| Ω.A.L0.WIFI.03.CMP.rc | returncode==0 | bool |
| Ω.A.L0.WIFI.04.RX.line | for line in stdout | str |
| Ω.A.L0.WIFI.04b.CMP.bssid | skip line startswith BSSID | — |
| Ω.A.L0.WIFI.04c.RX.ssid | SSID: value after colon | ssid\|null |
| Ω.A.L0.WIFI.05.WAIT.retry | sleep 1.5 | — |
| Ω.A.L0.WIFI.06.CMP.attempt | attempt < max_attempts(3) | bool |
| Ω.A.L0.WIFI.07.PURE.cache_at | monotonic at success | float |
| Ω.A.L0.WIFI.08.CMP.cache_ttl | age<=180 use cache | ssid |
| Ω.A.L0.WIFI.09.CMP.allowed | ssid in parse(REQUIRED_HOTSPOT) | bool |

---

## §L0-WIN (Ω.A.L0.WIN.01–07)

| ID | leaf |
|----|------|
| Ω.A.L0.WIN.01.PROC.find | findwindows(title_re) |
| Ω.A.L0.WIN.02.CMP.count | len(handles)>=1 |
| Ω.A.L0.WIN.03.W32.connect | Application.connect per handle |
| Ω.A.L0.WIN.04a.CMP.visible | is_visible +100 |
| Ω.A.L0.WIN.04b.PURE.area | min(w*h//1000,500) |
| Ω.A.L0.WIN.04c.CMP.tree | SysTreeView32 exists +200 |
| Ω.A.L0.WIN.04d.CMP.list | SysListView32 exists +100 |
| Ω.A.L0.WIN.05.PURE.argmax | max score handle |
| Ω.A.L0.WIN.06.W32.rect | rectangle() |
| Ω.A.L0.WIN.07.CMP.fg | GetForegroundWindow==hwnd |

---

## §L0-LV per-ctrl (Ω.A.L0.LV.01–03, ctrl×9)

| ID | leaf |
|----|------|
| Ω.A.L0.LV.01.W32.desc | descendants SysListView32 |
| Ω.A.L0.LV.02a.W32.rect | rectangle |
| Ω.A.L0.LV.02b.W32.count | item_count |
| Ω.A.L0.LV.02c.CMP.n | n>0 |
| Ω.A.L0.LV.02d.CMP.h | h>=60 |
| Ω.A.L0.LV.02e.CMP.w | w>=180 |
| Ω.A.L0.LV.02f.PURE.frac | rel_mid_y/win_h |
| Ω.A.L0.LV.02g.CMP.lower | frac>=0.30 if prefer lower |
| Ω.A.L0.LV.02h.CMP.upper | frac<=0.72 if prefer upper |
| Ω.A.L0.LV.02i.PURE.append | candidates[] |
| Ω.A.L0.LV.03.PURE.fallback | retry prefer any |

---

## §L0-LV-PICK (Ω.A.L0.LVP.01–04)

| ID | leaf | target_frac |
|----|------|-------------|
| Ω.A.L0.LVP.01.PURE.score | item_count | — |
| Ω.A.L0.LVP.02.PURE.bias | (1-abs(frac-target))*1000 | upper 0.35 lower 0.75 any 0.5 |
| Ω.A.L0.LVP.03.PURE.sum | score+bias | — |
| Ω.A.L0.LVP.04.PURE.argmax | pick ctrl | — |

---

## §L0-TR (Ω.A.L0.TR.01–05)

| ID | leaf |
|----|------|
| Ω.A.L0.TR.01.W32.desc | all SysTreeView32 |
| Ω.A.L0.TR.02.PURE.rel_left | left-win.left |
| Ω.A.L0.TR.03.CMP.half | rel_left<=0.5*width |
| Ω.A.L0.TR.04.PURE.area | h*w |
| Ω.A.L0.TR.05.PURE.max | argmax area left half |

---

## §L0-TAB (Ω.A.L0.TAB.01–04)

| ID | leaf |
|----|------|
| Ω.A.L0.TAB.01.W32.child | SysTabControl32 Tab1 |
| Ω.A.L0.TAB.02.W32.menu | menu_items texts |
| Ω.A.L0.TAB.03.CMP.analysis | any 분석목록 in t |
| Ω.A.L0.TAB.04.CMP.control | any 제어목록 in t |

---

## §L0-DN (Ω.A.L0.DN.*)

| ID | leaf |
|----|------|
| Ω.A.L0.DN.01.W32.tab | select control tab |
| Ω.A.L0.DN.02.WAIT | 300ms |
| Ω.A.L0.DN-T.01.W32.title | window_text |
| Ω.A.L0.DN-T.02.RX | dash Autochro pattern |
| Ω.A.L0.DN-T.03.PURE.slice | before match |
| Ω.A.L0.DN-T.04.PURE.splitdot | split . [0] |
| Ω.A.L0.DN-T.05a.RX | ^\\d{6} |
| Ω.A.L0.DN-T.05b.RX | ^\\d{8} |
| Ω.A.L0.DN-R.01.W32.texts | tree lines |
| Ω.A.L0.DN-R.02.CMP.marker | YL6500 GC |
| Ω.A.L0.DN-R.03.PURE.prevline | idx-1 |
| Ω.A.L0.DN-R.04.W32.selected | get_selected fallback |
| Ω.A.L0.DN.99.CMP.ok | non-empty else E_DATA_NAME |

---

## §L0-MTD (Ω.A.L0.MTD.01–03)

| ID | leaf |
|----|------|
| Ω.A.L0.MTD.01.RX.date6 | ^(\\d{6}) |
| Ω.A.L0.MTD.01b.RX.date8 | ^(\\d{8}) |
| Ω.A.L0.MTD.02.PURE.path | dir + date + 분석방법.MTD |
| Ω.A.L0.MTD.03.FS.isfile | exists else E_MTD_MISSING |

---

## §L0-PDF (Ω.A.L0.PDF.01–05)

| ID | leaf |
|----|------|
| Ω.A.L0.PDF.01.FS.isfile | path |
| Ω.A.L0.PDF.02.FS.mtime | mtime |
| Ω.A.L0.PDF.03.FS.read4k | rb read 4096 |
| Ω.A.L0.PDF.04.CMP.lock | PermissionError |
| Ω.A.L0.PDF.05.FITZ.pages | page_count |

---

## §L0-SCR-H hierarchical (420 leaf)

7 regions × 3 stages × 20 steps. ID: `Ω.A.L0.SCR.H.{regionIdx}{stageIdx}{step}`

| leaf ID | region | stage | step | op |
|---------|--------|-------|------|-----|
| Ω.A.L0.SCR.H.011G01 | autochro_window | full | G01 | FS.load config |
| Ω.A.L0.SCR.H.011G02 | autochro_window | full | G02 | PURE parent chain |
| Ω.A.L0.SCR.H.011G03 | autochro_window | full | G03 | PURE abs box |
| Ω.A.L0.SCR.H.011G04 | autochro_window | full | G04 | CMP min size |
| Ω.A.L0.SCR.H.011C01 | autochro_window | full | C01 | PROC mss.grab |
| Ω.A.L0.SCR.H.011C02 | autochro_window | full | C02 | PURE ImageGrab fallback |
| Ω.A.L0.SCR.H.011C03 | autochro_window | full | C03 | PURE rgb |
| Ω.A.L0.SCR.H.011Z01 | autochro_window | full | Z01 | CMP scale<=1 skip |
| Ω.A.L0.SCR.H.011Z02 | autochro_window | full | Z02 | PURE nw nh |
| Ω.A.L0.SCR.H.011Z03 | autochro_window | full | Z03 | PURE LANCZOS resize |
| Ω.A.L0.SCR.H.011P01 | autochro_window | full | P01 | PURE grayscale |
| Ω.A.L0.SCR.H.011P02 | autochro_window | full | P02 | PURE contrast 1.35 |
| Ω.A.L0.SCR.H.011O01 | autochro_window | full | O01 | FS tesseract |
| Ω.A.L0.SCR.H.011O02 | autochro_window | full | O02 | PROC to_string |
| Ω.A.L0.SCR.H.011O03 | autochro_window | full | O03 | PROC to_data |
| Ω.A.L0.SCR.H.011O04a | autochro_window | full | O04a | PURE strip |
| Ω.A.L0.SCR.H.011O04b | autochro_window | full | O04b | CMP empty skip |
| Ω.A.L0.SCR.H.011O04c | autochro_window | full | O04c | CMP conf<0 |
| Ω.A.L0.SCR.H.011O04d | autochro_window | full | O04d | CMP conf<25 |
| Ω.A.L0.SCR.H.011O04e | autochro_window | full | O04e | PURE token |
| Ω.A.L0.SCR.H.012G01 | autochro_window | panel | G01 | FS.load config |
| Ω.A.L0.SCR.H.012G02 | autochro_window | panel | G02 | PURE parent chain |
| Ω.A.L0.SCR.H.012G03 | autochro_window | panel | G03 | PURE abs box |
| Ω.A.L0.SCR.H.012G04 | autochro_window | panel | G04 | CMP min size |
| Ω.A.L0.SCR.H.012C01 | autochro_window | panel | C01 | PROC mss.grab |
| Ω.A.L0.SCR.H.012C02 | autochro_window | panel | C02 | PURE ImageGrab fallback |
| Ω.A.L0.SCR.H.012C03 | autochro_window | panel | C03 | PURE rgb |
| Ω.A.L0.SCR.H.012Z01 | autochro_window | panel | Z01 | CMP scale<=1 skip |
| Ω.A.L0.SCR.H.012Z02 | autochro_window | panel | Z02 | PURE nw nh |
| Ω.A.L0.SCR.H.012Z03 | autochro_window | panel | Z03 | PURE LANCZOS resize |
| Ω.A.L0.SCR.H.012P01 | autochro_window | panel | P01 | PURE grayscale |
| Ω.A.L0.SCR.H.012P02 | autochro_window | panel | P02 | PURE contrast 1.35 |
| Ω.A.L0.SCR.H.012O01 | autochro_window | panel | O01 | FS tesseract |
| Ω.A.L0.SCR.H.012O02 | autochro_window | panel | O02 | PROC to_string |
| Ω.A.L0.SCR.H.012O03 | autochro_window | panel | O03 | PROC to_data |
| Ω.A.L0.SCR.H.012O04a | autochro_window | panel | O04a | PURE strip |
| Ω.A.L0.SCR.H.012O04b | autochro_window | panel | O04b | CMP empty skip |
| Ω.A.L0.SCR.H.012O04c | autochro_window | panel | O04c | CMP conf<0 |
| Ω.A.L0.SCR.H.012O04d | autochro_window | panel | O04d | CMP conf<25 |
| Ω.A.L0.SCR.H.012O04e | autochro_window | panel | O04e | PURE token |
| Ω.A.L0.SCR.H.013G01 | autochro_window | fine | G01 | FS.load config |
| Ω.A.L0.SCR.H.013G02 | autochro_window | fine | G02 | PURE parent chain |
| Ω.A.L0.SCR.H.013G03 | autochro_window | fine | G03 | PURE abs box |
| Ω.A.L0.SCR.H.013G04 | autochro_window | fine | G04 | CMP min size |
| Ω.A.L0.SCR.H.013C01 | autochro_window | fine | C01 | PROC mss.grab |
| Ω.A.L0.SCR.H.013C02 | autochro_window | fine | C02 | PURE ImageGrab fallback |
| Ω.A.L0.SCR.H.013C03 | autochro_window | fine | C03 | PURE rgb |
| Ω.A.L0.SCR.H.013Z01 | autochro_window | fine | Z01 | CMP scale<=1 skip |
| Ω.A.L0.SCR.H.013Z02 | autochro_window | fine | Z02 | PURE nw nh |
| Ω.A.L0.SCR.H.013Z03 | autochro_window | fine | Z03 | PURE LANCZOS resize |
| Ω.A.L0.SCR.H.013P01 | autochro_window | fine | P01 | PURE grayscale |
| Ω.A.L0.SCR.H.013P02 | autochro_window | fine | P02 | PURE contrast 1.35 |
| Ω.A.L0.SCR.H.013O01 | autochro_window | fine | O01 | FS tesseract |
| Ω.A.L0.SCR.H.013O02 | autochro_window | fine | O02 | PROC to_string |
| Ω.A.L0.SCR.H.013O03 | autochro_window | fine | O03 | PROC to_data |
| Ω.A.L0.SCR.H.013O04a | autochro_window | fine | O04a | PURE strip |
| Ω.A.L0.SCR.H.013O04b | autochro_window | fine | O04b | CMP empty skip |
| Ω.A.L0.SCR.H.013O04c | autochro_window | fine | O04c | CMP conf<0 |
| Ω.A.L0.SCR.H.013O04d | autochro_window | fine | O04d | CMP conf<25 |
| Ω.A.L0.SCR.H.013O04e | autochro_window | fine | O04e | PURE token |
| Ω.A.L0.SCR.H.021G01 | bottom_tabs | full | G01 | FS.load config |
| Ω.A.L0.SCR.H.021G02 | bottom_tabs | full | G02 | PURE parent chain |
| Ω.A.L0.SCR.H.021G03 | bottom_tabs | full | G03 | PURE abs box |
| Ω.A.L0.SCR.H.021G04 | bottom_tabs | full | G04 | CMP min size |
| Ω.A.L0.SCR.H.021C01 | bottom_tabs | full | C01 | PROC mss.grab |
| Ω.A.L0.SCR.H.021C02 | bottom_tabs | full | C02 | PURE ImageGrab fallback |
| Ω.A.L0.SCR.H.021C03 | bottom_tabs | full | C03 | PURE rgb |
| Ω.A.L0.SCR.H.021Z01 | bottom_tabs | full | Z01 | CMP scale<=1 skip |
| Ω.A.L0.SCR.H.021Z02 | bottom_tabs | full | Z02 | PURE nw nh |
| Ω.A.L0.SCR.H.021Z03 | bottom_tabs | full | Z03 | PURE LANCZOS resize |
| Ω.A.L0.SCR.H.021P01 | bottom_tabs | full | P01 | PURE grayscale |
| Ω.A.L0.SCR.H.021P02 | bottom_tabs | full | P02 | PURE contrast 1.35 |
| Ω.A.L0.SCR.H.021O01 | bottom_tabs | full | O01 | FS tesseract |
| Ω.A.L0.SCR.H.021O02 | bottom_tabs | full | O02 | PROC to_string |
| Ω.A.L0.SCR.H.021O03 | bottom_tabs | full | O03 | PROC to_data |
| Ω.A.L0.SCR.H.021O04a | bottom_tabs | full | O04a | PURE strip |
| Ω.A.L0.SCR.H.021O04b | bottom_tabs | full | O04b | CMP empty skip |
| Ω.A.L0.SCR.H.021O04c | bottom_tabs | full | O04c | CMP conf<0 |
| Ω.A.L0.SCR.H.021O04d | bottom_tabs | full | O04d | CMP conf<25 |
| Ω.A.L0.SCR.H.021O04e | bottom_tabs | full | O04e | PURE token |
| Ω.A.L0.SCR.H.022G01 | bottom_tabs | panel | G01 | FS.load config |
| Ω.A.L0.SCR.H.022G02 | bottom_tabs | panel | G02 | PURE parent chain |
| Ω.A.L0.SCR.H.022G03 | bottom_tabs | panel | G03 | PURE abs box |
| Ω.A.L0.SCR.H.022G04 | bottom_tabs | panel | G04 | CMP min size |
| Ω.A.L0.SCR.H.022C01 | bottom_tabs | panel | C01 | PROC mss.grab |
| Ω.A.L0.SCR.H.022C02 | bottom_tabs | panel | C02 | PURE ImageGrab fallback |
| Ω.A.L0.SCR.H.022C03 | bottom_tabs | panel | C03 | PURE rgb |
| Ω.A.L0.SCR.H.022Z01 | bottom_tabs | panel | Z01 | CMP scale<=1 skip |
| Ω.A.L0.SCR.H.022Z02 | bottom_tabs | panel | Z02 | PURE nw nh |
| Ω.A.L0.SCR.H.022Z03 | bottom_tabs | panel | Z03 | PURE LANCZOS resize |
| Ω.A.L0.SCR.H.022P01 | bottom_tabs | panel | P01 | PURE grayscale |
| Ω.A.L0.SCR.H.022P02 | bottom_tabs | panel | P02 | PURE contrast 1.35 |
| Ω.A.L0.SCR.H.022O01 | bottom_tabs | panel | O01 | FS tesseract |
| Ω.A.L0.SCR.H.022O02 | bottom_tabs | panel | O02 | PROC to_string |
| Ω.A.L0.SCR.H.022O03 | bottom_tabs | panel | O03 | PROC to_data |
| Ω.A.L0.SCR.H.022O04a | bottom_tabs | panel | O04a | PURE strip |
| Ω.A.L0.SCR.H.022O04b | bottom_tabs | panel | O04b | CMP empty skip |
| Ω.A.L0.SCR.H.022O04c | bottom_tabs | panel | O04c | CMP conf<0 |
| Ω.A.L0.SCR.H.022O04d | bottom_tabs | panel | O04d | CMP conf<25 |
| Ω.A.L0.SCR.H.022O04e | bottom_tabs | panel | O04e | PURE token |
| Ω.A.L0.SCR.H.023G01 | bottom_tabs | fine | G01 | FS.load config |
| Ω.A.L0.SCR.H.023G02 | bottom_tabs | fine | G02 | PURE parent chain |
| Ω.A.L0.SCR.H.023G03 | bottom_tabs | fine | G03 | PURE abs box |
| Ω.A.L0.SCR.H.023G04 | bottom_tabs | fine | G04 | CMP min size |
| Ω.A.L0.SCR.H.023C01 | bottom_tabs | fine | C01 | PROC mss.grab |
| Ω.A.L0.SCR.H.023C02 | bottom_tabs | fine | C02 | PURE ImageGrab fallback |
| Ω.A.L0.SCR.H.023C03 | bottom_tabs | fine | C03 | PURE rgb |
| Ω.A.L0.SCR.H.023Z01 | bottom_tabs | fine | Z01 | CMP scale<=1 skip |
| Ω.A.L0.SCR.H.023Z02 | bottom_tabs | fine | Z02 | PURE nw nh |
| Ω.A.L0.SCR.H.023Z03 | bottom_tabs | fine | Z03 | PURE LANCZOS resize |
| Ω.A.L0.SCR.H.023P01 | bottom_tabs | fine | P01 | PURE grayscale |
| Ω.A.L0.SCR.H.023P02 | bottom_tabs | fine | P02 | PURE contrast 1.35 |
| Ω.A.L0.SCR.H.023O01 | bottom_tabs | fine | O01 | FS tesseract |
| Ω.A.L0.SCR.H.023O02 | bottom_tabs | fine | O02 | PROC to_string |
| Ω.A.L0.SCR.H.023O03 | bottom_tabs | fine | O03 | PROC to_data |
| Ω.A.L0.SCR.H.023O04a | bottom_tabs | fine | O04a | PURE strip |
| Ω.A.L0.SCR.H.023O04b | bottom_tabs | fine | O04b | CMP empty skip |
| Ω.A.L0.SCR.H.023O04c | bottom_tabs | fine | O04c | CMP conf<0 |
| Ω.A.L0.SCR.H.023O04d | bottom_tabs | fine | O04d | CMP conf<25 |
| Ω.A.L0.SCR.H.023O04e | bottom_tabs | fine | O04e | PURE token |
| Ω.A.L0.SCR.H.031G01 | left_analysis_tree | full | G01 | FS.load config |
| Ω.A.L0.SCR.H.031G02 | left_analysis_tree | full | G02 | PURE parent chain |
| Ω.A.L0.SCR.H.031G03 | left_analysis_tree | full | G03 | PURE abs box |
| Ω.A.L0.SCR.H.031G04 | left_analysis_tree | full | G04 | CMP min size |
| Ω.A.L0.SCR.H.031C01 | left_analysis_tree | full | C01 | PROC mss.grab |
| Ω.A.L0.SCR.H.031C02 | left_analysis_tree | full | C02 | PURE ImageGrab fallback |
| Ω.A.L0.SCR.H.031C03 | left_analysis_tree | full | C03 | PURE rgb |
| Ω.A.L0.SCR.H.031Z01 | left_analysis_tree | full | Z01 | CMP scale<=1 skip |
| Ω.A.L0.SCR.H.031Z02 | left_analysis_tree | full | Z02 | PURE nw nh |
| Ω.A.L0.SCR.H.031Z03 | left_analysis_tree | full | Z03 | PURE LANCZOS resize |
| Ω.A.L0.SCR.H.031P01 | left_analysis_tree | full | P01 | PURE grayscale |
| Ω.A.L0.SCR.H.031P02 | left_analysis_tree | full | P02 | PURE contrast 1.35 |
| Ω.A.L0.SCR.H.031O01 | left_analysis_tree | full | O01 | FS tesseract |
| Ω.A.L0.SCR.H.031O02 | left_analysis_tree | full | O02 | PROC to_string |
| Ω.A.L0.SCR.H.031O03 | left_analysis_tree | full | O03 | PROC to_data |
| Ω.A.L0.SCR.H.031O04a | left_analysis_tree | full | O04a | PURE strip |
| Ω.A.L0.SCR.H.031O04b | left_analysis_tree | full | O04b | CMP empty skip |
| Ω.A.L0.SCR.H.031O04c | left_analysis_tree | full | O04c | CMP conf<0 |
| Ω.A.L0.SCR.H.031O04d | left_analysis_tree | full | O04d | CMP conf<25 |
| Ω.A.L0.SCR.H.031O04e | left_analysis_tree | full | O04e | PURE token |
| Ω.A.L0.SCR.H.032G01 | left_analysis_tree | panel | G01 | FS.load config |
| Ω.A.L0.SCR.H.032G02 | left_analysis_tree | panel | G02 | PURE parent chain |
| Ω.A.L0.SCR.H.032G03 | left_analysis_tree | panel | G03 | PURE abs box |
| Ω.A.L0.SCR.H.032G04 | left_analysis_tree | panel | G04 | CMP min size |
| Ω.A.L0.SCR.H.032C01 | left_analysis_tree | panel | C01 | PROC mss.grab |
| Ω.A.L0.SCR.H.032C02 | left_analysis_tree | panel | C02 | PURE ImageGrab fallback |
| Ω.A.L0.SCR.H.032C03 | left_analysis_tree | panel | C03 | PURE rgb |
| Ω.A.L0.SCR.H.032Z01 | left_analysis_tree | panel | Z01 | CMP scale<=1 skip |
| Ω.A.L0.SCR.H.032Z02 | left_analysis_tree | panel | Z02 | PURE nw nh |
| Ω.A.L0.SCR.H.032Z03 | left_analysis_tree | panel | Z03 | PURE LANCZOS resize |
| Ω.A.L0.SCR.H.032P01 | left_analysis_tree | panel | P01 | PURE grayscale |
| Ω.A.L0.SCR.H.032P02 | left_analysis_tree | panel | P02 | PURE contrast 1.35 |
| Ω.A.L0.SCR.H.032O01 | left_analysis_tree | panel | O01 | FS tesseract |
| Ω.A.L0.SCR.H.032O02 | left_analysis_tree | panel | O02 | PROC to_string |
| Ω.A.L0.SCR.H.032O03 | left_analysis_tree | panel | O03 | PROC to_data |
| Ω.A.L0.SCR.H.032O04a | left_analysis_tree | panel | O04a | PURE strip |
| Ω.A.L0.SCR.H.032O04b | left_analysis_tree | panel | O04b | CMP empty skip |
| Ω.A.L0.SCR.H.032O04c | left_analysis_tree | panel | O04c | CMP conf<0 |
| Ω.A.L0.SCR.H.032O04d | left_analysis_tree | panel | O04d | CMP conf<25 |
| Ω.A.L0.SCR.H.032O04e | left_analysis_tree | panel | O04e | PURE token |
| Ω.A.L0.SCR.H.033G01 | left_analysis_tree | fine | G01 | FS.load config |
| Ω.A.L0.SCR.H.033G02 | left_analysis_tree | fine | G02 | PURE parent chain |
| Ω.A.L0.SCR.H.033G03 | left_analysis_tree | fine | G03 | PURE abs box |
| Ω.A.L0.SCR.H.033G04 | left_analysis_tree | fine | G04 | CMP min size |
| Ω.A.L0.SCR.H.033C01 | left_analysis_tree | fine | C01 | PROC mss.grab |
| Ω.A.L0.SCR.H.033C02 | left_analysis_tree | fine | C02 | PURE ImageGrab fallback |
| Ω.A.L0.SCR.H.033C03 | left_analysis_tree | fine | C03 | PURE rgb |
| Ω.A.L0.SCR.H.033Z01 | left_analysis_tree | fine | Z01 | CMP scale<=1 skip |
| Ω.A.L0.SCR.H.033Z02 | left_analysis_tree | fine | Z02 | PURE nw nh |
| Ω.A.L0.SCR.H.033Z03 | left_analysis_tree | fine | Z03 | PURE LANCZOS resize |
| Ω.A.L0.SCR.H.033P01 | left_analysis_tree | fine | P01 | PURE grayscale |
| Ω.A.L0.SCR.H.033P02 | left_analysis_tree | fine | P02 | PURE contrast 1.35 |
| Ω.A.L0.SCR.H.033O01 | left_analysis_tree | fine | O01 | FS tesseract |
| Ω.A.L0.SCR.H.033O02 | left_analysis_tree | fine | O02 | PROC to_string |
| Ω.A.L0.SCR.H.033O03 | left_analysis_tree | fine | O03 | PROC to_data |
| Ω.A.L0.SCR.H.033O04a | left_analysis_tree | fine | O04a | PURE strip |
| Ω.A.L0.SCR.H.033O04b | left_analysis_tree | fine | O04b | CMP empty skip |
| Ω.A.L0.SCR.H.033O04c | left_analysis_tree | fine | O04c | CMP conf<0 |
| Ω.A.L0.SCR.H.033O04d | left_analysis_tree | fine | O04d | CMP conf<25 |
| Ω.A.L0.SCR.H.033O04e | left_analysis_tree | fine | O04e | PURE token |
| Ω.A.L0.SCR.H.041G01 | top_sample_table | full | G01 | FS.load config |
| Ω.A.L0.SCR.H.041G02 | top_sample_table | full | G02 | PURE parent chain |
| Ω.A.L0.SCR.H.041G03 | top_sample_table | full | G03 | PURE abs box |
| Ω.A.L0.SCR.H.041G04 | top_sample_table | full | G04 | CMP min size |
| Ω.A.L0.SCR.H.041C01 | top_sample_table | full | C01 | PROC mss.grab |
| Ω.A.L0.SCR.H.041C02 | top_sample_table | full | C02 | PURE ImageGrab fallback |
| Ω.A.L0.SCR.H.041C03 | top_sample_table | full | C03 | PURE rgb |
| Ω.A.L0.SCR.H.041Z01 | top_sample_table | full | Z01 | CMP scale<=1 skip |
| Ω.A.L0.SCR.H.041Z02 | top_sample_table | full | Z02 | PURE nw nh |
| Ω.A.L0.SCR.H.041Z03 | top_sample_table | full | Z03 | PURE LANCZOS resize |
| Ω.A.L0.SCR.H.041P01 | top_sample_table | full | P01 | PURE grayscale |
| Ω.A.L0.SCR.H.041P02 | top_sample_table | full | P02 | PURE contrast 1.35 |
| Ω.A.L0.SCR.H.041O01 | top_sample_table | full | O01 | FS tesseract |
| Ω.A.L0.SCR.H.041O02 | top_sample_table | full | O02 | PROC to_string |
| Ω.A.L0.SCR.H.041O03 | top_sample_table | full | O03 | PROC to_data |
| Ω.A.L0.SCR.H.041O04a | top_sample_table | full | O04a | PURE strip |
| Ω.A.L0.SCR.H.041O04b | top_sample_table | full | O04b | CMP empty skip |
| Ω.A.L0.SCR.H.041O04c | top_sample_table | full | O04c | CMP conf<0 |
| Ω.A.L0.SCR.H.041O04d | top_sample_table | full | O04d | CMP conf<25 |
| Ω.A.L0.SCR.H.041O04e | top_sample_table | full | O04e | PURE token |
| Ω.A.L0.SCR.H.042G01 | top_sample_table | panel | G01 | FS.load config |
| Ω.A.L0.SCR.H.042G02 | top_sample_table | panel | G02 | PURE parent chain |
| Ω.A.L0.SCR.H.042G03 | top_sample_table | panel | G03 | PURE abs box |
| Ω.A.L0.SCR.H.042G04 | top_sample_table | panel | G04 | CMP min size |
| Ω.A.L0.SCR.H.042C01 | top_sample_table | panel | C01 | PROC mss.grab |
| Ω.A.L0.SCR.H.042C02 | top_sample_table | panel | C02 | PURE ImageGrab fallback |
| Ω.A.L0.SCR.H.042C03 | top_sample_table | panel | C03 | PURE rgb |
| Ω.A.L0.SCR.H.042Z01 | top_sample_table | panel | Z01 | CMP scale<=1 skip |
| Ω.A.L0.SCR.H.042Z02 | top_sample_table | panel | Z02 | PURE nw nh |
| Ω.A.L0.SCR.H.042Z03 | top_sample_table | panel | Z03 | PURE LANCZOS resize |
| Ω.A.L0.SCR.H.042P01 | top_sample_table | panel | P01 | PURE grayscale |
| Ω.A.L0.SCR.H.042P02 | top_sample_table | panel | P02 | PURE contrast 1.35 |
| Ω.A.L0.SCR.H.042O01 | top_sample_table | panel | O01 | FS tesseract |
| Ω.A.L0.SCR.H.042O02 | top_sample_table | panel | O02 | PROC to_string |
| Ω.A.L0.SCR.H.042O03 | top_sample_table | panel | O03 | PROC to_data |
| Ω.A.L0.SCR.H.042O04a | top_sample_table | panel | O04a | PURE strip |
| Ω.A.L0.SCR.H.042O04b | top_sample_table | panel | O04b | CMP empty skip |
| Ω.A.L0.SCR.H.042O04c | top_sample_table | panel | O04c | CMP conf<0 |
| Ω.A.L0.SCR.H.042O04d | top_sample_table | panel | O04d | CMP conf<25 |
| Ω.A.L0.SCR.H.042O04e | top_sample_table | panel | O04e | PURE token |
| Ω.A.L0.SCR.H.043G01 | top_sample_table | fine | G01 | FS.load config |
| Ω.A.L0.SCR.H.043G02 | top_sample_table | fine | G02 | PURE parent chain |
| Ω.A.L0.SCR.H.043G03 | top_sample_table | fine | G03 | PURE abs box |
| Ω.A.L0.SCR.H.043G04 | top_sample_table | fine | G04 | CMP min size |
| Ω.A.L0.SCR.H.043C01 | top_sample_table | fine | C01 | PROC mss.grab |
| Ω.A.L0.SCR.H.043C02 | top_sample_table | fine | C02 | PURE ImageGrab fallback |
| Ω.A.L0.SCR.H.043C03 | top_sample_table | fine | C03 | PURE rgb |
| Ω.A.L0.SCR.H.043Z01 | top_sample_table | fine | Z01 | CMP scale<=1 skip |
| Ω.A.L0.SCR.H.043Z02 | top_sample_table | fine | Z02 | PURE nw nh |
| Ω.A.L0.SCR.H.043Z03 | top_sample_table | fine | Z03 | PURE LANCZOS resize |
| Ω.A.L0.SCR.H.043P01 | top_sample_table | fine | P01 | PURE grayscale |
| Ω.A.L0.SCR.H.043P02 | top_sample_table | fine | P02 | PURE contrast 1.35 |
| Ω.A.L0.SCR.H.043O01 | top_sample_table | fine | O01 | FS tesseract |
| Ω.A.L0.SCR.H.043O02 | top_sample_table | fine | O02 | PROC to_string |
| Ω.A.L0.SCR.H.043O03 | top_sample_table | fine | O03 | PROC to_data |
| Ω.A.L0.SCR.H.043O04a | top_sample_table | fine | O04a | PURE strip |
| Ω.A.L0.SCR.H.043O04b | top_sample_table | fine | O04b | CMP empty skip |
| Ω.A.L0.SCR.H.043O04c | top_sample_table | fine | O04c | CMP conf<0 |
| Ω.A.L0.SCR.H.043O04d | top_sample_table | fine | O04d | CMP conf<25 |
| Ω.A.L0.SCR.H.043O04e | top_sample_table | fine | O04e | PURE token |
| Ω.A.L0.SCR.H.051G01 | bottom_peak_table | full | G01 | FS.load config |
| Ω.A.L0.SCR.H.051G02 | bottom_peak_table | full | G02 | PURE parent chain |
| Ω.A.L0.SCR.H.051G03 | bottom_peak_table | full | G03 | PURE abs box |
| Ω.A.L0.SCR.H.051G04 | bottom_peak_table | full | G04 | CMP min size |
| Ω.A.L0.SCR.H.051C01 | bottom_peak_table | full | C01 | PROC mss.grab |
| Ω.A.L0.SCR.H.051C02 | bottom_peak_table | full | C02 | PURE ImageGrab fallback |
| Ω.A.L0.SCR.H.051C03 | bottom_peak_table | full | C03 | PURE rgb |
| Ω.A.L0.SCR.H.051Z01 | bottom_peak_table | full | Z01 | CMP scale<=1 skip |
| Ω.A.L0.SCR.H.051Z02 | bottom_peak_table | full | Z02 | PURE nw nh |
| Ω.A.L0.SCR.H.051Z03 | bottom_peak_table | full | Z03 | PURE LANCZOS resize |
| Ω.A.L0.SCR.H.051P01 | bottom_peak_table | full | P01 | PURE grayscale |
| Ω.A.L0.SCR.H.051P02 | bottom_peak_table | full | P02 | PURE contrast 1.35 |
| Ω.A.L0.SCR.H.051O01 | bottom_peak_table | full | O01 | FS tesseract |
| Ω.A.L0.SCR.H.051O02 | bottom_peak_table | full | O02 | PROC to_string |
| Ω.A.L0.SCR.H.051O03 | bottom_peak_table | full | O03 | PROC to_data |
| Ω.A.L0.SCR.H.051O04a | bottom_peak_table | full | O04a | PURE strip |
| Ω.A.L0.SCR.H.051O04b | bottom_peak_table | full | O04b | CMP empty skip |
| Ω.A.L0.SCR.H.051O04c | bottom_peak_table | full | O04c | CMP conf<0 |
| Ω.A.L0.SCR.H.051O04d | bottom_peak_table | full | O04d | CMP conf<25 |
| Ω.A.L0.SCR.H.051O04e | bottom_peak_table | full | O04e | PURE token |
| Ω.A.L0.SCR.H.052G01 | bottom_peak_table | panel | G01 | FS.load config |
| Ω.A.L0.SCR.H.052G02 | bottom_peak_table | panel | G02 | PURE parent chain |
| Ω.A.L0.SCR.H.052G03 | bottom_peak_table | panel | G03 | PURE abs box |
| Ω.A.L0.SCR.H.052G04 | bottom_peak_table | panel | G04 | CMP min size |
| Ω.A.L0.SCR.H.052C01 | bottom_peak_table | panel | C01 | PROC mss.grab |
| Ω.A.L0.SCR.H.052C02 | bottom_peak_table | panel | C02 | PURE ImageGrab fallback |
| Ω.A.L0.SCR.H.052C03 | bottom_peak_table | panel | C03 | PURE rgb |
| Ω.A.L0.SCR.H.052Z01 | bottom_peak_table | panel | Z01 | CMP scale<=1 skip |
| Ω.A.L0.SCR.H.052Z02 | bottom_peak_table | panel | Z02 | PURE nw nh |
| Ω.A.L0.SCR.H.052Z03 | bottom_peak_table | panel | Z03 | PURE LANCZOS resize |
| Ω.A.L0.SCR.H.052P01 | bottom_peak_table | panel | P01 | PURE grayscale |
| Ω.A.L0.SCR.H.052P02 | bottom_peak_table | panel | P02 | PURE contrast 1.35 |
| Ω.A.L0.SCR.H.052O01 | bottom_peak_table | panel | O01 | FS tesseract |
| Ω.A.L0.SCR.H.052O02 | bottom_peak_table | panel | O02 | PROC to_string |
| Ω.A.L0.SCR.H.052O03 | bottom_peak_table | panel | O03 | PROC to_data |
| Ω.A.L0.SCR.H.052O04a | bottom_peak_table | panel | O04a | PURE strip |
| Ω.A.L0.SCR.H.052O04b | bottom_peak_table | panel | O04b | CMP empty skip |
| Ω.A.L0.SCR.H.052O04c | bottom_peak_table | panel | O04c | CMP conf<0 |
| Ω.A.L0.SCR.H.052O04d | bottom_peak_table | panel | O04d | CMP conf<25 |
| Ω.A.L0.SCR.H.052O04e | bottom_peak_table | panel | O04e | PURE token |
| Ω.A.L0.SCR.H.053G01 | bottom_peak_table | fine | G01 | FS.load config |
| Ω.A.L0.SCR.H.053G02 | bottom_peak_table | fine | G02 | PURE parent chain |
| Ω.A.L0.SCR.H.053G03 | bottom_peak_table | fine | G03 | PURE abs box |
| Ω.A.L0.SCR.H.053G04 | bottom_peak_table | fine | G04 | CMP min size |
| Ω.A.L0.SCR.H.053C01 | bottom_peak_table | fine | C01 | PROC mss.grab |
| Ω.A.L0.SCR.H.053C02 | bottom_peak_table | fine | C02 | PURE ImageGrab fallback |
| Ω.A.L0.SCR.H.053C03 | bottom_peak_table | fine | C03 | PURE rgb |
| Ω.A.L0.SCR.H.053Z01 | bottom_peak_table | fine | Z01 | CMP scale<=1 skip |
| Ω.A.L0.SCR.H.053Z02 | bottom_peak_table | fine | Z02 | PURE nw nh |
| Ω.A.L0.SCR.H.053Z03 | bottom_peak_table | fine | Z03 | PURE LANCZOS resize |
| Ω.A.L0.SCR.H.053P01 | bottom_peak_table | fine | P01 | PURE grayscale |
| Ω.A.L0.SCR.H.053P02 | bottom_peak_table | fine | P02 | PURE contrast 1.35 |
| Ω.A.L0.SCR.H.053O01 | bottom_peak_table | fine | O01 | FS tesseract |
| Ω.A.L0.SCR.H.053O02 | bottom_peak_table | fine | O02 | PROC to_string |
| Ω.A.L0.SCR.H.053O03 | bottom_peak_table | fine | O03 | PROC to_data |
| Ω.A.L0.SCR.H.053O04a | bottom_peak_table | fine | O04a | PURE strip |
| Ω.A.L0.SCR.H.053O04b | bottom_peak_table | fine | O04b | CMP empty skip |
| Ω.A.L0.SCR.H.053O04c | bottom_peak_table | fine | O04c | CMP conf<0 |
| Ω.A.L0.SCR.H.053O04d | bottom_peak_table | fine | O04d | CMP conf<25 |
| Ω.A.L0.SCR.H.053O04e | bottom_peak_table | fine | O04e | PURE token |
| Ω.A.L0.SCR.H.061G01 | bottom_peak_table_fine | full | G01 | FS.load config |
| Ω.A.L0.SCR.H.061G02 | bottom_peak_table_fine | full | G02 | PURE parent chain |
| Ω.A.L0.SCR.H.061G03 | bottom_peak_table_fine | full | G03 | PURE abs box |
| Ω.A.L0.SCR.H.061G04 | bottom_peak_table_fine | full | G04 | CMP min size |
| Ω.A.L0.SCR.H.061C01 | bottom_peak_table_fine | full | C01 | PROC mss.grab |
| Ω.A.L0.SCR.H.061C02 | bottom_peak_table_fine | full | C02 | PURE ImageGrab fallback |
| Ω.A.L0.SCR.H.061C03 | bottom_peak_table_fine | full | C03 | PURE rgb |
| Ω.A.L0.SCR.H.061Z01 | bottom_peak_table_fine | full | Z01 | CMP scale<=1 skip |
| Ω.A.L0.SCR.H.061Z02 | bottom_peak_table_fine | full | Z02 | PURE nw nh |
| Ω.A.L0.SCR.H.061Z03 | bottom_peak_table_fine | full | Z03 | PURE LANCZOS resize |
| Ω.A.L0.SCR.H.061P01 | bottom_peak_table_fine | full | P01 | PURE grayscale |
| Ω.A.L0.SCR.H.061P02 | bottom_peak_table_fine | full | P02 | PURE contrast 1.35 |
| Ω.A.L0.SCR.H.061O01 | bottom_peak_table_fine | full | O01 | FS tesseract |
| Ω.A.L0.SCR.H.061O02 | bottom_peak_table_fine | full | O02 | PROC to_string |
| Ω.A.L0.SCR.H.061O03 | bottom_peak_table_fine | full | O03 | PROC to_data |
| Ω.A.L0.SCR.H.061O04a | bottom_peak_table_fine | full | O04a | PURE strip |
| Ω.A.L0.SCR.H.061O04b | bottom_peak_table_fine | full | O04b | CMP empty skip |
| Ω.A.L0.SCR.H.061O04c | bottom_peak_table_fine | full | O04c | CMP conf<0 |
| Ω.A.L0.SCR.H.061O04d | bottom_peak_table_fine | full | O04d | CMP conf<25 |
| Ω.A.L0.SCR.H.061O04e | bottom_peak_table_fine | full | O04e | PURE token |
| Ω.A.L0.SCR.H.062G01 | bottom_peak_table_fine | panel | G01 | FS.load config |
| Ω.A.L0.SCR.H.062G02 | bottom_peak_table_fine | panel | G02 | PURE parent chain |
| Ω.A.L0.SCR.H.062G03 | bottom_peak_table_fine | panel | G03 | PURE abs box |
| Ω.A.L0.SCR.H.062G04 | bottom_peak_table_fine | panel | G04 | CMP min size |
| Ω.A.L0.SCR.H.062C01 | bottom_peak_table_fine | panel | C01 | PROC mss.grab |
| Ω.A.L0.SCR.H.062C02 | bottom_peak_table_fine | panel | C02 | PURE ImageGrab fallback |
| Ω.A.L0.SCR.H.062C03 | bottom_peak_table_fine | panel | C03 | PURE rgb |
| Ω.A.L0.SCR.H.062Z01 | bottom_peak_table_fine | panel | Z01 | CMP scale<=1 skip |
| Ω.A.L0.SCR.H.062Z02 | bottom_peak_table_fine | panel | Z02 | PURE nw nh |
| Ω.A.L0.SCR.H.062Z03 | bottom_peak_table_fine | panel | Z03 | PURE LANCZOS resize |
| Ω.A.L0.SCR.H.062P01 | bottom_peak_table_fine | panel | P01 | PURE grayscale |
| Ω.A.L0.SCR.H.062P02 | bottom_peak_table_fine | panel | P02 | PURE contrast 1.35 |
| Ω.A.L0.SCR.H.062O01 | bottom_peak_table_fine | panel | O01 | FS tesseract |
| Ω.A.L0.SCR.H.062O02 | bottom_peak_table_fine | panel | O02 | PROC to_string |
| Ω.A.L0.SCR.H.062O03 | bottom_peak_table_fine | panel | O03 | PROC to_data |
| Ω.A.L0.SCR.H.062O04a | bottom_peak_table_fine | panel | O04a | PURE strip |
| Ω.A.L0.SCR.H.062O04b | bottom_peak_table_fine | panel | O04b | CMP empty skip |
| Ω.A.L0.SCR.H.062O04c | bottom_peak_table_fine | panel | O04c | CMP conf<0 |
| Ω.A.L0.SCR.H.062O04d | bottom_peak_table_fine | panel | O04d | CMP conf<25 |
| Ω.A.L0.SCR.H.062O04e | bottom_peak_table_fine | panel | O04e | PURE token |
| Ω.A.L0.SCR.H.063G01 | bottom_peak_table_fine | fine | G01 | FS.load config |
| Ω.A.L0.SCR.H.063G02 | bottom_peak_table_fine | fine | G02 | PURE parent chain |
| Ω.A.L0.SCR.H.063G03 | bottom_peak_table_fine | fine | G03 | PURE abs box |
| Ω.A.L0.SCR.H.063G04 | bottom_peak_table_fine | fine | G04 | CMP min size |
| Ω.A.L0.SCR.H.063C01 | bottom_peak_table_fine | fine | C01 | PROC mss.grab |
| Ω.A.L0.SCR.H.063C02 | bottom_peak_table_fine | fine | C02 | PURE ImageGrab fallback |
| Ω.A.L0.SCR.H.063C03 | bottom_peak_table_fine | fine | C03 | PURE rgb |
| Ω.A.L0.SCR.H.063Z01 | bottom_peak_table_fine | fine | Z01 | CMP scale<=1 skip |
| Ω.A.L0.SCR.H.063Z02 | bottom_peak_table_fine | fine | Z02 | PURE nw nh |
| Ω.A.L0.SCR.H.063Z03 | bottom_peak_table_fine | fine | Z03 | PURE LANCZOS resize |
| Ω.A.L0.SCR.H.063P01 | bottom_peak_table_fine | fine | P01 | PURE grayscale |
| Ω.A.L0.SCR.H.063P02 | bottom_peak_table_fine | fine | P02 | PURE contrast 1.35 |
| Ω.A.L0.SCR.H.063O01 | bottom_peak_table_fine | fine | O01 | FS tesseract |
| Ω.A.L0.SCR.H.063O02 | bottom_peak_table_fine | fine | O02 | PROC to_string |
| Ω.A.L0.SCR.H.063O03 | bottom_peak_table_fine | fine | O03 | PROC to_data |
| Ω.A.L0.SCR.H.063O04a | bottom_peak_table_fine | fine | O04a | PURE strip |
| Ω.A.L0.SCR.H.063O04b | bottom_peak_table_fine | fine | O04b | CMP empty skip |
| Ω.A.L0.SCR.H.063O04c | bottom_peak_table_fine | fine | O04c | CMP conf<0 |
| Ω.A.L0.SCR.H.063O04d | bottom_peak_table_fine | fine | O04d | CMP conf<25 |
| Ω.A.L0.SCR.H.063O04e | bottom_peak_table_fine | fine | O04e | PURE token |
| Ω.A.L0.SCR.H.071G01 | chromatogram_center | full | G01 | FS.load config |
| Ω.A.L0.SCR.H.071G02 | chromatogram_center | full | G02 | PURE parent chain |
| Ω.A.L0.SCR.H.071G03 | chromatogram_center | full | G03 | PURE abs box |
| Ω.A.L0.SCR.H.071G04 | chromatogram_center | full | G04 | CMP min size |
| Ω.A.L0.SCR.H.071C01 | chromatogram_center | full | C01 | PROC mss.grab |
| Ω.A.L0.SCR.H.071C02 | chromatogram_center | full | C02 | PURE ImageGrab fallback |
| Ω.A.L0.SCR.H.071C03 | chromatogram_center | full | C03 | PURE rgb |
| Ω.A.L0.SCR.H.071Z01 | chromatogram_center | full | Z01 | CMP scale<=1 skip |
| Ω.A.L0.SCR.H.071Z02 | chromatogram_center | full | Z02 | PURE nw nh |
| Ω.A.L0.SCR.H.071Z03 | chromatogram_center | full | Z03 | PURE LANCZOS resize |
| Ω.A.L0.SCR.H.071P01 | chromatogram_center | full | P01 | PURE grayscale |
| Ω.A.L0.SCR.H.071P02 | chromatogram_center | full | P02 | PURE contrast 1.35 |
| Ω.A.L0.SCR.H.071O01 | chromatogram_center | full | O01 | FS tesseract |
| Ω.A.L0.SCR.H.071O02 | chromatogram_center | full | O02 | PROC to_string |
| Ω.A.L0.SCR.H.071O03 | chromatogram_center | full | O03 | PROC to_data |
| Ω.A.L0.SCR.H.071O04a | chromatogram_center | full | O04a | PURE strip |
| Ω.A.L0.SCR.H.071O04b | chromatogram_center | full | O04b | CMP empty skip |
| Ω.A.L0.SCR.H.071O04c | chromatogram_center | full | O04c | CMP conf<0 |
| Ω.A.L0.SCR.H.071O04d | chromatogram_center | full | O04d | CMP conf<25 |
| Ω.A.L0.SCR.H.071O04e | chromatogram_center | full | O04e | PURE token |
| Ω.A.L0.SCR.H.072G01 | chromatogram_center | panel | G01 | FS.load config |
| Ω.A.L0.SCR.H.072G02 | chromatogram_center | panel | G02 | PURE parent chain |
| Ω.A.L0.SCR.H.072G03 | chromatogram_center | panel | G03 | PURE abs box |
| Ω.A.L0.SCR.H.072G04 | chromatogram_center | panel | G04 | CMP min size |
| Ω.A.L0.SCR.H.072C01 | chromatogram_center | panel | C01 | PROC mss.grab |
| Ω.A.L0.SCR.H.072C02 | chromatogram_center | panel | C02 | PURE ImageGrab fallback |
| Ω.A.L0.SCR.H.072C03 | chromatogram_center | panel | C03 | PURE rgb |
| Ω.A.L0.SCR.H.072Z01 | chromatogram_center | panel | Z01 | CMP scale<=1 skip |
| Ω.A.L0.SCR.H.072Z02 | chromatogram_center | panel | Z02 | PURE nw nh |
| Ω.A.L0.SCR.H.072Z03 | chromatogram_center | panel | Z03 | PURE LANCZOS resize |
| Ω.A.L0.SCR.H.072P01 | chromatogram_center | panel | P01 | PURE grayscale |
| Ω.A.L0.SCR.H.072P02 | chromatogram_center | panel | P02 | PURE contrast 1.35 |
| Ω.A.L0.SCR.H.072O01 | chromatogram_center | panel | O01 | FS tesseract |
| Ω.A.L0.SCR.H.072O02 | chromatogram_center | panel | O02 | PROC to_string |
| Ω.A.L0.SCR.H.072O03 | chromatogram_center | panel | O03 | PROC to_data |
| Ω.A.L0.SCR.H.072O04a | chromatogram_center | panel | O04a | PURE strip |
| Ω.A.L0.SCR.H.072O04b | chromatogram_center | panel | O04b | CMP empty skip |
| Ω.A.L0.SCR.H.072O04c | chromatogram_center | panel | O04c | CMP conf<0 |
| Ω.A.L0.SCR.H.072O04d | chromatogram_center | panel | O04d | CMP conf<25 |
| Ω.A.L0.SCR.H.072O04e | chromatogram_center | panel | O04e | PURE token |
| Ω.A.L0.SCR.H.073G01 | chromatogram_center | fine | G01 | FS.load config |
| Ω.A.L0.SCR.H.073G02 | chromatogram_center | fine | G02 | PURE parent chain |
| Ω.A.L0.SCR.H.073G03 | chromatogram_center | fine | G03 | PURE abs box |
| Ω.A.L0.SCR.H.073G04 | chromatogram_center | fine | G04 | CMP min size |
| Ω.A.L0.SCR.H.073C01 | chromatogram_center | fine | C01 | PROC mss.grab |
| Ω.A.L0.SCR.H.073C02 | chromatogram_center | fine | C02 | PURE ImageGrab fallback |
| Ω.A.L0.SCR.H.073C03 | chromatogram_center | fine | C03 | PURE rgb |
| Ω.A.L0.SCR.H.073Z01 | chromatogram_center | fine | Z01 | CMP scale<=1 skip |
| Ω.A.L0.SCR.H.073Z02 | chromatogram_center | fine | Z02 | PURE nw nh |
| Ω.A.L0.SCR.H.073Z03 | chromatogram_center | fine | Z03 | PURE LANCZOS resize |
| Ω.A.L0.SCR.H.073P01 | chromatogram_center | fine | P01 | PURE grayscale |
| Ω.A.L0.SCR.H.073P02 | chromatogram_center | fine | P02 | PURE contrast 1.35 |
| Ω.A.L0.SCR.H.073O01 | chromatogram_center | fine | O01 | FS tesseract |
| Ω.A.L0.SCR.H.073O02 | chromatogram_center | fine | O02 | PROC to_string |
| Ω.A.L0.SCR.H.073O03 | chromatogram_center | fine | O03 | PROC to_data |
| Ω.A.L0.SCR.H.073O04a | chromatogram_center | fine | O04a | PURE strip |
| Ω.A.L0.SCR.H.073O04b | chromatogram_center | fine | O04b | CMP empty skip |
| Ω.A.L0.SCR.H.073O04c | chromatogram_center | fine | O04c | CMP conf<0 |
| Ω.A.L0.SCR.H.073O04d | chromatogram_center | fine | O04d | CMP conf<25 |
| Ω.A.L0.SCR.H.073O04e | chromatogram_center | fine | O04e | PURE token |

---

## §L0-TASK (read_tasks — verify leaf chain)

### TASK.verify_active_tab_analysis

| ID | leaf |
|----|------|
| Ω.A.L0.TASK.VTA.01 | SCR.H on bottom_tabs |
| Ω.A.L0.TASK.VTA.02.CMP | "분석목록" in plain_text |

### TASK.verify_peak_table_has_data

| ID | leaf |
|----|------|
| Ω.A.L0.TASK.VPD.01 | SCR.H on bottom_peak_table_fine |
| Ω.A.L0.TASK.VPD.02.RX | findall numeric tokens |
| Ω.A.L0.TASK.VPD.03.CMP | count>=expect_numeric_min(1) |
| Ω.A.L0.TASK.VPD.04.CMP | not mostly_zero if reject |

### TASK.verify_peak_table_cleared

| ID | leaf |
|----|------|
| Ω.A.L0.TASK.VPC.01 | SCR.H on bottom_peak_table_fine |
| Ω.A.L0.TASK.VPC.02.RX | zero-like tokens |
| Ω.A.L0.TASK.VPC.03.CMP | zero_ratio>=0.85 |

---

## §L0-FOCUS (Ω.A.L0.FOC.*)

| ID | leaf |
|----|------|
| Ω.A.L0.FOC.01.W32.create | hollow red rect 2px |
| Ω.A.L0.FOC.02.PURE.clamp_ms | GC_SCREEN_FOCUS_MS 150-400 |
| Ω.A.L0.FOC.03.WAIT.min | sleep clamp_ms |
| Ω.A.L0.FOC.04.W32.destroy_prev | remove prior overlay |
| Ω.A.L0.FOC.05.STW.stage | record stage name |

---

## §L0-T11 leaf count

| block | leaves |
|-------|--------|
| WIFI | 11 |
| WIN | 10 |
| LV+PICK | 15 |
| TR | 5 |
| TAB | 4 |
| DN | 14 |
| MTD | 4 |
| PDF | 5 |
| SCR-H | 420 |
| TASK | 9 |
| FOCUS | 5 |
| **합** | **502** |


---

*PART1 L0 — T11 complete*
