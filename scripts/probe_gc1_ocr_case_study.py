# -*- coding: utf-8 -*-
"""probe_gc1_ocr_case_study.py — Autochro 단계별 OCR 케이스 스터디 (조작 없음·읽기 전용)

각 prep/export 단계에 대응하는 영역·read_tasks·앵커(.raw, 트리명, 메뉴)를
OCR로 스캔하고 JSON 리포트를 남깁니다. 파이프라인을 막지 않으며 실수·미인식도 기록.

  python scripts/probe_gc1_ocr_case_study.py
  python scripts/probe_gc1_ocr_case_study.py --pretty
  python scripts/probe_gc1_ocr_case_study.py --with-menu   # 우클릭 후 메뉴 OCR (UI 변경)
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

_REPO = Path(__file__).resolve().parents[1]
if str(_REPO) not in sys.path:
    sys.path.insert(0, str(_REPO))

from gc_screen_read import (  # noqa: E402
    DEFAULT_CONFIG,
    find_autochro_window_box,
    load_config,
    read_region_hierarchical,
    read_track_zoom_on_box,
    resolve_region_box,
)
from gc1_runtime.layer3_eye import verify_read_task  # noqa: E402
from gc1_runtime.layer3_eye_guide import (  # noqa: E402
    AutochroStepEye,
    token_looks_like_raw,
)


def _out_dir() -> Path:
    d = Path(os.environ.get("USERPROFILE", ".")) / ".cursor" / "gc-ocr-case-study"
    d.mkdir(parents=True, exist_ok=True)
    return d


def _stage_summary(tracked) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    for st in tracked.stages:
        rows.append(
            {
                "stage": st.stage,
                "step": round(st.adaptive_step, 3),
                "crop": round(st.crop_frac, 3),
                "early": st.stopped_early,
                "tokens": len(st.tokens),
                "top_tokens": [
                    {"text": t.text, "conf": round(t.confidence, 1)}
                    for t in sorted(st.tokens, key=lambda x: -x.confidence)[:8]
                ],
            }
        )
    return rows


def _probe_region(
    config: dict,
    window_box,
    region_id: str,
    *,
    needles: Optional[List[str]] = None,
) -> Dict[str, Any]:
    row: Dict[str, Any] = {"region": region_id, "ok": False}
    try:
        rb, chain = resolve_region_box(config, region_id, window_box)
        row["box"] = [rb.left, rb.top, rb.width, rb.height]
        row["chain"] = chain
        tracked = read_track_zoom_on_box(
            rb,
            config,
            region_id=region_id,
            save_images=True,
            needles=needles,
        )
        row["stages"] = _stage_summary(tracked)
        if tracked.stages:
            last = tracked.stages[-1]
            row["text_preview"] = (last.plain_text or "")[:240]
            row["token_count"] = len(last.tokens)
        read = read_region_hierarchical(
            config, region_id, window_box=window_box, save_images=False
        )
        row["final_preview"] = (read.final_text or "")[:240]
        row["ok"] = bool((read.final_text or "").strip())
    except Exception as exc:
        row["error"] = str(exc)
    return row


def _probe_tasks(config: dict, eye: AutochroStepEye, task_ids: List[str]) -> List[Dict[str, Any]]:
    out: List[Dict[str, Any]] = []
    tasks = config.get("read_tasks") or {}
    for tid in task_ids:
        entry: Dict[str, Any] = {"task": tid}
        if tid not in tasks:
            entry["skip"] = "unknown"
            out.append(entry)
            continue
        region_id = str(tasks[tid].get("region") or "")
        entry["region"] = region_id
        try:
            text = eye.ocr_region(region_id, label=f"case:{tid}")
            verdict = verify_read_task(config, tid, text)
            entry["passed"] = verdict.passed
            entry["detail"] = verdict.detail
            entry["preview"] = text[:120]
        except Exception as exc:
            entry["passed"] = False
            entry["error"] = str(exc)
        out.append(entry)
    return out


def _probe_anchors(eye: AutochroStepEye, data_name: str) -> Dict[str, Any]:
    raw_xy = eye.find_raw_anchor_screen_xy("top_sample_table")
    tree_xy = eye.find_tree_name_screen_xy(data_name) if data_name else None
    return {
        "raw_anchor": list(raw_xy) if raw_xy else None,
        "tree_anchor": list(tree_xy) if tree_xy else None,
        "data_name": data_name,
    }


def run_case_study(*, with_menu: bool = False) -> Dict[str, Any]:
    from gc_autochro import (
        _analysis_sample_table,
        _neutral_list_coords,
        connect_main_window,
        load_autochro_config,
        read_active_control_data_name,
        _select_analysis_tab,
        _select_control_tab,
    )

    os.environ.setdefault("GC_SCREEN_SHOW_FOCUS", "0")
    cfg = load_autochro_config(str(_REPO))
    conf = load_config(DEFAULT_CONFIG)
    report: Dict[str, Any] = {
        "ts": datetime.now(timezone.utc).isoformat(),
        "adaptive": os.getenv("GC1_AUTOCHRO_EYE_ADAPT", "1"),
        "strict": os.getenv("GC1_AUTOCHRO_EYE_STRICT", "0"),
        "steps": [],
    }

    wb = find_autochro_window_box(conf.get("window_title_contains", "Autochro"))
    if not wb:
        report["error"] = "Autochro 창 없음"
        return report

    _, win = connect_main_window(cfg)
    data_name = ""
    try:
        data_name = read_active_control_data_name(win, cfg)
    except Exception as exc:
        report["data_name_error"] = str(exc)

    eye = AutochroStepEye.from_window_rect(win.rectangle())

    # --- P1 제어목록 ---
    _select_control_tab(win)
    time.sleep(0.5)
    report["steps"].append(
        {
            "id": "P1.control_tab",
            "description": "제어목록 탭·시료 표",
            "regions": [
                _probe_region(conf, wb, "bottom_tabs", needles=["제어목록"]),
                _probe_region(conf, wb, "control_sample_table", needles=["raw"]),
                _probe_region(conf, wb, "top_sample_table", needles=["raw", "시료"]),
            ],
            "tasks": _probe_tasks(
                conf,
                eye,
                ["eye_active_tab_control", "eye_before_control_sync", "eye_before_sync_dclick"],
            ),
            "anchors": _probe_anchors(eye, data_name),
        }
    )

    # --- P2 분석목록 ---
    _select_analysis_tab(win)
    time.sleep(0.5)
    report["steps"].append(
        {
            "id": "P2.analysis_tab",
            "description": "분석목록 탭·트리·피크 표",
            "regions": [
                _probe_region(conf, wb, "bottom_tabs", needles=["분석목록"]),
                _probe_region(conf, wb, "left_analysis_tree", needles=["dre", "2026"]),
                _probe_region(conf, wb, "top_sample_table", needles=["raw", "시료"]),
                _probe_region(conf, wb, "bottom_peak_table_fine", needles=["H2", "RT", "0"]),
            ],
            "tasks": _probe_tasks(
                conf,
                eye,
                [
                    "eye_active_tab_analysis",
                    "eye_before_sample_table",
                    "eye_after_mtd_peak",
                    "eye_after_context_init",
                ],
            ),
            "anchors": _probe_anchors(eye, data_name),
        }
    )

    if with_menu:
        sample_list = _analysis_sample_table(win)
        rel_x, rel_y = _neutral_list_coords(sample_list)
        sample_list.set_focus()
        sample_list.click_input(button="right", coords=(rel_x, rel_y))
        time.sleep(0.5)
        report["steps"].append(
            {
                "id": "P3.context_menu",
                "description": "우클릭 컨텍스트 메뉴 (시료 표)",
                "regions": [
                    _probe_region(
                        conf, wb, "context_menu_popup", needles=["초기화", "불러", "정량"]
                    ),
                ],
                "note": "메뉴 열린 상태 — ESC 로 닫을 수 있음",
            }
        )

    report["data_name"] = data_name
    report["capture_dir"] = str(
        Path(os.environ.get("USERPROFILE", ".")) / ".cursor" / "gc-screen-capture"
    )
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description="GC1 Autochro OCR case study")
    parser.add_argument("--pretty", action="store_true")
    parser.add_argument(
        "--with-menu",
        action="store_true",
        help="시료 표 우클릭 후 메뉴 영역 OCR (UI 변경)",
    )
    parser.add_argument("--out", default="", help="JSON 출력 경로 (기본: .cursor/gc-ocr-case-study/)")
    args = parser.parse_args()

    report = run_case_study(with_menu=args.with_menu)
    out_path = Path(args.out) if args.out else _out_dir() / f"case_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    out_path.write_text(
        json.dumps(report, ensure_ascii=False, indent=2 if args.pretty else None),
        encoding="utf-8",
    )
    print(f"[case-study] wrote {out_path}")
    if args.pretty:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        for step in report.get("steps", []):
            sid = step.get("id", "?")
            tasks = step.get("tasks") or []
            passed = sum(1 for t in tasks if t.get("passed"))
            print(f"  {sid}: tasks {passed}/{len(tasks)}")
            anchors = step.get("anchors") or {}
            print(f"    raw={anchors.get('raw_anchor')} tree={anchors.get('tree_anchor')}")
    if report.get("error"):
        print(f"[case-study] ERROR: {report['error']}")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
