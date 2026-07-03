# -*- coding: utf-8 -*-
"""Generate PART2_L4_P5_P9.md + job JSON example — T14."""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "deploy" / "GC1_RUNTIME_DESIGN_PART2_L4_P5_P9.md"
JSON_OUT = ROOT / "deploy" / "gc_autochro_job.example.json"

ATOMS: list[tuple[str, str, str, str, str, str, str, int]] = [
    # P5 maps P2
    ("Ω.A.L4.P5.01", "분석목록 탭 (2차)", "H", "Ω.A.L4.P4.08 ok", "maps Ω.A.L4.P2.01", "Ω.A.L0.TAB.03", "{code:null,max_attempt:1}", 10000),
    ("Ω.A.L4.P5.02", "시료표 LV (2차)", "H", "Ω.A.L0.TAB.03", "maps Ω.A.L4.P2.02", "CMP sample_list", "{code:null,max_attempt:1}", 10000),
    ("Ω.A.L4.P5.03", "focus click (2차)", "H", "Ω.A.L4.P5.02 ok", "maps Ω.A.L4.P2.03", "CMP focus", "{code:E_P2_FOCUS,max_attempt:3,retry_delay_ms:500}", 15000),
    ("Ω.A.L4.P5.04", "Ctrl+A (2차)", "H", "Ω.A.L4.P5.03 ok", "maps Ω.A.L4.P2.04", "CMP keys", "{code:E_P2_SELECT,max_attempt:2,retry_delay_ms:300}", 5000),
    ("Ω.A.L4.P5.05", "WAIT (2차)", "W", "Ω.A.L4.P5.04 ok", "maps Ω.A.L4.P2.05", "CMP elapsed", "{code:null,max_attempt:1}", 1000),
    # P6 maps P3
    ("Ω.A.L4.P6.01", "분석목록 (2차)", "H", "Ω.A.L4.P5.05 ok", "maps Ω.A.L4.P3.01", "Ω.A.L0.TAB.03", "{code:null,max_attempt:1}", 10000),
    ("Ω.A.L4.P6.02", "시료표 (2차)", "H", "Ω.A.L0.TAB.03", "maps Ω.A.L4.P3.02", "CMP sample_list", "{code:null,max_attempt:1}", 10000),
    ("Ω.A.L4.P6.03", "우클릭 (2차)", "H", "Ω.A.L4.P6.02 ok", "maps Ω.A.L4.P3.03", "CMP rclick", "{code:null,max_attempt:1}", 10000),
    ("Ω.A.L4.P6.04", "초기화 메뉴 (2차)", "H", "Ω.A.L4.P6.03 ok", "maps Ω.A.L4.P3.04", "CMP menu", "{code:E_P3_MENU,max_attempt:3,retry_delay_ms:120}", 20000),
    ("Ω.A.L4.P6.05", "WAIT (2차)", "W", "Ω.A.L4.P6.04 ok", "maps Ω.A.L4.P3.05", "CMP elapsed", "{code:null,max_attempt:1}", 2000),
    ("Ω.A.L4.P6.06", "cleared verify (2차)", "E", "Ω.A.L4.P6.05 ok", "maps Ω.A.L4.P3.06", "TASK cleared", "{code:E_VERIFY_PEAK,max_attempt:1}", 30000),
    # P7
    ("Ω.A.L4.P7.01", "P2 subtree", "H", "Ω.A.L4.P6.06 ok", "P7.01 P2.01..P2.05", "Ω.A.L4.P2.05 ok", "{code:null,max_attempt:1}", 30000),
    ("Ω.A.L4.P7.02", "초기화+정량 메뉴", "H", "Ω.A.L4.P7.01 ok", "P7.02.1..P7.02.7", "CMP menu selected", "{code:E_P7_MENU,max_attempt:2,retry_delay_ms:500}", 20000),
    ("Ω.A.L4.P7.03", "정량 시작 대기", "W", "Ω.A.L4.P7.02 ok", "P7.03 WAIT 3000", "CMP elapsed>=3000", "{code:null,max_attempt:1}", 4000),
    ("Ω.A.L4.P7.04", "progress poll", "PROC|W", "Ω.A.L4.P7.03 ok", "P7.04.1..P7.04.5 loop", "CMP progress done", "{code:null,max_attempt:1}", 120000),
    ("Ω.A.L4.P7.05", "피크 데이터 검증", "E", "Ω.A.L4.P7.04 ok", "TASK verify_peak_table_has_data", "TASK pass", "{code:E_VERIFY_PEAK,max_attempt:1}", 30000),
    # P8
    ("Ω.A.L4.P8.01", "P2 subtree", "H", "Ω.A.L4.P7.05 ok", "P8.01 P2.01..P2.05", "Ω.A.L4.P2.05 ok", "{code:null,max_attempt:1}", 30000),
    ("Ω.A.L4.P8.02", "창 focus", "H", "Ω.A.L4.P8.01 ok", "P8.02 set_focus", "CMP fg hwnd", "{code:null,max_attempt:1}", 5000),
    ("Ω.A.L4.P8.03", "Ctrl+P", "H", "Ω.A.L4.P8.02 ok", "P8.03 ^p", "CMP keys", "{code:null,max_attempt:1}", 5000),
    ("Ω.A.L4.P8.04", "인쇄 대화 대기", "W", "Ω.A.L4.P8.03 ok", "P8.04 WAIT 1000", "CMP elapsed", "{code:null,max_attempt:1}", 2000),
    ("Ω.A.L4.P8.05", "인쇄 확인", "H", "Ω.A.L4.P8.04 ok", "P8.05.1..P8.05.5", "CMP dlg handled", "{code:E_P8_PRINT,max_attempt:2,retry_delay_ms:500}", 30000),
    ("Ω.A.L4.P8.06", "저장 대화 poll", "W", "Ω.A.L4.P8.05 ok", "P8.06 poll 500ms", "CMP save dlg or timeout", "{code:null,max_attempt:1}", 60000),
    # P9
    ("Ω.A.L4.P9.01", "output dir", "FS", "Ω.A.L4.P8.06 ok", "P9.01 makedirs", "FS.isdir parent", "{code:null,max_attempt:1}", 5000),
    ("Ω.A.L4.P9.02", "저장 대화 찾기", "PROC", "Ω.A.L4.P9.01 ok", "P9.02 find dlg", "CMP dlg non-null", "{code:E_P9_DLG,max_attempt:3,retry_delay_ms:2000}", 120000),
    ("Ω.A.L4.P9.03", "대화 focus", "H", "Ω.A.L4.P9.02 ok", "P9.03 set_focus", "CMP fg dlg", "{code:null,max_attempt:1}", 5000),
    ("Ω.A.L4.P9.04", "stem pure", "PURE", "data_name STW", "P9.04 PURE stem", "CMP stem", "{code:null,max_attempt:1}", 1000),
    ("Ω.A.L4.P9.05", "Edit 찾기", "H", "Ω.A.L4.P9.03 ok", "P9.05.1..P9.05.4", "CMP edit found", "{code:null,max_attempt:1}", 15000),
    ("Ω.A.L4.P9.06", "경로 입력", "H", "Ω.A.L4.P9.05 ok", "P9.06 set_edit_text", "CMP text set", "{code:null,max_attempt:1}", 10000),
    ("Ω.A.L4.P9.07", "입력 대기", "W", "Ω.A.L4.P9.06 ok", "P9.07 WAIT 500", "CMP elapsed", "{code:null,max_attempt:1}", 1000),
    ("Ω.A.L4.P9.08", "저장 버튼", "H", "Ω.A.L4.P9.07 ok", "P9.08 btn loop+%s", "CMP click", "{code:E_P9_SAVE_BTN,max_attempt:2,retry_delay_ms:300}", 15000),
    ("Ω.A.L4.P9.09", "덮어쓰기", "H", "Ω.A.L4.P9.08 ok", "P9.09 Yes loop", "CMP overwrite ok", "{code:null,max_attempt:1}", 15000),
    ("Ω.A.L4.P9.10", "hancom loop", "H|W", "Ω.A.L4.P9.09 ok", "P9.H.01..08 × iter", "CMP hancom idle", "{code:null,max_attempt:1}", 180000),
    ("Ω.A.L4.P9.11", "PDF ready", "FS|W", "Ω.A.L4.P9.10 ok", "PAR.00 poll", "Ω.A.L0.PDF.01..05", "{code:E_P9_READY,max_attempt:1}", 120000),
    ("Ω.A.L4.P9.12", "PDF fallback glob", "FS", "Ω.A.L4.P9.11 fail soft", "P9.12 glob mtime", "CMP recent pdf", "{code:null,max_attempt:1}", 10000),
    ("Ω.A.L4.P9.13", "cleanup CL", "FS", "pdf path known", "CL.01..CL.08", "CL.08 kept_path", "{code:E_CLEAN_WRONG,max_attempt:1}", 30000),
    ("Ω.A.L4.P9.14", "export record", "STW", "Ω.A.L4.P9.11 or P9.12 ok", "P9.14 STW atoms+paths", "CMP record_export", "{code:null,max_attempt:1}", 5000),
]

