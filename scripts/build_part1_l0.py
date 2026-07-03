# -*- coding: utf-8 -*-
"""Build deploy/GC1_RUNTIME_DESIGN_PART1_L0.md (T11 deliverable)."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SNIP = ROOT / "deploy" / "_scr_h_table_snippet.md"
OUT = ROOT / "deploy" / "GC1_RUNTIME_DESIGN_PART1_L0.md"

HEADER = """# GC1 Runtime 설계 — PART 1: Ω-L0 프로브 (전 leaf)

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
| Ω.A.L0.WIFI.04c.RX.ssid | SSID: value after colon | ssid\\|null |
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
| Ω.A.L0.DN-T.05a.RX | ^\\\\d{6} |
| Ω.A.L0.DN-T.05b.RX | ^\\\\d{8} |
| Ω.A.L0.DN-R.01.W32.texts | tree lines |
| Ω.A.L0.DN-R.02.CMP.marker | YL6500 GC |
| Ω.A.L0.DN-R.03.PURE.prevline | idx-1 |
| Ω.A.L0.DN-R.04.W32.selected | get_selected fallback |
| Ω.A.L0.DN.99.CMP.ok | non-empty else E_DATA_NAME |

---

## §L0-MTD (Ω.A.L0.MTD.01–03)

| ID | leaf |
|----|------|
| Ω.A.L0.MTD.01.RX.date6 | ^(\\\\d{6}) |
| Ω.A.L0.MTD.01b.RX.date8 | ^(\\\\d{8}) |
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

"""

TASK = """
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
"""

FOOTER = """

---

*PART1 L0 — T11 complete*
"""

def main() -> None:
    snip = SNIP.read_text(encoding="utf-8") if SNIP.is_file() else ""
    OUT.write_text(HEADER + snip + TASK + FOOTER, encoding="utf-8")
    print(f"wrote {OUT}")


if __name__ == "__main__":
    main()