JOB_EXAMPLE = {
    "job_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
    "started_at": "2026-06-30T10:00:00+09:00",
    "data_name": "20260630_DRE-01",
    "pdf_path_planned": "C:\\Users\\User\\Desktop\\박은규\\20260630_DRE-01.pdf",
    "prep_enabled": True,
    "phase_current": "P4",
    "atom_current": "Ω.A.L4.P4.03",
    "resume_from": None,
    "force": False,
    "hancom_windows_seen": 1,
    "atoms": {
        "Ω.A.L4.P0.01": {
            "status": "ok",
            "attempt": 1,
            "channel_used": "H",
            "fail_code": None,
            "probe_snapshot": {"hancom_closed": 1},
            "started_at": "2026-06-30T10:00:01+09:00",
            "ended_at": "2026-06-30T10:00:05+09:00",
        },
        "Ω.A.L4.P4.03": {
            "status": "running",
            "attempt": 2,
            "channel_used": "H",
            "fail_code": None,
            "probe_snapshot": {"tree_line": "20260630_DRE-01.1"},
            "started_at": "2026-06-30T10:02:10+09:00",
            "ended_at": None,
        },
        "Ω.A.L4.P9.14": {
            "status": "pending",
            "attempt": 0,
            "channel_used": None,
            "fail_code": None,
            "probe_snapshot": {},
            "started_at": None,
            "ended_at": None,
        },
    },
}


def main() -> None:
    lines = [
        "# GC1 Runtime 설계 — PART 2b: L4 P5~P9 + job JSON (T14)",
        "",
        "> 상위: [GC1_RUNTIME_DESIGN.md](GC1_RUNTIME_DESIGN.md)",
        "> P0~P4 registry: [PART2_L4_P0_P4](GC1_RUNTIME_DESIGN_PART2_L4_P0_P4.md)",
        "> L6 leaf: [PART3_L6](GC1_RUNTIME_DESIGN_PART3_L6.md)",
        "",
        "---",
        "",
        "## §L4-P5~P9 atom registry (36 atoms)",
        "",
        "| atom_id | channel | pre_probe[] | post_probe[] | on_fail | timeout_ms |",
        "|---------|---------|-------------|--------------|---------|------------|",
    ]
    for row in ATOMS:
        aid, _t, ch, pre, _a, post, fail, tmo = row
        lines.append(f"| {aid} | {ch} | {pre} | {post} | {fail} | {tmo} |")

    lines += ["", "---", ""]
    for row in ATOMS:
        aid, title, ch, pre, act, post, fail, tmo = row
        lines += [
            f"### {aid} — {title}",
            "",
            "| 필드 | 값 |",
            "|------|-----|",
            f"| id | {aid} |",
            f"| channel | {ch} |",
            f"| pre_probe | [{pre}] |",
            f"| action | [{act}] |",
            f"| post_probe | [{post}] |",
            f"| on_fail | {fail} |",
            f"| timeout_ms | {tmo} |",
            "",
        ]

    lines += [
        "## §L6 cross-ref (T14 — export 이후)",
        "",
        "| chain | PART3 section | leaf |",
        "|-------|---------------|------|",
        "| PDF wait | §PAR.00 | 11 |",
        "| parse+trim | §PAR.01–08 | 10+6×N+14+5 |",
        "| excel | §PAR.09–10 | 7 |",
        "| cleanup | §CL | 7×files |",
        "| mail | §ML | 14+3×retries |",
        "",
        "## §JOB-JSON — `.gc_autochro_job.json` 예시",
        "",
        "파일: [gc_autochro_job.example.json](gc_autochro_job.example.json)",
        "",
        "```json",
        json.dumps(JOB_EXAMPLE, ensure_ascii=False, indent=2),
        "```",
        "",
        "### §JOB-JSON 필드 leaf (§B-STATE)",
        "",
        "| JSON path | STW leaf |",
        "|-----------|----------|",
        "| job_id | Ω.A.B.STATE.job_id |",
        "| atoms.{id}.status | Ω.A.B.STATE.atoms.status |",
        "| atoms.{id}.attempt | Ω.A.B.STATE.atoms.attempt |",
        "| resume_from | Ω.A.B.STATE.resume_from |",
        "",
        "## §T14 leaf count",
        "",
        "| block | atoms |",
        "|-------|-------|",
        "| P5 | 5 |",
        "| P6 | 6 |",
        "| P7 | 5 |",
        "| P8 | 6 |",
        "| P9 | 14 |",
        "| **합** | **36** |",
        "",
        "*T14 complete*",
        "",
    ]
    OUT.write_text("\n".join(lines), encoding="utf-8")
    JSON_OUT.write_text(json.dumps(JOB_EXAMPLE, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"wrote {OUT} atoms={len(ATOMS)}")
    print(f"wrote {JSON_OUT}")


if __name__ == "__main__":
    main()
